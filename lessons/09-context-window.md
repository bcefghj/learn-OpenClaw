# 第九课：Context Window — 最核心的工程约束

> **阶段二 · 核心架构** | [上一课 ←](./08-react-loop.md) | [下一课 →](./10-memory-system.md) | [目录](../README.md)

---

## 本课目标

学完这节课，你能回答：

1. 为什么 Context Window 被称为"Agent 工程中最核心的约束"？
2. 长对话时面临哪些挑战？有哪些解决方案？
3. OpenClaw 的 Context Engine 可插拔抽象层是怎么设计的？
4. 工具返回超大结果（如 50KB）时怎么处理？
5. Compaction 策略是什么？什么时候触发？
6. Context Overflow 的两条检测路径分别是什么？为什么路径 B 更危险？

---

## 1. 什么是 Context Window？

### 用"工作台"比喻

想象你有一张 **固定大小的工作台**——这就是 Context Window：

- 工作台上可以放图纸（System Prompt）、笔记本（对话历史）、工具箱（工具定义）、参考资料（Memory）
- 工作台的大小是 **固定的**——不管你多想放更多东西，放不下就是放不下
- 如果工作台满了，你必须 **收走一些旧东西** 才能放新东西
- **LLM 只能看到工作台上的内容**——不在工作台上的，它完全看不到

```
┌────────────────── Context Window (工作台) ────────────────────┐
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐     │
│  │ System      │  │ 工具定义     │  │ Memory            │     │
│  │ Prompt      │  │ (Tools)     │  │ (记忆)            │     │
│  │ ~3K tokens  │  │ ~2K tokens  │  │ ~5K tokens        │     │
│  └─────────────┘  └─────────────┘  └───────────────────┘     │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                    对话历史                              │   │
│  │  User: 帮我查天气                                      │   │
│  │  Assistant: [调用 weather_api]                          │   │
│  │  Tool: {"temp": 25, "condition": "晴"}                 │   │
│  │  Assistant: 北京今天晴天，25°C                          │   │
│  │  User: 那明天呢？                                      │   │
│  │  ...                                                   │   │
│  │                                      ~30K tokens       │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  已用: 40,000 tokens / 上限: 128,000 tokens                   │
│  ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░  31%               │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 各模型的 Context Window 大小

| 模型 | Context Window | 大约等于 | 价格区间 |
|------|---------------|---------|---------|
| GPT-4 Turbo | 128K tokens | ~96,000 个中文字 | $0.01/1K input |
| GPT-4o | 128K tokens | ~96,000 个中文字 | $0.005/1K input |
| Claude 3.5 Sonnet | 200K tokens | ~150,000 个中文字 | $0.003/1K input |
| Gemini 1.5 Pro | 1M tokens | ~750,000 个中文字 | $0.00125/1K input |
| GPT-3.5 Turbo | 16K tokens | ~12,000 个中文字 | $0.0005/1K input |

### 看起来很大？Agent 场景会快速消耗

```
典型的一轮 Agent 运行的 Token 消耗:

  System Prompt (SOUL.md + AGENTS.md):       ~3,000 tokens   (固定开销)
  工具定义 (10 个工具的 Schema):              ~2,000 tokens   (固定开销)
  Memory (MEMORY.md + USER.md):              ~5,000 tokens   (半固定)
  本轮用户消息:                               ~500 tokens     (变量)
  工具调用结果:                               ~5,000-50,000 tokens ← 最大变量！
  ──────────────────────────────────────────
  单轮消耗:                                   ~15,500-60,500 tokens

  5 轮 ReAct 循环后:
    累积消耗:                                 ~50,000-128,000 tokens
    
  即使是 128K 的 GPT-4 Turbo，5 轮循环后也可能接近满载！
```

### 为什么是"最核心的约束"？

```
Agent 的所有高级能力都受 Context Window 限制:

  多轮工具调用    → 每轮增加 Context 消耗 → 限制 ReAct 循环次数
  长对话          → 历史不断累积 → 总有装不下的时候
  丰富的 Memory   → Memory 越详细越好 → 但也要占 Context 空间
  复杂 System Prompt → 人格越丰富越好 → 但也要占 Context 空间
  大量工具        → 工具越多能力越强 → 但 Schema 也要占空间
  
  所有功能互相"抢"同一个 Context 空间
  → Context Window 是所有功能的"天花板"
  → 管好 Context = 管好 Agent 的上限
```

> **核心认知**：Context Window 不是"大就够用"的问题。在多轮工具调用的 Agent 场景下，Context 消耗速度远超普通聊天。**这就是为什么 Context 管理是 Agent 工程中最核心的约束之一——它是所有高级功能的瓶颈。**

---

## 2. 长对话的挑战

### 问题场景：一个持续 1 小时的对话

```
对话第 1 轮:   用了 20K tokens ──▶ 剩余 108K  ✅ 很充裕
对话第 5 轮:   用了 50K tokens ──▶ 剩余  78K  ✅ 还行
对话第 10 轮:  用了 85K tokens ──▶ 剩余  43K  ⚠️ 开始紧张
对话第 15 轮:  用了 110K tokens ──▶ 剩余  18K  🔴 危险！
对话第 18 轮:  用了 125K tokens ──▶ 剩余   3K  💀 即将溢出
对话第 19 轮:  用了 130K tokens ──▶ 溢出！💥 LLM 拒绝处理

怎么办？
```

### 核心矛盾

```
矛盾: 我们想保留完整对话历史（让 Agent 记住所有聊过的内容）
      但 Context Window 是有限的（放不下那么多内容）

这不是一个"技术可以解决"的问题，而是一个"必须做取舍"的约束
→ 问题变成: 保留什么？丢弃什么？如何让丢弃的信息损失最小？
```

### 解决方案概览

```
策略 1: 截断（Truncation）
  ─────────────────────
  做法: 删掉最早的对话历史
  优点: 简单、快速、零额外开销
  缺点: 可能丢失重要上下文（"你之前说要帮我分析那个数据"——被删了）
  适用: 简单闲聊场景

策略 2: 压缩（Compaction）
  ─────────────────────
  做法: 用 LLM 将旧对话总结为摘要，用摘要替代原文
  优点: 保留语义信息，信息损失小
  缺点: 需要额外 LLM 调用（延迟 + 费用）
  适用: 需要长期上下文的场景

策略 3: 工具结果截断（Tool Result Truncation）
  ─────────────────────
  做法: 对超大的工具返回结果进行截断
  优点: 保护 Context 不被单次工具调用撑爆
  缺点: 可能丢失部分工具返回的有用信息
  适用: 工具密集型 Agent

策略 4: 滑动窗口（Sliding Window）
  ─────────────────────
  做法: 保留最近 N 轮对话 + System Prompt，丢弃更早的
  优点: 简单有效，始终保持最新上下文
  缺点: 早期上下文完全丢失
  适用: 对历史不敏感的场景

策略 5: 混合策略（Hybrid）
  ─────────────────────
  做法: 按优先级组合多种策略
  优点: 兼顾各种情况
  复杂度: 最高
  适用: 通用场景（OpenClaw 默认推荐）
```

---

## 3. OpenClaw 的 Context Engine

### 可插拔抽象层设计

OpenClaw 没有把 Context 管理写死成某一种策略，而是设计了一个 **可插拔的 Context Engine 抽象层**：

```typescript
interface ContextEngine {
  // 组装发送给 LLM 的 messages 数组
  assembleContext(
    session: Session,
    newMessage: Message,
    options: ContextOptions
  ): Promise<AssembledContext>;

  // 检查是否接近或已经溢出
  checkOverflow(
    messages: Message[],
    modelLimit: number
  ): OverflowCheckResult;

  // 执行压缩/截断
  compact(
    messages: Message[],
    strategy: CompactionStrategy
  ): Promise<Message[]>;

  // 估算 Token 数
  estimateTokens(messages: Message[]): number;
}

interface AssembledContext {
  messages: Message[];        // 组装好的消息数组
  totalTokens: number;        // 总 Token 数
  wasCompacted: boolean;      // 是否触发了压缩
  droppedMessages: number;    // 被丢弃的消息数量
}

interface OverflowCheckResult {
  isOverflow: boolean;        // 是否溢出
  utilizationRatio: number;   // 使用率 (0-1)
  suggestedAction: "none" | "compact" | "truncate" | "abort";
}
```

### 为什么要可插拔？

不同类型的 Agent 有不同的 Context 需求：

```
"客服 Agent" → 需要保留完整对话历史
  → 用户提到的细节不能丢（"我上次说的那个订单号"）
  → 策略: compaction 为主，尽量保留语义

"搜索 Agent" → 工具返回大量结果
  → 搜索结果用完就可以丢弃
  → 策略: truncate_tools 为主，激进截断工具结果

"代码审查 Agent" → 需要保留完整代码上下文
  → 代码不能被截断（断了就没法分析了）
  → 策略: sliding_window，保留最近的代码块

"日报 Agent" → 每次独立运行，上下文不长
  → 几乎不需要 Compaction
  → 策略: 简单截断就够了
```

> **设计哲学**：通过接口抽象，不同的 Agent 可以使用不同的 Context 管理策略。这是"策略模式（Strategy Pattern）"的应用。

### Context 组装的优先级

当空间不够时，哪些内容优先保留？

```
优先级从高到低:

  P0 (必须保留 — 没有这些 Agent 无法工作):
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • System Prompt (SOUL.md + AGENTS.md)
    • 工具定义 (Tool Schemas)
    • 当前用户消息（这轮要处理的）
    
  P1 (高优先级 — Agent 理解当前任务的基础):
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • 最近 2-3 轮对话
    • 本轮工具调用的结果
    
  P2 (中优先级 — 提供上下文和个性化):
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • Memory (MEMORY.md / USER.md)
    • 近期对话历史（第 4-10 轮）
    
  P3 (低优先级 — 可以被压缩):
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • 早期对话历史（第 10 轮以前）
    → 可以被 Compaction 压缩为摘要
    
  P4 (最低优先级 — 可以被截断):
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • 超大工具返回结果（>阈值的部分）
    → 可以截断到关键片段
```

---

## 4. 工具返回超大结果的处理

### 问题场景：50KB 的搜索结果

```
用户: "搜索所有关于量子计算的最新论文"

web_search 工具返回: 50KB 的 JSON 数据
  ≈ 40,000 tokens
  ≈ 128K 上限的 31%

一个工具结果就吃掉了接近三分之一的 Context 空间！
如果再调用几次搜索... 💥
```

### OpenClaw 的处理方案

```
工具返回结果
     │
     ▼
┌──────────────────┐
│  检查结果大小     │
│  countTokens()   │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
  ≤ 阈值    > 阈值 (例如 10K tokens)
    │         │
    ▼         ▼
 原样保留  ┌─────────────────────────────────────┐
           │  截断策略 (按优先级尝试):             │
           │                                     │
           │  策略 A: 智能截断                    │
           │  ───────────────                    │
           │  • 如果是列表结果: 保留前 N 条       │
           │  • 附加: "...还有 M 条结果被省略"    │
           │  • 保留结构完整性                    │
           │                                     │
           │  策略 B: 摘要替代                    │
           │  ───────────────                    │
           │  • 用 LLM 对结果做快速摘要           │
           │  • 将摘要替换原始数据                │
           │  • 保留语义，大幅压缩体积            │
           │  （额外开销: 一次 LLM 调用）         │
           │                                     │
           │  策略 C: 硬截断（最后兜底）           │
           │  ───────────────                    │
           │  • 直接截断到 N tokens              │
           │  • 附加 "[结果已截断]" 提示          │
           │  • 简单粗暴，信息损失最大            │
           │                                     │
           └─────────────────────────────────────┘
```

### 代码示例

```typescript
function truncateToolResult(
  result: string, 
  maxTokens: number,
  strategy: "smart" | "summarize" | "hard" = "smart"
): string | Promise<string> {
  
  const tokens = countTokens(result);
  if (tokens <= maxTokens) {
    return result;
  }

  switch (strategy) {
    case "smart": {
      const parsed = tryParseJSON(result);
      if (Array.isArray(parsed)) {
        const kept = parsed.slice(0, 10);
        const omitted = parsed.length - 10;
        return JSON.stringify(kept) + 
          `\n\n[显示前10条结果，还有${omitted}条结果被省略]`;
      }
      // 非数组：回退到硬截断
      return truncateToTokens(result, maxTokens - 100) +
        `\n\n[结果已截断，原始大小: ${tokens} tokens]`;
    }
      
    case "summarize":
      return summarizeWithLLM(result, maxTokens);
      
    case "hard":
      return truncateToTokens(result, maxTokens - 100) +
        `\n\n[结果已截断，原始大小: ${tokens} tokens]`;
  }
}
```

### 截断 vs 不截断的 trade-off

```
完全不截断:
  ✅ 信息完整
  ❌ Context 被一个工具结果撑爆
  ❌ 后续轮次没有空间
  ❌ 可能直接导致 Context Overflow

过度截断:
  ✅ Context 空间充裕
  ❌ Agent 看到的信息不完整
  ❌ 可能基于不完整的信息做出错误判断
  ❌ "搜了10篇论文但只给你看1篇的摘要"

合理截断:
  ✅ 保留关键信息
  ✅ Context 空间可控
  ⚠️ 需要精心设计截断策略
  → 这就是工程的艺术
```

> **面试考点**：工具结果截断是"信息保真度 vs Context 空间"的 trade-off。好的截断策略应该：① 保留结构化信息（如 JSON 中的关键字段）；② 明确标注截断发生（让 Agent 知道信息不完整）；③ 提供获取完整信息的方式（如"如果需要更多细节，可以调用 read_url 查看完整内容"）。

---

## 5. Compaction 策略

### 什么是 Compaction？

当对话变得很长时，用 LLM 把旧对话 **压缩成摘要**，用摘要替代原始消息：

```
压缩前（15 轮对话，约 50K tokens）:
──────────────────────────────────
  User: 帮我分析这份Q3财报
  Assistant: 好的，我先下载 PDF...
  Tool: [read_pdf 返回 10K tokens 的 PDF 内容]
  Assistant: 我看到收入增长了 20%，让我详细分析...
  User: 利润率呢？
  Assistant: 净利润率是 15%，比去年提高了 3 个百分点...
  User: 研发投入占比多少？
  Assistant: 研发投入占收入的 12%...
  User: 和竞争对手比呢？
  Assistant: 让我搜索竞争对手的数据...
  Tool: [web_search 返回 8K tokens]
  ... (更多对话) ...

压缩后（约 2K tokens）:
──────────────────────────────────
  [对话摘要]:
  用户请求分析 Q3 财报。已完成的分析：
  1. 收入同比增长 20%
  2. 净利润率 15%（同比 +3pp）
  3. 研发投入占比 12%
  4. 已搜索竞争对手数据进行对比
  
  关键发现：公司表现优于行业平均，但研发投入低于头部竞争对手。
  用户特别关注利润率趋势和研发投入回报。

信息密度大幅提升: 50K tokens → 2K tokens (25倍压缩)
```

### Compaction 触发时机

```
每次 LLM 调用前的 Context 检查:

  计算总 Token 数
       │
       ▼
  ┌───────────────────────────────────────┐
  │  使用率 = 总Token / 模型上限          │
  └───────────────────┬───────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
      < 70%       70% ~ 85%     > 85%
         │            │            │
         ▼            ▼            ▼
      正常继续    预警模式      触发 Compaction
                  (下一轮可        │
                   能需要压缩)     ├── 1. 选择要压缩的消息范围
                                   │      (通常是最早的 50% 对话)
                                   │
                                   ├── 2. 调用 LLM 生成摘要
                                   │      "请总结以下对话的关键信息..."
                                   │
                                   ├── 3. 用摘要消息替换原始消息
                                   │      messages = [systemPrompt, 
                                   │                  summary, 
                                   │                  ...recentMessages]
                                   │
                                   └── 4. 重新计算 Token 数
                                          确认在安全阈值内
```

### Compaction 的成本

```
Compaction 不是免费的:

  时间成本:
    • 需要额外一次 LLM 调用来生成摘要
    • 增加 1-5 秒延迟
    
  金钱成本:
    • 摘要请求本身消耗 Token
    • 输入: 被压缩的消息 (可能 20-50K tokens)
    • 输出: 摘要 (约 1-2K tokens)
    • 大约 $0.02-0.05 每次
    
  信息成本:
    • 再好的摘要也有信息损失
    • "用户在第3轮提到的那个具体错误代码"可能被遗漏
    
  → 这是"用时间和金钱换 Context 空间"的 trade-off
  → 不能太频繁（成本高），也不能太迟（溢出了就晚了）
```

### Compaction 与 Memory flush 的关系

```
Compaction 和 Memory 是互补的:

  Compaction:
    "我的 Context 快满了，把旧对话压缩一下"
    → 短期行为，只影响当前会话的 Context
    → 压缩后的摘要留在 messages[] 中
    
  Memory flush:
    "这些重要信息应该长期记住"
    → 长期行为，写入 MEMORY.md / daily memory
    → 下次会话也能访问
    
  它们经常同时发生:
    触发 Compaction 时 → 顺便把关键信息写入 Memory
    → 即使 Compaction 丢失了细节，Memory 里还有备份
    
  流程:
    对话太长 → 触发 Compaction
                 │
                 ├── 1. 生成摘要（替换旧消息）
                 └── 2. 提取关键信息 → flush 到 MEMORY.md
```

---

## 6. Context Overflow 的两条检测路径

这是一个非常重要的工程细节——OpenClaw 有 **两条** 检测 Context 溢出的路径，而大多数开发者只知道其中一条。

```
┌─────────────────────────────────────────────────────────────────┐
│                 Context Overflow 检测                             │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  路径 A：异常抛出（Exception）                             │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                              │  │
│  │                                                           │  │
│  │  发生时机: LLM API 调用时，Provider 直接返回错误          │  │
│  │  HTTP 状态: 400 Bad Request                               │  │
│  │  错误信息: "This model's maximum context length is        │  │
│  │            128000 tokens. However, your messages           │  │
│  │            resulted in 135000 tokens."                     │  │
│  │                                                           │  │
│  │  表现形式: 抛出 ContextOverflowError 异常                 │  │
│  │                                                           │  │
│  │  特点:                                                    │  │
│  │    ✅ 显式的、容易捕获                                    │  │
│  │    ✅ 错误信息明确（告诉你超了多少）                       │  │
│  │    ✅ 用 try-catch 就能处理                                │  │
│  │    ⚠️ 通常发生在 Token 计数不准确的情况下                  │  │
│  │       (本地估算 < 实际值，所以没被提前拦住)               │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  路径 B：meta 里的隐藏错误 ⚠️ 更危险！                    │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                    │  │
│  │                                                           │  │
│  │  发生时机: LLM API "成功"返回，但响应实际被截断          │  │
│  │  HTTP 状态: 200 OK  ← 看起来完全正常！                    │  │
│  │                                                           │  │
│  │  表现形式: response.meta 中包含溢出标记                   │  │
│  │                                                           │  │
│  │  示例响应:                                                │  │
│  │    {                                                      │  │
│  │      "choices": [{                                        │  │
│  │        "message": { "content": "根据分析，这份报告..." }, │  │
│  │        "finish_reason": "length"   ← 🔴 被截断了！        │  │
│  │      }],                                                  │  │
│  │      "usage": {                                           │  │
│  │        "prompt_tokens": 127500,    ← 已经用了 99.6%      │  │
│  │        "completion_tokens": 500    ← 只生成了 500 token   │  │
│  │      }                              (正常应该 2000+)      │  │
│  │    }                                                      │  │
│  │                                                           │  │
│  │  特点:                                                    │  │
│  │    ❌ 隐式的、非常容易被忽略！                             │  │
│  │    ❌ HTTP 200 OK — 看起来"一切正常"                      │  │
│  │    ❌ 响应格式完整，不会触发错误处理                       │  │
│  │    ❌ 必须主动检查 finish_reason 和 usage 才能发现         │  │
│  │    ❌ Agent 可能基于不完整的回复继续行动                   │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 为什么路径 B 更危险？

```
路径 A（显式异常）— 容易处理:

  调用 LLM
    │
    └── ❌ 400 Error: "context length exceeded"
         │
         └── catch (error) {
               triggerCompaction();  // 压缩后重试
               retryLLMCall();
             }
  
  → 开发者一定知道出问题了
  → 错误处理流程会被触发
  → 相对容易修复


路径 B（隐藏错误）— 极其危险:

  调用 LLM
    │
    └── ✅ 200 OK, 返回了响应
         │
         └── 看起来正常...
              │
              └── 但 finish_reason 是 "length" 而不是 "stop"
                   │
                   └── 回复被截断了！
                        │
                        ├── Agent 收到: "根据分析，这份报告..."
                        │   (本应是: "根据分析，这份报告显示三个问题：
                        │            1. 成本超支 2. 进度延迟 3. 质量下降")
                        │
                        ├── Agent 以为回复完整了 → 继续下一步
                        │
                        ├── 基于不完整信息做出决策 → 结果可能完全错误
                        │
                        └── 用户看到残缺的回复，感到困惑
                        
  → 如果代码里没有检查 finish_reason，这个问题会完全无声地发生
  → 没有错误日志、没有异常、没有任何提示
  → 是典型的"静默失败（Silent Failure）"
```

### 检测代码实现

```typescript
function checkForHiddenOverflow(response: LLMResponse): {
  isOverflow: boolean;
  details?: string;
} {
  // 检查 1: finish_reason 是否为 "length"（被截断）
  const finishReason = response.choices[0]?.finish_reason;
  if (finishReason === "length") {
    return {
      isOverflow: true,
      details: `Response truncated: finish_reason="length", ` +
               `completion_tokens=${response.usage.completion_tokens}`,
    };
  }

  // 检查 2: prompt_tokens 是否接近模型上限
  const ratio = response.usage.prompt_tokens / modelMaxTokens;
  if (ratio > 0.95) {
    return {
      isOverflow: true,
      details: `Near overflow: prompt used ${(ratio * 100).toFixed(1)}% ` +
               `of ${modelMaxTokens} token limit`,
    };
  }

  // 检查 3: completion_tokens 异常低（可能是被迫提前停止）
  if (response.usage.completion_tokens < 50 && 
      response.choices[0]?.finish_reason !== "stop") {
    return {
      isOverflow: true,
      details: `Suspiciously short completion: only ` +
               `${response.usage.completion_tokens} tokens`,
    };
  }

  return { isOverflow: false };
}
```

### 完整的双路径处理流程

```typescript
async function safeLLMCall(messages: Message[]): Promise<LLMResponse> {
  try {
    // ── 路径 A: try-catch 捕获显式异常 ──
    const response = await llm.chat(messages);
    
    // ── 路径 B: 主动检查隐藏溢出 ──
    const overflowCheck = checkForHiddenOverflow(response);
    if (overflowCheck.isOverflow) {
      logger.warn("Hidden context overflow detected", overflowCheck.details);
      
      // 触发与路径 A 相同的恢复流程
      const compacted = await compactMessages(messages);
      return await llm.chat(compacted);
    }
    
    return response;
    
  } catch (error) {
    if (error instanceof ContextOverflowError) {
      // 路径 A 的处理
      logger.error("Explicit context overflow", error.message);
      const compacted = await compactMessages(messages);
      return await llm.chat(compacted);
    }
    throw error;
  }
}
```

> **面试高频考点**：很多候选人只知道路径 A（异常），不知道路径 B（隐藏错误）。能答出路径 B 是加分项——说明你 **真正理解了 LLM API 的行为细节**，而不是只会用 try-catch。`finish_reason: "length"` 是一个容易被忽视但影响重大的信号。

---

## 7. Context Engine 的策略支持

OpenClaw 的 Context Engine 可以配置不同的策略组合：

| 策略 | 描述 | 适用场景 | 复杂度 |
|------|------|---------|--------|
| `sliding_window` | 保留最近 N 轮，丢弃最早的 | 简单对话，历史不重要 | 低 |
| `compaction` | 压缩旧对话为摘要 | 长对话，需要保留语义 | 中 |
| `truncate_tools` | 优先截断工具返回结果 | 工具密集型 Agent | 低 |
| `hybrid` | 组合多种策略，按优先级执行 | 通用场景（推荐默认） | 高 |
| `custom` | 自定义实现 ContextEngine 接口 | 特殊业务需求 | 取决于实现 |

### Hybrid 策略的执行顺序

```
hybrid 策略 — 按优先级逐步释放空间:

  ┌──────────────────────────────────────────────────────┐
  │  Step 1: 截断超大工具结果                             │
  │                                                      │
  │  遍历所有 tool message                               │
  │  if (toolResult.tokens > TOOL_THRESHOLD) {           │
  │    truncate(toolResult)                              │
  │  }                                                   │
  │                                                      │
  │  → 通常能释放 30-50% 的空间                          │
  └──────────────────────┬───────────────────────────────┘
                         │
                    空间够了？
                    ├── 是 → 完成 ✅
                    └── 否 ↓
                         │
  ┌──────────────────────┴───────────────────────────────┐
  │  Step 2: 压缩早期对话                                │
  │                                                      │
  │  选择最早的 50% 消息                                  │
  │  调用 LLM 生成摘要                                   │
  │  替换原始消息                                         │
  │                                                      │
  │  → 通常能释放 60-80% 的空间                          │
  └──────────────────────┬───────────────────────────────┘
                         │
                    空间够了？
                    ├── 是 → 完成 ✅
                    └── 否 ↓
                         │
  ┌──────────────────────┴───────────────────────────────┐
  │  Step 3: 滑动窗口                                    │
  │                                                      │
  │  只保留 System Prompt + 最近 3 轮对话                 │
  │  其他全部丢弃                                         │
  │                                                      │
  │  → 最激进的措施，信息损失最大                         │
  └──────────────────────┬───────────────────────────────┘
                         │
                    空间够了？
                    ├── 是 → 完成 ✅ (但用户体验受损)
                    └── 否 → 返回溢出错误 ❌
                             (status: "final",
                              reason: "context_overflow")
```

---

## 8. Context 管理完整流程图

```
                        新消息到达
                            │
                            ▼
                ┌─────────────────────────┐
                │   组装 Context           │
                │                         │
                │   P0: System Prompt     │
                │       + Tool Schemas    │
                │       + 当前消息        │
                │   P1: 最近对话          │
                │   P2: Memory            │
                │   P3: 早期历史          │
                │   P4: 工具结果          │
                └─────────────┬───────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │  Token 计数              │
                │  estimateTokens()       │
                │  使用率 = ?             │
                └─────────────┬───────────┘
                              │
                  ┌───────────┼───────────┐
                  │           │           │
               < 70%      70%-85%      > 85%
                  │           │           │
                  ▼           ▼           ▼
            直接发送      预警日志    ┌─────────────────────┐
            给 LLM       继续发送    │  触发 Compaction      │
                  │           │      │                     │
                  │           │      │  1. 截断工具结果     │
                  │           │      │  2. 压缩旧对话       │
                  │           │      │  3. 滑动窗口         │
                  │           │      └──────────┬──────────┘
                  │           │                 │
                  │           │            仍然超限？
                  │           │            ┌────┴────┐
                  │           │            │         │
                  │           │           否       是
                  │           │            │         │
                  │           │            ▼         ▼
                  │           │         发送 LLM  返回溢出错误
                  │           │            │    (final)
                  └───────┬───┘────────────┘
                          │
                          ▼
                ┌─────────────────────────┐
                │   LLM 返回响应           │
                └─────────────┬───────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │  双路径溢出检测           │
                │                         │
                │  路径 A: 异常？          │
                │    → try-catch 已处理    │
                │                         │
                │  路径 B: 隐藏溢出？      │
                │    → finish_reason?     │
                │    → usage.prompt_tokens?│
                └─────────────┬───────────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
                正常                 检测到溢出
                  │                       │
                  ▼                       ▼
            继续 ReAct              触发恢复流程
            循环                   Compact + 重试
```

---

## 9. 面试考点

> **高频题 1**：为什么说 Context Window 是 Agent 工程中最核心的约束？
>
> **参考思路**：因为 Agent 不只是聊天——它需要在 Context 里同时放入 System Prompt、工具定义、Memory、对话历史、工具调用结果等大量信息。每轮 ReAct 循环都会增加 Context 消耗（尤其是工具返回结果）。一旦溢出，Agent 要么报错终止，要么回复被截断导致行为异常。**所有高级功能（多轮工具调用、长对话、丰富记忆、大量工具）都在争抢同一个有限的 Context 空间**——Context Window 的大小直接决定了 Agent 能力的上限。

> **高频题 2**：Context Overflow 有几种检测方式？路径 B 为什么更危险？
>
> **参考思路**：两种——**路径 A** 是 LLM API 直接抛异常（HTTP 400，错误信息明确告诉你 token 数超限），用 try-catch 就能捕获；**路径 B** 是 API 返回 HTTP 200 OK，但 `finish_reason` 为 `"length"` 而非 `"stop"`。路径 B 更危险是因为它是"静默失败"——HTTP 状态码正常、响应格式完整、不会触发错误处理，但回复内容实际被截断了。如果代码没有主动检查 `finish_reason` 和 `usage`，Agent 会基于不完整的信息继续运行，导致难以排查的 bug。

> **高频题 3**：如何设计一个好的 Compaction 策略？
>
> **参考思路**：好的 Compaction 策略需要平衡三个维度：① **信息保真**——压缩后不能丢失关键信息（如用户明确提到的需求、关键数据点）；② **延迟开销**——Compaction 本身需要一次 LLM 调用，不能太频繁（建议在使用率 >80% 时触发，而非每轮都做）；③ **用户体验**——用户不应感知到 Compaction 的发生（压缩是后台进行的，不影响回复）。实践中推荐 hybrid 策略：先截断超大工具结果（成本最低），再压缩早期对话（效果最好），最后才用滑动窗口丢弃（损失最大）。

> **进阶题**：OpenClaw 的本地 Token 估算和 LLM Provider 的实际 Token 计数可能不一致，你怎么处理这个问题？
>
> **参考思路**：Token 计数不一致是 Context Overflow 的重要根因。解决方案：① 使用各 Provider 官方的 tokenizer（如 OpenAI 的 tiktoken）进行本地估算，提高准确性；② 在安全阈值中留出更大的 buffer（比如用 75% 而非 85%），容忍估算误差；③ 实现路径 B 的检测作为兜底——即使估算不准导致没有提前拦住，也能在 LLM 返回后发现问题；④ 记录每次实际 token 使用量与本地估算的差异，用于校准估算算法。

---

## 10. 课后练习

### 练习 1：Token 预算计算

假设你使用 GPT-4 Turbo（128K context），Agent 配置如下：
- System Prompt: 3,000 tokens
- 10 个工具定义: 2,000 tokens
- Memory: 5,000 tokens
- 安全阈值: 80%（即 102,400 tokens）

计算：
1. 可用于对话和工具结果的 Token 预算是多少？
2. 假设每轮用户消息 500 tokens，Agent 回复 1,000 tokens，工具调用结果平均 5,000 tokens。在不触发 Compaction 的情况下，最多能进行几轮 ReAct 循环？
3. 如果其中一轮的工具返回了 40,000 tokens（未截断），情况会怎样？

### 练习 2：溢出检测代码

写一个函数，同时检测路径 A（异常）和路径 B（隐藏错误）的 Context Overflow，要求：
- 路径 A: 通过 try-catch 捕获 ContextOverflowError
- 路径 B: 检查 `finish_reason`、`usage.prompt_tokens`、`usage.completion_tokens`
- 统一返回 `{ isOverflow: boolean, path: "A" | "B" | "none", details: string }`
- 如果检测到溢出，自动触发 Compaction 并重试

### 练习 3：策略设计

你正在为一个"法律顾问 Agent"设计 Context 管理策略。这个 Agent 的特点：
- 需要精确引用法律条文（不能丢失或截断法条内容）
- 支持 1 小时以上的长对话
- 需要对比分析多个法律文档
- 用户可能在对话中提到很久以前讨论过的案例

请设计你的 Context 管理方案，包括：
1. 使用哪种 Compaction 策略？为什么？
2. 工具结果（法律文档）如何截断？有哪些特殊考虑？
3. 优先级排序：哪些信息必须保留，哪些可以压缩？
4. 你会设置多大的安全阈值？为什么？

---

> [上一课 ← 08-react-loop](./08-react-loop.md) | [下一课 → 10-memory-system](./10-memory-system.md) | [回到目录](../README.md)
