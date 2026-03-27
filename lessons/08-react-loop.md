# 第八课：ReAct 循环 — Agent 的大脑回路

> **阶段二 · 核心架构** | [上一课 ←](./07-agent-runner.md) | [下一课 →](./09-context-window.md) | [目录](../README.md)

---

## 本课目标

学完这节课，你能回答：

1. ReAct 模式是什么？它和普通 Function Calling 有什么区别？
2. OpenClaw 中 ReAct 循环的具体实现是怎样的？
3. 一轮 Agent 运行的 6 个完整阶段分别做了什么？
4. 工具调用的完整流程是怎样的？包括不同 LLM Provider 的 Schema 差异处理？
5. ReAct 循环什么时候停止？所有终止条件有哪些？

---

## 1. 回顾 ReAct 概念

### Reason + Act = ReAct

传统 LLM 只能 **说（生成文本）**，不能 **做（执行动作）**。ReAct 模式赋予了 LLM "思考-行动"的循环能力：

```
传统 LLM（只能"说"）:
  用户: "北京今天天气怎样？"
  LLM:  "抱歉，我无法获取实时天气信息，但通常3月底..."  ← 只能猜

ReAct Agent（能"想"也能"做"）:
  用户: "北京今天天气怎样？"
  
  Agent 思考: "用户问天气，我有 weather_api 工具"           ← Reason (推理)
  Agent 行动: 调用 weather_api({ city: "北京" })            ← Act    (行动)
  工具返回:   { "temp": 25, "condition": "晴", "wind": "微风" }
  Agent 思考: "拿到了准确数据，可以回复用户了"               ← Reason (推理)
  Agent 回复: "北京今天晴天，气温 25°C，微风，适合出门！"    ← Act    (输出)
```

### ReAct 的核心循环

```
         ┌──────────────────┐
         │                  │
         ▼                  │
    ┌──────────┐      ┌──────────┐
    │  Reason  │─────▶│   Act    │
    │  (推理)  │      │  (行动)  │
    │          │      │          │
    │ "我需要  │      │ 调用工具 │
    │  做什么？"│      │ 或回复  │
    └──────────┘      └────┬─────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  需要继续？   │
                    └──────┬───────┘
                      ┌────┴────┐
                      │         │
                    Yes        No
                      │         │
                      ▼         ▼
                 回到 Reason  输出最终回复
                               ▲
                               │
                          循环结束！
```

### ReAct vs 普通 Function Calling

| 维度 | 普通 Function Calling | ReAct 模式 |
|------|----------------------|------------|
| 调用次数 | 单次调用 | 多轮循环 |
| 决策能力 | LLM 一次决定调用哪个函数 | LLM 根据上一步结果决定下一步 |
| 复杂任务 | 不擅长（只能调一次） | 擅长（可以分步完成） |
| 信息依赖 | 无（一步完成） | 有（后一步依赖前一步的结果） |
| 类比 | 计算器（按一下出结果） | 人类解题（一步步推导） |

**关键区别**：Function Calling 是"一次性"的——LLM 调一个函数就直接回答。ReAct 是"多轮迭代"的——LLM 可以调完一个工具后思考，再调另一个工具，直到任务完成。

> **一句话理解**：ReAct 就是让 AI 像人一样——先想清楚要做什么，做完看看结果，再决定下一步。不断循环直到问题解决。

---

## 2. OpenClaw 中 ReAct 循环的实现

在 OpenClaw 中，ReAct 循环不是一个抽象概念，而是 Agent Runner 中 **真实运行的代码逻辑**。

### 一轮 Agent 运行的完整 6 个阶段

```
┌──────────────────────────────────────────────────────────────────┐
│                     一轮 Agent 运行                                │
│                                                                  │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐               │
│   │ ① 组装    │    │ ② 加载    │    │ ③ 检查    │               │
│   │ System    │───▶│ Memory    │───▶│ Context   │               │
│   │ Prompt    │    │           │    │ Window    │               │
│   │           │    │ 会话历史  │    │           │               │
│   │ SOUL.md   │    │ MEMORY.md │    │ Token计数 │               │
│   │ AGENTS.md │    │ USER.md   │    │ 溢出检查  │               │
│   │ 工具定义  │    │ daily.md  │    │ Compaction│               │
│   └───────────┘    └───────────┘    └─────┬─────┘               │
│                                           │                      │
│                                           ▼                      │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐               │
│   │ ⑥ 流式    │    │ ⑤ 工具    │    │ ④ LLM     │               │
│   │ 回复推送  │◀───│ 执行      │◀──▶│ 调用      │               │
│   │           │    │           │    │           │               │
│   │ WebSocket │    │ 调用 API  │    │ GPT-4 /   │               │
│   │ → Channel │    │ 读取文件  │    │ Claude /  │               │
│   │ → 用户    │    │ 执行代码  │    │ Gemini    │               │
│   └───────────┘    └─────┬─────┘    └───────────┘               │
│                          │ ▲                                     │
│                          │ │     工具调用循环                     │
│                          └─┘     (ReAct 核心)                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

### 阶段 ①：组装 System Prompt

System Prompt 是 Agent 的"大脑操作系统"，决定了它的行为模式、人格特征和能力边界。

```typescript
function assembleSystemPrompt(agent: AgentDefinition): string {
  const parts: string[] = [];

  // 1. SOUL.md — Agent 的核心人格与指令
  //    "你是一个友善的编程助手，擅长 TypeScript 和 React..."
  parts.push(loadFile(agent.soulPath));

  // 2. AGENTS.md — 操作手册与行为规范
  //    "当用户问代码问题时，先理解需求再给代码..."
  parts.push(loadFile(agent.agentsPath));

  // 3. 工具定义 — 告诉 LLM 有哪些工具可用
  //    每个工具的名称、描述、参数 Schema
  parts.push(formatToolSchemas(agent.tools));

  // 4. 运行时上下文 — 动态注入的信息
  //    当前时间、用户名、会话 ID 等
  parts.push(formatRuntimeContext({
    currentTime: new Date().toISOString(),
    userName: session.userName,
    timezone: session.timezone,
  }));

  return parts.join("\n\n---\n\n");
}
```

组装后的 System Prompt 结构示意：

```
┌─────────────────────────────────────────┐
│  System Prompt (~3,000-5,000 tokens)    │
│                                         │
│  ┌─── SOUL.md ─────────────────────┐   │
│  │ 你是 CodeBot，一个编程助手...     │   │
│  │ 你的风格是简洁、友善、实用...     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─── AGENTS.md ───────────────────┐   │
│  │ 回答代码问题时：先理解→再编码    │   │
│  │ 遇到不确定的：说"我不确定"       │   │
│  │ 敏感操作前：先确认用户意图       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─── Tool Schemas ────────────────┐   │
│  │ weather_api: 查询天气           │   │
│  │ web_search: 网络搜索            │   │
│  │ read_file: 读取文件             │   │
│  │ execute_code: 执行代码          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─── Runtime Context ─────────────┐   │
│  │ 当前时间: 2026-03-27 10:30 CST  │   │
│  │ 用户: Alice                     │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### 阶段 ②：加载 Memory

Memory 加载有严格的优先级——确保最重要的信息最先加载：

```
Memory 加载优先级（从高到低）:

  优先级 1: 会话历史（当前对话的所有消息）
            → 这是 Agent 理解"我们正在聊什么"的基础
            → 不加载就等于 Agent 失忆了
            
  优先级 2: MEMORY.md（持久化记忆）
            → 跨会话的重要信息（"用户喜欢简洁的回答"）
            → 让 Agent 记住上次对话的关键信息
            
  优先级 3: memory/YYYY-MM-DD.md（当日工作记忆）
            → 今天做过什么、讨论过什么
            → 避免重复工作
            
  优先级 4: USER.md（用户偏好）
            → 编程语言偏好、回复风格等
            → 个性化体验
```

### 阶段 ③：检查 Context Window

在发送给 LLM 之前，必须确保所有内容不超过上下文窗口限制（下节课详讲）：

```
Token 预算计算:

  总 Token = System Prompt + Memory + 对话历史 + 工具定义 + 新消息
  
  if (总 Token > 模型上限 × 安全系数 0.8) {
      触发 Compaction:
        1. 截断超大工具结果
        2. 压缩早期对话为摘要
        3. 必要时使用滑动窗口
  }
  
  if (Compaction 后仍超限) {
      return { status: "final", reason: "context_overflow" }
  }
```

### 阶段 ④：调用 LLM

把组装好的 messages 数组发送给 LLM Provider（GPT-4、Claude、Gemini 等），流式接收响应。

### 阶段 ⑤：工具执行（ReAct 循环的核心）

如果 LLM 不直接回复，而是要求调用工具——这里就进入了 ReAct 循环。

### 阶段 ⑥：流式回复

当 LLM 输出最终文本时，通过 WebSocket 逐 token 推送给用户，实现"打字机效果"。

---

## 3. 工具调用的详细流程

这是 ReAct 循环中最复杂的部分。

### 完整时序图

```
Agent Runner                          LLM API                           工具系统
    │                                   │                                  │
    │  ① 发送 messages[]               │                                  │
    │  (含 System Prompt + 历史        │                                  │
    │   + 工具 Schemas)                │                                  │
    │──────────────────────────────────▶│                                  │
    │                                   │                                  │
    │  ② LLM 返回: tool_call           │                                  │
    │  {                                │                                  │
    │    name: "weather_api",           │                                  │
    │    arguments: '{"city":"北京"}'   │                                  │
    │    id: "call_abc123"              │                                  │
    │  }                                │                                  │
    │◀──────────────────────────────────│                                  │
    │                                   │                                  │
    │  ③ 解析工具调用参数                                                  │
    │  ④ 执行工具                                                         │
    │──────────────────────────────────────────────────────────────────────▶│
    │                                                                      │
    │  ⑤ 工具返回结果                                                      │
    │  { "temp": 25, "condition": "晴", "humidity": "45%" }               │
    │◀─────────────────────────────────────────────────────────────────────│
    │                                   │                                  │
    │  ⑥ 将工具调用 + 结果追加到 messages[]                                │
    │  messages.push({ role: "assistant", tool_calls: [...] })             │
    │  messages.push({ role: "tool", tool_call_id: "call_abc123",          │
    │                  content: '{"temp":25,...}' })                        │
    │                                   │                                  │
    │  ⑦ 再次发送 messages[] 给 LLM    │                                  │
    │──────────────────────────────────▶│                                  │
    │                                   │                                  │
    │  ⑧ LLM 返回: 纯文本回复          │                                  │
    │  "北京今天晴天，气温25°C，        │                                  │
    │   湿度45%，适合出门！"            │                                  │
    │◀──────────────────────────────────│                                  │
    │                                   │                                  │
    │  ⑨ 流式推送给用户                                                    │
    ▼                                   ▼                                  ▼
```

### Tool Schema 定义

LLM 需要知道有哪些工具可用、每个工具接受什么参数。这通过 Tool Schema 描述：

```typescript
const weatherTool: ToolDefinition = {
  name: "weather_api",
  description: "查询指定城市的当前天气信息，包括温度、天气状况、湿度等",
  parameters: {
    type: "object",
    properties: {
      city: {
        type: "string",
        description: "城市名称，如 '北京'、'上海'、'New York'"
      },
      unit: {
        type: "string",
        enum: ["celsius", "fahrenheit"],
        description: "温度单位，默认 celsius"
      }
    },
    required: ["city"]
  }
};
```

> Tool Schema 的质量直接影响 LLM 调用工具的准确性。`description` 写得越清楚，LLM 越容易正确使用工具。

### 不同 LLM Provider 的 Schema 差异

这是一个容易忽略但工程上非常重要的细节——三大 Provider 的 Tool Schema 格式互不兼容：

```
┌────────────────────────────────────────────────────────────┐
│  OpenAI (GPT-4)                                            │
│                                                            │
│  tools: [{                                                 │
│    type: "function",              ← 需要 type 字段         │
│    function: {                    ← 嵌套在 function 对象中  │
│      name: "weather_api",                                  │
│      description: "查询天气",                               │
│      parameters: { ... }          ← 字段名: "parameters"   │
│    }                                                       │
│  }]                                                        │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  Anthropic (Claude)                                        │
│                                                            │
│  tools: [{                                                 │
│    name: "weather_api",           ← 扁平结构，没有嵌套     │
│    description: "查询天气",                                 │
│    input_schema: { ... }          ← 字段名: "input_schema" │
│  }]                               ← 不是 "parameters"！    │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  Google (Gemini)                                           │
│                                                            │
│  tools: [{                                                 │
│    functionDeclarations: [{       ← 嵌套在                 │
│      name: "weather_api",         ← functionDeclarations 里│
│      description: "查询天气",                               │
│      parameters: { ... }          ← 字段名: "parameters"   │
│    }]                                                      │
│  }]                                                        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### OpenClaw 的适配层解决方案

```
OpenClaw 内部统一格式:
  { name, description, parameters }
           │
           ▼
  ┌──────────────────────┐
  │  Provider Adapter     │  ← 适配器模式 (Adapter Pattern)
  │                      │
  │  toOpenAI(tool)      │  → { type: "function", function: { ... } }
  │  toAnthropic(tool)   │  → { name, input_schema: { ... } }
  │  toGoogle(tool)      │  → { functionDeclarations: [{ ... }] }
  │                      │
  │  fromOpenAI(resp)    │  → 统一的 ToolCallResult
  │  fromAnthropic(resp) │  → 统一的 ToolCallResult
  │  fromGoogle(resp)    │  → 统一的 ToolCallResult
  └──────────────────────┘
```

```typescript
// 适配器示例（简化）
function convertToolSchema(tool: ToolDefinition, provider: string) {
  switch (provider) {
    case "openai":
      return {
        type: "function",
        function: {
          name: tool.name,
          description: tool.description,
          parameters: tool.parameters,
        },
      };
      
    case "anthropic":
      return {
        name: tool.name,
        description: tool.description,
        input_schema: tool.parameters,  // parameters → input_schema
      };
      
    case "google":
      return {
        functionDeclarations: [{
          name: tool.name,
          description: tool.description,
          parameters: tool.parameters,
        }],
      };
  }
}
```

> **面试考点**：这是 **适配器模式（Adapter Pattern）** 的经典应用。新增 Provider 时只需写一个新的适配器，不需要修改 Agent Runner 的核心逻辑——这是开闭原则（OCP）的体现。

---

## 4. 用具体例子走一遍完整的 ReAct 循环

### 场景：用户问 "帮我搜索关于 React 19 的最新文章，总结前三篇"

这个任务需要多步才能完成——搜索 → 读取 → 总结。

```
╔══════════════════════════════════════════════════════════════╗
║  循环第 1 轮                                                  ║
║                                                              ║
║  ── messages[] 发送给 LLM ──                                 ║
║  [System Prompt, User: "搜索React19文章，总结前三篇"]        ║
║                                                              ║
║  [Reason] LLM 思考:                                         ║
║    "用户要搜索文章并总结。我需要先搜索，再读内容，最后总结。  ║
║     第一步：用 web_search 工具搜索 React 19 相关文章。"      ║
║                                                              ║
║  [Act] LLM 输出:                                            ║
║    tool_call: web_search({ query: "React 19 最新文章 2026" })║
║                                                              ║
║  [执行] web_search 工具被调用，返回:                         ║
║    [                                                         ║
║      { title: "React 19 新特性全解析", url: "https://a..." },║
║      { title: "React 19 性能优化实战", url: "https://b..." },║
║      { title: "React 19 迁移指南",     url: "https://c..." },║
║      { title: "...(更多结果)..." }                           ║
║    ]                                                         ║
║                                                              ║
║  → 工具结果追加到 messages[]                                  ║
╚══════════════════════════════════════════════════════════════╝
         │
         ▼ messages[] 增长了，继续循环

╔══════════════════════════════════════════════════════════════╗
║  循环第 2 轮                                                  ║
║                                                              ║
║  ── messages[] 发送给 LLM ──                                 ║
║  [System Prompt, User消息, 搜索工具调用, 搜索结果]           ║
║                                                              ║
║  [Reason] LLM 思考:                                         ║
║    "搜索结果拿到了，有3篇文章标题和URL。                      ║
║     我需要读取每篇文章的内容才能总结。先读第一篇。"          ║
║                                                              ║
║  [Act] LLM 输出:                                            ║
║    tool_call: read_url({ url: "https://a..." })              ║
║                                                              ║
║  [执行] read_url 返回第一篇文章内容 (~5000 tokens)           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
         │
         ▼

╔══════════════════════════════════════════════════════════════╗
║  循环第 3 轮                                                  ║
║                                                              ║
║  [Reason] "第一篇读完了，继续读第二篇"                       ║
║  [Act] tool_call: read_url({ url: "https://b..." })          ║
║  [执行] 返回第二篇文章内容                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
         │
         ▼

╔══════════════════════════════════════════════════════════════╗
║  循环第 4 轮                                                  ║
║                                                              ║
║  [Reason] "第二篇也读完了，读第三篇"                         ║
║  [Act] tool_call: read_url({ url: "https://c..." })          ║
║  [执行] 返回第三篇文章内容                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
         │
         ▼

╔══════════════════════════════════════════════════════════════╗
║  循环第 5 轮 — 最终轮                                         ║
║                                                              ║
║  ── messages[] 此时已经非常长 ──                              ║
║  [System Prompt, User消息, 搜索调用, 搜索结果,               ║
║   读取调用1, 文章1, 读取调用2, 文章2, 读取调用3, 文章3]      ║
║                                                              ║
║  [Reason] LLM 思考:                                         ║
║    "三篇文章都读完了，信息充足，可以总结了。"                 ║
║                                                              ║
║  [Act] LLM 输出 纯文本（无 tool_call）:                      ║
║    "以下是 React 19 最新三篇文章的总结：                      ║
║                                                              ║
║     1. 《React 19 新特性全解析》                              ║
║        React 19 引入了全新的编译器（React Compiler），        ║
║        自动优化组件重渲染...                                  ║
║                                                              ║
║     2. 《React 19 性能优化实战》                              ║
║        通过 use() Hook 和 Server Components，                ║
║        页面加载速度提升 40%...                                ║
║                                                              ║
║     3. 《React 19 迁移指南》                                  ║
║        从 React 18 升级需要注意..."                           ║
║                                                              ║
║  → 没有 tool_call → 循环结束！                                ║
║  → 回复流式推送给用户                                         ║
║  → return { status: "success", response: "..." }             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### 这个例子中 Context 的增长

```
Token 消耗追踪:

  初始:  System Prompt(3K) + User消息(50) = ~3,050 tokens
  
  第1轮: + 搜索调用(100) + 搜索结果(2K) = ~5,150 tokens
  第2轮: + 读取调用(100) + 文章1(5K)    = ~10,250 tokens
  第3轮: + 读取调用(100) + 文章2(5K)    = ~15,350 tokens
  第4轮: + 读取调用(100) + 文章3(5K)    = ~20,450 tokens
  第5轮: + 最终回复(500)                 = ~20,950 tokens
  
  5 轮循环，Context 从 3K 增长到 21K tokens
  如果文章更长或需要更多搜索，很容易突破 100K！
```

> 这就是为什么 Context Window 管理如此重要——下节课会详细讲。

---

## 5. 循环什么时候停止？终止条件完整分析

ReAct 循环不会无限运行。以下是所有终止条件：

### 正常终止（Happy Path）

| 条件 | 触发方式 | 说明 |
|------|---------|------|
| LLM 输出纯文本 | `response.toolCalls` 为空 | 最常见——LLM 认为任务完成，给出最终回复 |
| LLM 输出 stop token | `finish_reason: "stop"` | 模型显式发出停止信号 |

### 异常终止（Safety Mechanisms）

| 条件 | 触发方式 | 说明 |
|------|---------|------|
| 达到最大循环次数 | `iteration >= maxIterations` | 防止无限循环，通常设为 10-20 轮 |
| Context Window 溢出 | Token 计数超限 | 工具返回太多内容，Context 装不下 |
| LLM API 报错且重试耗尽 | 连续 N 次调用失败 | 模型服务不可用 |
| 工具执行超时 | 单个工具执行 > 超时阈值 | 某个工具卡住了 |
| 防护标志触发 | 三个重试标志之一为 true | 上节课讲的防护机制 |

### 终止判断流程

```
LLM 返回响应
     │
     ├── 响应包含 tool_call？
     │     │
     │     ├── 是 → 执行工具
     │     │         │
     │     │         ▼
     │     │    检查终止条件:
     │     │         │
     │     │         ├── 循环次数 >= 最大值？
     │     │         │     │
     │     │         │     ├── 是 → 终止 (status: "final", reason: "max_iterations")
     │     │         │     └── 否 ↓
     │     │         │
     │     │         ├── Context 溢出？
     │     │         │     │
     │     │         │     ├── 是 → 尝试 Compaction → 仍超限？→ 终止
     │     │         │     └── 否 ↓
     │     │         │
     │     │         └── 所有检查通过 → 继续下一轮循环 🔄
     │     │
     │     └── 否（纯文本回复）
     │           │
     │           └── 循环正常结束 ✅ (status: "success")
     │
     └── 响应报错？
           │
           ├── 可重试的错误？ → Fallback / 重试
           └── 不可重试？ → 终止 (status: "final", reason: "llm_error")
```

### 最大循环次数：安全阀设计

```
为什么需要最大循环次数？

  假设一个"失控"的 Agent：
    用户: "帮我收集所有相关信息"
    Agent: search("React") → 结果太多 → search("React 2026") → 
           read(url1) → read(url2) → read(url3) → search("更多") →
           read(url4) → ... 永远不停下来！

  每轮循环的成本：
    • LLM API 调用 ~$0.03-0.10
    • 时间 ~3-10 秒
    • Context 持续膨胀

  没有最大次数限制：
    • 50 轮 = $1.50-5.00 + 3-8 分钟 + Context 爆炸
    • 用户等到天荒地老

  设为 15 轮：
    • 足以完成 95% 的正常任务
    • 限制最大成本 ~$0.45-1.50
    • 限制最大等待时间 ~45-150 秒
```

> **面试考点**：最大循环次数是一个关键的安全阀。它平衡了"任务完成度"和"资源控制"——太小会导致复杂任务无法完成，太大会导致费用失控和用户等待过长。

---

## 6. ReAct 循环的代码骨架

```typescript
async function reactLoop(
  messages: Message[],
  tools: ToolDefinition[],
  provider: LLMProvider,
  options: {
    maxIterations?: number;
    onStreamToken?: (token: string) => void;
  }
): Promise<AgentRunLoopResult> {
  
  const maxIter = options.maxIterations ?? 15;

  for (let i = 0; i < maxIter; i++) {
    
    // ── Step 1: 调用 LLM ──
    const response = await provider.chat({
      messages,
      tools: tools.map(t => convertToolSchema(t, provider.name)),
      stream: true,
    });

    // ── Step 2: 流式输出（如果是纯文本）──
    if (!response.toolCalls || response.toolCalls.length === 0) {
      for await (const token of response.stream) {
        options.onStreamToken?.(token);
      }
      return { 
        status: "success", 
        response: response.content,
        tokenUsage: response.usage,
      };
    }

    // ── Step 3: 执行工具调用 ──
    messages.push({
      role: "assistant",
      toolCalls: response.toolCalls,
    });

    for (const toolCall of response.toolCalls) {
      const result = await executeTool(toolCall.name, toolCall.arguments);

      messages.push({
        role: "tool",
        toolCallId: toolCall.id,
        content: typeof result === "string" ? result : JSON.stringify(result),
      });
    }

    // ── Step 4: 检查 Context Window ──
    if (isContextNearOverflow(messages, provider.maxTokens)) {
      const compacted = await compactMessages(messages);
      if (!compacted) {
        return { status: "final", reason: "context_overflow" };
      }
      messages = compacted;
    }
  }

  // ── 达到最大循环次数 ──
  return { status: "final", reason: "max_iterations" };
}
```

### 并行工具调用

注意上面代码中 `response.toolCalls` 是一个 **数组**——LLM 可以一次请求调用多个工具：

```
单次调用:
  LLM: "我需要查天气"
  → tool_call: weather_api("北京")
  → 1 次工具执行

并行调用（LLM 一次返回多个 tool_call）:
  LLM: "我需要同时查天气和股票"
  → tool_calls: [
      weather_api("北京"),
      stock_api("AAPL")
    ]
  → 2 次工具执行（可以并行）

这可以减少 ReAct 循环的轮数，提高效率。
```

---

## 7. 面试考点

> **高频题 1**：请解释 ReAct 模式和普通 Function Calling 有什么区别？
>
> **参考思路**：Function Calling 是单次的——LLM 调一个函数，拿到结果，直接回复。ReAct 是 **多轮循环** 的——LLM 可以根据上一步工具的结果，思考并决定是否需要调更多工具。核心区别在于 **决策链路**：Function Calling 是"一步到位"，ReAct 是"逐步推进"。这让 Agent 能处理复杂的多步骤任务（如"搜索-阅读-总结"），而不仅仅是"一问一答"。

> **高频题 2**：不同 LLM Provider 的 Tool Schema 格式不同，OpenClaw 怎么处理？
>
> **参考思路**：OpenClaw 内部维护一套统一的 Tool Schema 格式。在实际调用时，有一个 **Provider 适配层**，负责将统一格式转换为各 Provider 的特定格式（OpenAI 用 `parameters`，Anthropic 用 `input_schema`，Google 嵌套在 `functionDeclarations` 里）。反向也一样——各 Provider 返回的工具调用结果也通过适配层转换为统一格式。这是 **适配器模式（Adapter Pattern）** 的典型应用，遵循开闭原则——新增 Provider 只需写一个适配器。

> **高频题 3**：ReAct 循环可能出现哪些问题？如何防范？
>
> **参考思路**：三大问题：① **无限循环**——Agent 不断调工具但从不给最终回复 → 用最大循环次数限制；② **Context 爆炸**——工具返回大量数据，多轮循环后 Context 撑爆 → 每轮循环后检查 Context 大小 + Compaction；③ **费用失控**——每轮循环消耗一次 LLM API 调用 → 预算控制 + 最大循环次数 + 重试限制。这三个问题互相关联——无限循环既导致 Context 爆炸，也导致费用失控。

> **进阶题**：如果 LLM 在 ReAct 循环中反复调用同一个工具且参数相同，你怎么处理？
>
> **参考思路**：这是"Agent 卡在循环中"的典型症状。可以实现 **循环检测**：记录每轮的工具调用，如果连续 N 次（如 3 次）相同的 tool + args 组合，强制终止循环并向用户反馈。也可以将上一次的工具结果作为提示注入，告诉 LLM"你已经调用过这个工具了，结果是..."。

---

## 8. 课后练习

### 练习 1：手动模拟 ReAct

选择任务"帮我比较 React 和 Vue 的 2026 年最新版本"，手动在纸上模拟 ReAct 循环的每一轮：
- 明确写出 LLM 的 [Reason] 思考过程
- 写出 [Act] 工具调用（名称 + 参数）
- 写出工具返回结果（模拟数据即可）
- 估算每轮的 Token 增长量
- 记录需要多少轮才能完成任务

### 练习 2：终止条件设计

如果你要设计一个 ReAct 循环的终止条件系统，除了课上讲的这些，你还能想到哪些情况需要终止？

提示方向：
- 用户主动取消
- 敏感操作检测
- 费用超出预算
- 工具调用模式异常

每种情况应该如何检测？返回什么样的 status 和 reason？

### 练习 3：Provider 适配

写出将以下统一 Tool Schema 分别转换为 OpenAI、Anthropic、Google 三种格式的 TypeScript 代码：

```typescript
const tool = {
  name: "calculate",
  description: "执行数学计算，支持加减乘除和常见数学函数",
  parameters: {
    type: "object",
    properties: {
      expression: { type: "string", description: "数学表达式，如 '2 * (3 + 4)'" },
      precision: { type: "number", description: "小数精度，默认2位" }
    },
    required: ["expression"]
  }
};
```

额外挑战：同时写出反向转换——将各 Provider 的工具调用响应转换为统一格式。

---

> [上一课 ← 07-agent-runner](./07-agent-runner.md) | [下一课 → 09-context-window](./09-context-window.md) | [回到目录](../README.md)
