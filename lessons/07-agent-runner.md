# 第七课：Agent Runner — 消息如何被处理

> **阶段二 · 核心架构** | [上一课 ←](./06-gateway-architecture.md) | [下一课 →](./08-react-loop.md) | [目录](../README.md)

---

## 本课目标

学完这节课，你能回答：

1. 一条用户消息从发送到收到回复，经历了哪些完整步骤？
2. Channel Adapter 如何将不同平台的消息统一为内部格式？
3. 消息如何路由到正确的 Agent 实例？
4. Lane-based Command Queue 的设计原理和解决的核心问题是什么？
5. `runAgentTurnWithFallback()` 的核心逻辑和三个重试防护标志分别是什么？
6. `AgentRunLoopResult` 的 "success" 和 "final" 两种状态有什么区别？

---

## 1. 一条消息的完整旅程

当你在 Discord 里输入"帮我查一下天气"然后按回车，背后发生了什么？

这是一条消息从"出生"到"死亡"的完整生命周期：

```
你的消息: "帮我查一下天气"
  │
  │ ① Channel（Discord）接收原始消息
  ▼
┌───────────────────────────────┐
│  Channel Adapter               │  ② 格式标准化
│  (Discord 原始 JSON            │     各平台消息 → 统一 InternalMessage
│    → 统一 InternalMessage)     │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  Gateway 控制面                │  ③ 认证 + Session 路由
│                               │     → 消息合法吗？（鉴权）
│  认证鉴权                      │     → 属于哪个 Session？
│  Session 路由                  │     → 绑定了哪个 Agent？
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  Lane Queue                    │  ④ 排队等待
│  (per-session FIFO 队列)       │     → 同一 Session 的消息严格串行
│                               │     → 防止并发处理导致状态混乱
└──────────────┬────────────────┘
               │  取出队首消息
               ▼
┌───────────────────────────────┐
│  Agent Runner                  │  ⑤ 核心执行
│  runAgentTurnWithFallback()    │     → 检查重试防护
│                               │     → 组装 System Prompt
│                               │     → 加载 Memory
│                               │     → 检查 Context Window
│                               │     → 调用 LLM
│                               │     → 执行工具（ReAct循环）
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  流式回复推送                   │  ⑥ 返回结果
│  (WebSocket Stream)            │     → LLM 生成的 token 逐个推送
│                               │     → 通过 Channel Adapter 回到 Discord
└───────────────────────────────┘

你看到: "今天北京晴，气温 25°C，体感舒适，适合出门！"
```

> **记忆口诀**：**Channel → Adapter → Gateway → Lane → Runner → LLM → 回复**，七步走完一条消息的一生。

### 延迟分布

一条消息各阶段的典型延迟：

```
Channel → Adapter:   ~5ms     (本地通信)
Adapter → Gateway:   ~2ms     (格式转换)
Gateway 路由+鉴权:   ~10ms    (内存查找)
Lane 排队等待:       0ms~30s  (取决于前面有没有消息在处理)
Agent Runner 执行:   2s~60s   (取决于 LLM 速度和工具调用次数)
流式推送回用户:      ~5ms     (WebSocket 直推)
─────────────────────
总延迟:              ~2s~90s  (LLM 调用是主要瓶颈)
```

---

## 2. Channel Adapter：消息格式标准化

### 问题：平台消息格式千差万别

不同平台的消息格式完全不同——字段名不同、结构不同、功能不同：

```json
// ─── Discord 原始消息 ───
{
  "content": "帮我查天气",
  "author": { "id": "123456789", "username": "alice", "discriminator": "1234" },
  "channel_id": "987654321",
  "guild_id": "111222333",
  "attachments": [],
  "timestamp": "2026-03-27T10:00:00.000Z"
}

// ─── Slack 原始消息 ───
{
  "type": "message",
  "text": "帮我查天气",
  "user": "U0123ABC",
  "channel": "C0456DEF",
  "ts": "1711526400.123456",
  "team": "T0789GHI"
}

// ─── Telegram 原始消息 ───
{
  "update_id": 123456789,
  "message": {
    "message_id": 42,
    "text": "帮我查天气",
    "from": { "id": 123, "first_name": "Alice", "is_bot": false },
    "chat": { "id": -456, "type": "private" },
    "date": 1711526400
  }
}
```

### 解决方案：统一的 InternalMessage

Channel Adapter 的职责就是把这些 **五花八门的格式统一成 OpenClaw 内部格式**：

```typescript
interface InternalMessage {
  sessionId: string;           // 会话 ID（由 channelType + channelId + userId 推导）
  userId: string;              // 统一用户标识
  channel: ChannelType;        // 来源渠道枚举: 'discord' | 'slack' | 'telegram' | 'web' | ...
  content: string;             // 消息文本（纯文本）
  attachments?: Attachment[];  // 附件（图片、文件等）
  metadata: {
    rawMessage: unknown;       // 保留原始消息（用于回复时需要平台特有功能）
    channelId: string;         // 原始渠道 ID
    guildId?: string;          // 服务器/工作区 ID（如 Discord guild）
  };
  timestamp: number;           // 统一时间戳（Unix ms）
}
```

### Adapter 的设计模式

```
                    ┌──────────────────────┐
                    │  ChannelAdapter       │ ← 抽象基类
                    │  (interface)          │
                    ├──────────────────────┤
                    │  + normalize(raw)     │ → 原始消息 → InternalMessage
                    │  + send(msg)          │ → InternalMessage → 原始格式发出
                    │  + connect()          │ → 连接到平台 API
                    │  + disconnect()       │ → 断开连接
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────┴──┐   ┌────────┴───┐   ┌────────┴────┐
    │ Discord    │   │ Slack      │   │ Telegram    │
    │ Adapter    │   │ Adapter    │   │ Adapter     │
    └────────────┘   └────────────┘   └─────────────┘
```

> 这就像机场的"值机柜台"——不管你是国际航班还是国内航班，行李都要过同一套安检系统。Channel Adapter 就是这个"统一安检"层。

### 为什么要保留 rawMessage？

因为回复时可能需要平台特有功能：
- Discord：可以在原消息上加 Reaction、回复引用
- Slack：可以在 Thread 中回复、更新消息
- Telegram：可以用 Inline Keyboard、编辑已发送消息

统一格式用于内部处理，原始格式用于与平台交互——两者缺一不可。

---

## 3. 消息路由：找到正确的 Agent

Gateway 收到标准化消息后，需要回答两个核心问题："这条消息属于谁？" "谁来处理它？"

### 步骤 A：查找或创建 Session

```
消息到达 Gateway
      │
      ├── sessionId 已存在？
      │     │
      │     ├── 是 → 从内存/数据库加载已有 Session
      │     │         │
      │     │         ├── Session 活跃？ → 直接使用
      │     │         └── Session 过期？ → 恢复上下文，重新激活
      │     │
      │     └── 否 → 创建新 Session
      │               │
      │               ├── 根据 Channel 配置找到对应 Agent 定义
      │               │   (哪个 Discord 频道 → 哪个 Agent？)
      │               │
      │               ├── 初始化 Session 上下文
      │               │   (对话历史 = 空，Memory = 从文件加载)
      │               │
      │               └── 写入数据库（持久化）
      │
      ▼
  得到: Session { agent: AgentDef, history: Message[], ... }
```

### 步骤 B：Session 与 Agent 的绑定

每个 Session 绑定一个 Agent 定义。Agent 定义来自配置文件，包含：

```typescript
interface AgentDefinition {
  name: string;              // Agent 名称
  soul: string;              // SOUL.md 内容（人格设定）
  agents: string;            // AGENTS.md 内容（操作手册）
  tools: ToolDefinition[];   // 可用工具列表
  llm: {
    provider: string;        // LLM Provider: 'openai' | 'anthropic' | 'google'
    model: string;           // 模型名称: 'gpt-4' | 'claude-3.5-sonnet' | ...
    fallback?: {             // 降级配置
      provider: string;
      model: string;
    };
  };
  memory: MemoryConfig;      // Memory 策略配置
  context: ContextConfig;    // Context Window 策略配置
}
```

### Channel → Agent 映射配置

```
配置文件中的映射关系:

  Discord #general 频道  ──▶  "通用助手" Agent
  Discord #code-review   ──▶  "代码审查" Agent
  Slack #team-ops        ──▶  "运维助手" Agent
  Telegram @mybot        ──▶  "个人助理" Agent
  Web UI                 ──▶  根据用户选择的 Agent
```

---

## 4. Lane-based Command Queue

这是 OpenClaw 架构中最精妙的设计之一。

### 问题：为什么需要队列？

想象这个场景——用户连续快速发送了三条消息：

```
时间线:
  t=0.0s  用户发送: "帮我查天气"
  t=0.5s  用户发送: "顺便也查一下股票"     ← Agent 还在处理第一条！
  t=1.0s  用户发送: "算了，先查天气就行"   ← Agent 还在处理第一条！
```

### 没有队列会怎样？（灾难场景）

如果三条消息同时触发三个独立的 Agent Runner：

```
❌ 没有队列的情况 — 竞态条件（Race Condition）:

时间    Runner A ("查天气")    Runner B ("查股票")    Runner C ("算了")
─────  ────────────────────  ────────────────────  ────────────────────
t=0    读取对话历史 [空]      读取对话历史 [空]      读取对话历史 [空]
       ↑ 三者都看到空历史！
       
t=1    调用 LLM...           调用 LLM...           调用 LLM...
       ↑ 三者都不知道彼此的存在！
       
t=2    写入回复:"北京25°C"  写入回复:"股市涨了"  写入回复:"好的只查天气"
       ↑ 三者互相覆盖对话历史！

结果:
  • 对话历史变成一团糟——顺序混乱、消息交错
  • Runner C 说"好的只查天气"但它根本没看到前两条消息
  • 状态不一致：数据库里的对话历史取决于谁最后写入
  • 不可预测：每次运行结果可能不同
```

### 解决方案：Lane Queue（车道队列）

```
✅ 有 Lane 队列的情况 — 严格串行:

Lane (Session_ABC 专属):
  ┌─────────────────┬─────────────────┬──────────────────────┐
  │  "帮我查天气"    │ "顺便查股票"    │ "算了先查天气就行"   │
  │  (正在处理 ⏳)   │  (等待中 ⏸️)     │  (等待中 ⏸️)          │
  └─────────────────┴─────────────────┴──────────────────────┘
         │
         ▼
  Agent Runner 串行处理:

  1. 处理"帮我查天气"
     → 调用天气 API → 回复"北京25°C"
     → ✅ 完成，更新对话历史
     
  2. 处理"顺便也查一下股票"
     → 此时对话历史已包含第1条消息和回复
     → Agent 理解上下文："用户之前查了天气，现在还想查股票"
     → 调用股票 API → 回复结果
     → ✅ 完成，更新对话历史
     
  3. 处理"算了，先查天气就行"
     → 此时对话历史已包含前两条和所有回复
     → Agent 理解："用户改主意了"
     → 回复"好的，天气信息已经给您了..."
     → ✅ 完成
```

### Lane 的核心设计原则

```
┌──────────────────────────────────────────────────────┐
│              Lane Queue 系统                          │
│                                                      │
│  Lane "sess_001":  [msg1] → [msg2] → [msg3]   串行  │
│  Lane "sess_002":  [msgA] → [msgB]             串行  │
│  Lane "sess_003":  [msgX]                      串行  │
│         ↑              ↑           ↑                 │
│         └──────────────┼───────────┘                 │
│                        │                             │
│               不同 Lane 之间 并行                     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**三条核心规则：**

| 规则 | 说明 | 目的 |
|------|------|------|
| **一个 Session 对应一个 Lane** | 同一对话的消息排在同一条"车道" | 保证状态一致性 |
| **Lane 内 FIFO** | 先到先处理，严格按顺序 | 保证因果顺序 |
| **不同 Lane 之间并行** | 不同用户的对话可以同时处理 | 保证吞吐量 |

### 类比理解

```
Lane Queue 就像银行的"叫号系统":

  每个柜台 = 一个 Agent Runner
  每个客户的排队号 = Lane 中的消息
  
  • 同一个客户的业务必须在同一个柜台按顺序办理（Lane 内串行）
  • 不同客户可以在不同柜台同时办理（Lane 间并行）
  • 客户不能插队到别人的窗口（Session 隔离）
```

> **面试关键**：Lane 的本质是 **per-session 的串行化**，解决的核心问题是 **竞态条件（Race Condition）** 和 **状态不一致（State Inconsistency）**。它在"隔离性"和"并发度"之间找到了最佳平衡。

---

## 5. Agent Runner 核心：`runAgentTurnWithFallback()`

当消息从 Lane 队列中取出后，就进入了 Agent Runner 的核心函数。这是整个系统中 **最复杂、最重要** 的单个函数。

### 函数签名

```typescript
async function runAgentTurnWithFallback(
  session: Session,
  message: InternalMessage,
  agent: AgentDefinition,
  options: RunOptions
): Promise<AgentRunLoopResult> {
  // ...
}
```

### 函数名的含义

- `runAgentTurn`：运行一轮 Agent 处理（一条用户消息 → 一个完整回复）
- `WithFallback`：带有降级机制（主 LLM 失败 → 切换到备选 LLM）

### 完整执行流程

```
runAgentTurnWithFallback() 被调用
  │
  ├── ① 检查重试防护标志（三道安全门）
  │       │
  │       ├── isAlreadyRetrying?     → 防止重复重试（并发重入保护）
  │       ├── isCooldownActive?      → 防止频繁重试（API 限流保护）
  │       └── hasExceededMaxRetries?  → 防止无限重试（最终兜底）
  │       │
  │       └── 任一为 true → 直接返回 { status: "final" }
  │
  ├── ② 组装 System Prompt
  │       │
  │       ├── 加载 SOUL.md（Agent 的人格与核心指令）
  │       ├── 加载 AGENTS.md（操作手册与行为规范）
  │       ├── 注入工具定义（Tool Schemas）
  │       ├── 注入运行时上下文（当前时间、用户信息等）
  │       └── 拼接为完整的 System Prompt 字符串
  │
  ├── ③ 加载 Memory
  │       │
  │       ├── 加载会话历史（当前对话的所有消息）
  │       ├── 加载 MEMORY.md（持久化跨会话记忆）
  │       ├── 加载 USER.md（用户偏好信息）
  │       └── 按需加载 memory/YYYY-MM-DD.md（当日工作记忆）
  │
  ├── ④ 检查 Context Window
  │       │
  │       ├── 计算总 Token 数（System Prompt + Memory + 历史 + 工具定义）
  │       ├── 是否超过安全阈值？（通常是模型上限 × 0.8）
  │       │     │
  │       │     ├── 否 → 继续
  │       │     └── 是 → 触发 Compaction（压缩旧对话）
  │       │
  │       └── Compaction 后仍超限？ → 返回 { status: "final", reason: "context_overflow" }
  │
  ├── ⑤ 调用 LLM API（进入 ReAct 循环 — 下节课详讲）
  │       │
  │       ├── 发送组装好的 messages[] 给 LLM
  │       ├── 流式接收 response（token by token）
  │       │
  │       ├── LLM 返回纯文本？ → 推送给用户 → 循环结束
  │       │
  │       └── LLM 返回工具调用？
  │             │
  │             ├── 执行工具
  │             ├── 工具结果追加到 messages[]
  │             └── 再次调用 LLM → 继续循环...
  │
  ├── ⑥ 错误处理 + Fallback
  │       │
  │       ├── 主 LLM 调用失败？
  │       │     │
  │       │     ├── 有 fallback 配置？ → 切换到备选 LLM 重试
  │       │     └── 无 fallback？ → 标记错误，进入重试流程
  │       │
  │       └── 更新重试计数和冷却时间
  │
  └── ⑦ 返回 AgentRunLoopResult
```

### 三个重试防护标志

这是工程上非常重要的细节——防止 Agent 陷入无限循环或资源耗尽。

| 标志 | 作用 | 触发条件 | 重置条件 |
|------|------|---------|---------|
| `isAlreadyRetrying` | 防止并发重入 | 当前函数正在执行重试 | 重试完成（成功或放弃） |
| `isCooldownActive` | 冷却期保护 | 上次失败后，冷却时间未过 | 冷却时间到期 |
| `hasExceededMaxRetries` | 上限保护 | 连续重试次数达到最大值 | 成功处理一条消息后重置 |

```typescript
// 伪代码：重试防护逻辑
function checkRetryGuards(session: Session): AgentRunLoopResult | null {
  if (session.isAlreadyRetrying) {
    return { status: "final", reason: "already_retrying" };
  }
  
  if (session.isCooldownActive) {
    const remaining = session.cooldownExpiry - Date.now();
    return { status: "final", reason: "cooldown", retryAfterMs: remaining };
  }
  
  if (session.retryCount >= MAX_RETRIES) {
    return { status: "final", reason: "max_retries_exceeded" };
  }
  
  return null; // 所有检查通过，继续执行
}
```

### 为什么需要三个标志而不是一个？

```
场景分析:

  场景 1: 并发重入
  ─────────────────
  Lane 队列保证了消息串行，但如果 Runner 内部有异步重试逻辑，
  可能出现"上一次重试还没结束，新的重试又被触发"的情况。
  → isAlreadyRetrying 防止这种嵌套调用

  场景 2: 频繁失败
  ─────────────────
  如果 LLM API 暂时不可用（比如限流），短时间内密集重试只会
  加剧问题（thundering herd）。
  → isCooldownActive 强制等待一段冷却时间

  场景 3: 持续故障
  ─────────────────
  如果问题不是暂时性的（比如 API Key 过期），无限重试毫无意义。
  → hasExceededMaxRetries 设置最终上限，及时止损
```

> **面试考点**：为什么需要三个标志而不是一个？因为它们保护的场景不同——`isAlreadyRetrying` 防止并发重入，`isCooldownActive` 防止短时间内密集重试导致 API 限流（退避策略），`hasExceededMaxRetries` 是最终兜底。这体现了 **防御性编程（Defensive Programming）** 的思想。

---

## 6. 返回类型：AgentRunLoopResult

```typescript
interface AgentRunLoopResult {
  status: "success" | "final";
  response?: string;           // Agent 的回复文本
  toolCalls?: ToolCallRecord[]; // 本轮执行的工具调用记录
  reason?: string;             // 如果 status 是 "final"，终止原因
  tokenUsage?: TokenUsage;     // Token 使用量统计
}
```

### 两种状态的区别

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  status: "success"                                           │
│  ════════════════                                            │
│                                                              │
│  含义: 本轮处理成功完成 ✅                                    │
│                                                              │
│  场景:                                                       │
│    • LLM 给出了最终回复，无需继续循环                         │
│    • 用户的请求被完整处理                                     │
│                                                              │
│  后续动作:                                                    │
│    • 回复通过 WebSocket 推送给用户                            │
│    • 更新对话历史                                             │
│    • 更新 Memory（如果需要）                                  │
│    • Lane 队列处理下一条消息                                  │
│                                                              │
│  示例:                                                       │
│    { status: "success",                                      │
│      response: "北京今天晴天，气温25°C",                     │
│      toolCalls: [{ name: "weather_api", args: {...} }],      │
│      tokenUsage: { prompt: 5000, completion: 200 } }         │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  status: "final"                                             │
│  ════════════════                                            │
│                                                              │
│  含义: 本轮处理被终止（非正常完成）⛔                         │
│                                                              │
│  场景:                                                       │
│    • 重试次数耗尽 (reason: "max_retries_exceeded")           │
│    • Context Window 溢出无法恢复 (reason: "context_overflow")│
│    • LLM API 持续报错 (reason: "llm_error")                 │
│    • 冷却期保护触发 (reason: "cooldown")                     │
│    • 并发重入检测 (reason: "already_retrying")               │
│                                                              │
│  后续动作:                                                    │
│    • 记录错误日志                                             │
│    • 向用户发送错误提示（如"抱歉，我暂时无法处理..."）        │
│    • Lane 队列处理下一条消息                                  │
│                                                              │
│  示例:                                                       │
│    { status: "final",                                        │
│      reason: "max_retries_exceeded",                         │
│      tokenUsage: { prompt: 3000, completion: 0 } }           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 为什么不用 "success" / "error"？

```
设计思考:

  "success" vs "error" 的问题：
    → "error" 暗示"出了 bug"，需要修复
    → 但 "final" 中的很多情况不是 bug：
      - max_retries_exceeded: 不是 bug，是正常的防护机制生效
      - cooldown: 不是 bug，是合理的退避策略
      - context_overflow: 不是 bug，是物理约束

  "success" vs "final" 的语义：
    → "success" = 任务正常完成了
    → "final"  = 这一轮结束了，但不一定是正常完成
    → 两者都表示 Runner 的一轮执行到此为止
    
  调用方的处理逻辑：
    if (result.status === "success") → 把回复展示给用户
    if (result.status === "final")  → 根据 reason 决定展示什么
```

> **关键区别**："success" = 任务完成了；"final" = 任务被终止了。两者都表示这一轮 Agent 运行结束，但原因和后续处理不同。

---

## 7. 完整消息处理序列图

```
    用户         Channel        Adapter         Gateway         Lane Queue     Agent Runner       LLM API
     │              │              │               │                │               │               │
     │  发送消息    │              │               │                │               │               │
     │─────────────▶│              │               │                │               │               │
     │              │              │               │                │               │               │
     │              │  原始消息    │               │                │               │               │
     │              │─────────────▶│               │                │               │               │
     │              │              │               │                │               │               │
     │              │              │  标准化消息    │                │               │               │
     │              │              │──────────────▶│                │               │               │
     │              │              │               │                │               │               │
     │              │              │               │  认证 + 路由   │               │               │
     │              │              │               │  找到 Session  │               │               │
     │              │              │               │                │               │               │
     │              │              │               │  入队          │               │               │
     │              │              │               │───────────────▶│               │               │
     │              │              │               │                │               │               │
     │              │              │               │                │  出队          │               │
     │              │              │               │                │──────────────▶│               │
     │              │              │               │                │               │               │
     │              │              │               │                │               │  组装Prompt   │
     │              │              │               │                │               │  + 调用 LLM   │
     │              │              │               │                │               │──────────────▶│
     │              │              │               │                │               │               │
     │              │              │               │                │               │  流式返回     │
     │              │              │               │                │               │◀──────────────│
     │              │              │               │                │               │               │
     │◀══════════════════════════════ 流式推送回复 (WebSocket) ═══════│               │
     │              │              │               │                │               │               │
     │  收到回复    │              │               │                │               │               │
     ▼              ▼              ▼               ▼                ▼               ▼               ▼
```

---

## 8. 面试考点

> **高频题 1**：为什么使用 Lane Queue 而不是简单的全局队列？
>
> **参考思路**：全局队列有两个致命问题——① **不同用户互相阻塞**：用户A的长任务（10分钟）会阻塞用户B的简单问题（2秒）；② **同一用户的消息可能被乱序处理**：消息 1 分配给 Runner A，消息 2 分配给 Runner B，谁先完成是不确定的。Lane Queue 是 per-session 的，同一 Session 内串行保证状态一致性，不同 Session 之间并行保证吞吐量。这是"隔离性"和"并发度"的最佳平衡。

> **高频题 2**：`runAgentTurnWithFallback()` 中的 fallback 指什么？怎么实现？
>
> **参考思路**：fallback 是容错降级机制。当主 LLM Provider（比如 GPT-4）调用失败时，可以自动切换到备选 Provider（比如 Claude）。实现上，Agent 配置中定义了 `llm.fallback` 字段，Runner 在主调用失败后检查该配置，如果有则替换 Provider 重试。三个重试防护标志确保 fallback 过程不会失控——不会无限重试、不会并发重试、有冷却间隔。

> **高频题 3**：如何向面试官解释 "success" 和 "final" 两种返回状态的设计意图？
>
> **参考思路**：这是一种 **明确区分正常终止和非正常终止** 的设计。不用 "success/error" 是因为 "final" 中的很多情况不是真正的错误（如冷却期保护、最大重试限制），而是设计好的安全机制生效。调用方可以根据 status 决定给用户展示什么：success 展示回复，final 根据 reason 展示不同的提示信息。

> **进阶题**：如果一个 Session 的 Lane 队列堆积了 100 条消息，你会怎么处理？
>
> **参考思路**：这说明 Agent 的处理速度远低于用户的发送速度。可以考虑：① **队列深度限制**——超过 N 条时拒绝新消息并告知用户"稍后再试"；② **消息合并**——将多条等待中的消息合并为一条发送给 Agent；③ **优先级队列**——让最新的消息优先处理，旧消息降级或丢弃（取决于业务场景）。

---

## 9. 课后练习

### 练习 1：消息旅程复述

不看笔记，用自己的话描述一条用户消息从 Discord 输入框到最终收到回复的完整链路。要求：
- 至少包含 7 个关键节点
- 每个节点说明"做了什么"和"为什么要做"
- 标注哪些在控制面、哪些在数据面

### 练习 2：竞态条件分析

假设没有 Lane Queue，画出以下场景的时序图，指出会发生什么具体问题：
- 用户在 t=0 发送 "创建一个文件 test.txt"
- 用户在 t=0.5s 发送 "在 test.txt 里写入 Hello"
- 两条消息被两个 Runner 同时处理

分析：① 可能的执行顺序有几种？② 每种顺序的结果是什么？③ 哪些结果是错误的？

### 练习 3：防护标志设计

如果让你从零设计 Agent Runner 的重试机制，请回答：
1. 你会设计哪些防护标志？每个标志的触发条件和重置条件是什么？
2. 冷却时间应该是固定的还是指数退避（exponential backoff）？为什么？
3. 最大重试次数应该设为多少？根据什么因素决定？
4. 对比你的设计和 OpenClaw 的三标志方案，有什么异同？

---

> [上一课 ← 06-gateway-architecture](./06-gateway-architecture.md) | [下一课 → 08-react-loop](./08-react-loop.md) | [回到目录](../README.md)
