# 系统设计题：如何设计一个 Agent 系统

> **第四阶段 · 面试冲刺** | 第18课

**导航**：[上一课 ←](./17-source-code-tour.md) | [下一课 →](./19-resume-guide.md)

---

## 本课目标

- 理解面试中系统设计题的考察目标和答题框架
- 掌握"设计一个类似 OpenClaw 的 Agent 系统"的标准答案
- 学会从需求分析到监控观测的全链路系统设计
- 画出面试可用的完整架构图

---

## 一、面试中的系统设计题

### 1.1 考察目标

系统设计题不是考你背答案，而是考察：

| 维度 | 考察内容 | 权重 |
|------|---------|------|
| **需求分析能力** | 能否主动澄清需求、区分功能性/非功能性需求 | 20% |
| **架构设计能力** | 模块划分是否合理、组件间耦合度是否低 | 30% |
| **技术深度** | 关键模块能否深入讲解实现细节 | 25% |
| **权衡取舍** | 能否说明设计中的 trade-off | 15% |
| **工程素养** | 是否考虑了监控、安全、扩展性 | 10% |

### 1.2 标准答题框架（5 步法）

```
Step 1：需求澄清（2-3 分钟）
  → 确认功能边界、用户规模、性能要求

Step 2：高层架构（3-5 分钟）
  → 画出核心组件和数据流

Step 3：核心模块深入（10-15 分钟）
  → 挑 2-3 个最关键的模块详细设计

Step 4：扩展性与可靠性（3-5 分钟）
  → 高可用、水平扩展、降级策略

Step 5：总结与 trade-off（2-3 分钟）
  → 方案优缺点、未来演进方向
```

> **面试考点**：系统设计题的第一步永远是"需求澄清"。直接跳到画架构图是最常见的减分行为。先问清楚"这个系统要服务多少用户？要支持哪些渠道？对响应时间有什么要求？"展示你的工程素养。

---

## 二、需求分析

### 2.1 功能性需求（Functional Requirements）

当面试官说"设计一个类似 OpenClaw 的 Agent 系统"，你应该主动确认以下需求：

```
必须支持的核心功能：
  ✅ 接收用户自然语言输入，返回智能回复
  ✅ 支持 Tool Calling（工具调用）
  ✅ 支持多轮对话，维护上下文
  ✅ 支持多渠道接入（Web、微信、Slack 等）
  ✅ 支持自定义 System Prompt
  ✅ 支持 Skill/Plugin 扩展

可选的进阶功能（可以和面试官确认）：
  ❓ 是否需要多 Agent 协同？
  ❓ 是否需要长期记忆（跨会话）？
  ❓ 是否需要支持流式输出（Streaming）？
  ❓ 是否需要支持语音/图片等多模态？
```

### 2.2 非功能性需求（Non-Functional Requirements）

```
性能要求：
  - 首 token 延迟 < 2 秒
  - 端到端响应时间 < 30 秒（含工具调用）
  - 支持 10,000+ 并发会话

可用性要求：
  - SLA 99.9%（月停机时间 < 43 分钟）
  - 单组件故障不影响整体服务

安全要求：
  - 数据加密（传输中 + 静态）
  - 工具调用权限控制
  - 全链路审计日志

扩展性要求：
  - 水平扩展（加机器即可扩容）
  - 插件化架构（新增渠道/工具无需改核心代码）
```

---

## 三、架构设计

### 3.1 完整架构图（ASCII Art）

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                │
│                                                                     │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│   │   Web    │  │  微信     │  │  Slack   │  │  API     │          │
│   │  Client  │  │  Client  │  │  Client  │  │  Client  │          │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│        │              │             │              │                │
└────────┼──────────────┼─────────────┼──────────────┼────────────────┘
         │              │             │              │
         ▼              ▼             ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Gateway Layer (网关层)                           │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │                   Load Balancer (负载均衡)                │      │
│   └───────────────────────┬─────────────────────────────────┘      │
│                           │                                         │
│   ┌───────────────────────▼─────────────────────────────────┐      │
│   │              Gateway Server (网关服务器)                   │      │
│   │                                                         │      │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │      │
│   │  │   Auth   │  │  Rate    │  │  Channel │             │      │
│   │  │Middleware│  │ Limiter  │  │ Adapter  │             │      │
│   │  └──────────┘  └──────────┘  └──────────┘             │      │
│   │                                                         │      │
│   │  ┌──────────────────────────────────────┐              │      │
│   │  │     WebSocket Manager                 │              │      │
│   │  │  (双向实时通信 / 连接管理 / 心跳)      │              │      │
│   │  └──────────────────────────────────────┘              │      │
│   │                                                         │      │
│   │  ┌──────────────────────────────────────┐              │      │
│   │  │     Lane Manager (消息队列管理)       │              │      │
│   │  │  Session A: [msg1] → [msg2] → ...    │              │      │
│   │  │  Session B: [msg1] → ...             │              │      │
│   │  │  Session C: [msg1] → [msg2] → ...    │              │      │
│   │  └──────────────────────────────────────┘              │      │
│   └─────────────────────────────────────────────────────────┘      │
│                                                                     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Agent Layer (Agent 执行层)                        │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │                 Agent Runner (Agent 执行器)               │      │
│   │                                                         │      │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │      │
│   │  │  Context     │  │    LLM      │  │   Skill     │    │      │
│   │  │  Engine      │  │  Connector  │  │  Executor   │    │      │
│   │  │ (上下文引擎) │  │ (模型连接器) │  │ (技能执行器) │    │      │
│   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │      │
│   │         │                │                │            │      │
│   │         ▼                ▼                ▼            │      │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │      │
│   │  │  Compaction  │  │  Streaming  │  │   Policy    │    │      │
│   │  │  Strategy   │  │  Handler    │  │  Pipeline   │    │      │
│   │  │ (压缩策略)   │  │ (流式处理)  │  │ (策略管道)   │    │      │
│   │  └─────────────┘  └─────────────┘  └─────────────┘    │      │
│   │                                                         │      │
│   │  ┌──────────────────────────────────────┐              │      │
│   │  │           Hook Manager                │              │      │
│   │  │  before-reply / after-reply           │              │      │
│   │  │  before-tool-call / after-tool-call   │              │      │
│   │  └──────────────────────────────────────┘              │      │
│   └─────────────────────────────────────────────────────────┘      │
│                                                                     │
└────────┬─────────────────────────────┬──────────────────────────────┘
         │                             │
         ▼                             ▼
┌────────────────────┐    ┌────────────────────────────────────────────┐
│   Storage Layer    │    │          External Services                  │
│   (存储层)         │    │          (外部服务)                          │
│                    │    │                                              │
│  ┌──────────────┐  │    │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  短期记忆     │  │    │  │  LLM API │  │  第三方   │  │  监控     │ │
│  │  (Redis)     │  │    │  │ (OpenAI/ │  │  Tool    │  │  告警     │ │
│  ├──────────────┤  │    │  │ Claude..)│  │  APIs    │  │  系统     │ │
│  │  长期记忆     │  │    │  └──────────┘  └──────────┘  └──────────┘ │
│  │  (PostgreSQL)│  │    │                                              │
│  ├──────────────┤  │    └────────────────────────────────────────────┘
│  │  会话存储     │  │
│  │  (Redis)     │  │
│  ├──────────────┤  │
│  │  审计日志     │  │
│  │  (ES/ClickH) │  │
│  └──────────────┘  │
│                    │
└────────────────────┘
```

### 3.2 数据流概览

```
用户消息的完整流转路径：

Client → Load Balancer → Gateway → Auth → Rate Limit → Channel Adapt
  → WebSocket Manager → Lane Manager → Agent Runner → Context Engine
  → LLM Call → [Tool Call → Skill Executor → Tool Result]*
  → Response → WebSocket → Client

其中 [...]* 表示 Tool Calling 循环可能执行 0~N 次
```

---

## 四、核心模块设计

### 4.1 消息队列设计：Lane-based vs 普通消息队列

**为什么不用 Kafka / RabbitMQ？**

| 维度 | 普通消息队列 | Lane-based 设计 |
|------|------------|----------------|
| 隔离粒度 | Topic/Queue 级别 | Session 级别 |
| 顺序保证 | Partition 内有序 | 天然按会话有序 |
| 上下文关联 | 无，需额外管理 | Lane 直接持有 Context |
| 背压控制 | 全局限流 | 单 Lane 阻塞不影响其他 |
| 实现复杂度 | 依赖外部组件 | 内存实现，低延迟 |
| 适用规模 | 大规模分布式 | 中等规模，单机或小集群 |

```typescript
// Lane-based 消息队列核心设计
interface Lane {
  sessionId: string;
  queue: Message[];          // 消息队列
  context: AgentContext;     // 持有上下文引用
  isProcessing: boolean;     // 处理状态
  createdAt: number;
  lastActiveAt: number;

  push(message: Message): void;
  shift(): Message | undefined;
  isEmpty(): boolean;
}

interface LaneManager {
  // 核心 API
  enqueue(sessionId: string, message: Message): Promise<void>;
  getLane(sessionId: string): Lane | undefined;
  destroyLane(sessionId: string): void;

  // 监控
  getActiveLaneCount(): number;
  getLaneStats(): LaneStats;

  // 生命周期管理
  cleanupIdleLanes(maxIdleMs: number): void;
}
```

**面试加分话术**：
> "Lane-based 设计的核心优势在于会话级别的隔离和上下文关联。在 Agent 场景中，消息的处理强依赖上下文状态，用传统消息队列需要额外的状态管理层，而 Lane 将队列和上下文天然绑定，简化了架构。当然 trade-off 是不适合超大规模分布式场景，此时可以考虑每个节点跑一个 LaneManager，外层加一层 Session 路由。"

### 4.2 上下文管理方案设计

```typescript
// 上下文管理的核心挑战：
// 1. 上下文窗口有限（如 128K tokens）
// 2. 对话越长，上下文越大
// 3. 需要在"保留足够信息"和"不超过窗口"之间平衡

interface ContextManager {
  // 构建上下文：将各种来源的信息组装成 LLM 可接受的格式
  buildContext(params: {
    systemPrompt: string;
    conversationHistory: Message[];
    shortTermMemory: MemoryEntry[];
    longTermMemory: MemoryEntry[];
    availableTools: ToolDefinition[];
    maxTokens: number;
  }): BuiltContext;

  // 压缩策略
  compact(context: BuiltContext, targetReduction: number): BuiltContext;
}

// 三级压缩策略
enum CompactionLevel {
  LIGHT = 'light',     // 轻度：移除重复信息、压缩工具结果
  MEDIUM = 'medium',   // 中度：摘要早期对话轮次
  HEAVY = 'heavy',     // 重度：只保留最近 N 轮 + 关键摘要
}

function selectCompactionStrategy(
  overflowAmount: number,
  totalTokens: number
): CompactionLevel {
  const overflowRatio = overflowAmount / totalTokens;

  if (overflowRatio < 0.1) return CompactionLevel.LIGHT;
  if (overflowRatio < 0.3) return CompactionLevel.MEDIUM;
  return CompactionLevel.HEAVY;
}
```

### 4.3 多渠道适配方案

```typescript
// 渠道适配器接口（策略模式）
interface ChannelAdapter {
  // 渠道标识
  readonly channelId: string;

  // 入站：将渠道特定格式转为统一格式
  normalizeInbound(rawMessage: unknown): NormalizedMessage;

  // 出站：将统一格式转为渠道特定格式
  formatOutbound(response: AgentResponse): unknown;

  // 连接管理
  connect(config: ChannelConfig): Promise<void>;
  disconnect(): Promise<void>;

  // 能力声明：该渠道支持哪些特性
  capabilities(): ChannelCapabilities;
}

interface ChannelCapabilities {
  supportsStreaming: boolean;   // 是否支持流式输出
  supportsRichMedia: boolean;   // 是否支持富媒体
  supportsButtons: boolean;     // 是否支持交互按钮
  maxMessageLength: number;     // 最大消息长度
}

// 使用示例
class WechatAdapter implements ChannelAdapter {
  readonly channelId = 'wechat';

  normalizeInbound(rawMessage: WechatMessage): NormalizedMessage {
    return {
      text: rawMessage.Content,
      userId: rawMessage.FromUserName,
      timestamp: rawMessage.CreateTime,
      metadata: { msgType: rawMessage.MsgType },
    };
  }

  formatOutbound(response: AgentResponse): WechatReply {
    // 微信单条消息最大 2048 字符，超长需要分割
    if (response.text.length > 2048) {
      return this.splitMessage(response.text);
    }
    return { Content: response.text, MsgType: 'text' };
  }

  capabilities(): ChannelCapabilities {
    return {
      supportsStreaming: false,  // 微信不支持流式
      supportsRichMedia: true,
      supportsButtons: true,
      maxMessageLength: 2048,
    };
  }
}
```

---

## 五、安全与权限设计

```typescript
// 分层安全架构
// Layer 1: 传输层安全
//   - TLS/SSL 加密
//   - WebSocket Secure (wss://)

// Layer 2: 认证层
//   - API Key / JWT Token
//   - OAuth2 集成

// Layer 3: 授权层
//   - 工具白名单（用户/会话级别）
//   - 参数约束规则
//   - 操作审批流程

// Layer 4: 运行时安全
//   - 提示词注入检测
//   - 输出内容过滤
//   - 敏感数据脱敏

// Layer 5: 审计层
//   - 全链路日志
//   - 行为分析
//   - 异常告警

interface SecurityConfig {
  authentication: {
    method: 'api_key' | 'jwt' | 'oauth2';
    tokenExpiry: number;
  };
  authorization: {
    toolWhitelist: Map<string, string[]>;  // userId → allowedTools
    parameterRules: ToolParameterRule[];
    requireApprovalFor: string[];
  };
  runtime: {
    enablePromptInjectionDetection: boolean;
    enableOutputFiltering: boolean;
    sensitiveDataPatterns: RegExp[];
  };
  audit: {
    logLevel: 'all' | 'tool_calls_only' | 'errors_only';
    retentionDays: number;
    alertRules: AlertRule[];
  };
}
```

---

## 六、高可用与扩展性

### 6.1 水平扩展方案

```
                    ┌─────────────────┐
                    │  DNS / CDN       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Load Balancer  │
                    │  (Nginx / ALB)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌────▼──────┐ ┌────▼──────┐
     │  Gateway #1   │ │Gateway #2 │ │Gateway #3 │
     │  (Lane: A,B)  │ │(Lane: C,D)│ │(Lane: E,F)│
     └────────┬──────┘ └────┬──────┘ └────┬──────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Session Router  │
                    │  (一致性哈希)     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        Agent Pool     Redis Cluster   PostgreSQL
        (可弹性伸缩)   (会话 + 记忆)    (持久化)
```

**关键设计决策**：

```
1. Session 亲和性（Sticky Session）
   - 同一会话的消息必须路由到持有其 Lane 的 Gateway
   - 实现方式：一致性哈希（基于 sessionId）
   - 失效转移：Redis 中备份 Lane 状态

2. Agent Runner 无状态化
   - Agent Runner 不持有状态，所有状态存储在 Redis
   - 可以随时启动新实例或关闭旧实例
   - 通过 K8s HPA 根据 CPU/请求量自动伸缩

3. 降级策略
   - LLM API 超时：切换到备用模型
   - Gateway 宕机：Session Router 重新分配
   - Redis 宕机：降级到本地内存缓存
```

### 6.2 容错设计

```typescript
// 断路器模式
class CircuitBreaker {
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private failureCount = 0;
  private lastFailureTime = 0;

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime > this.cooldownMs) {
        this.state = 'half-open';
      } else {
        throw new CircuitOpenError();
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    this.state = 'closed';
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    if (this.failureCount >= this.threshold) {
      this.state = 'open';
    }
  }
}
```

---

## 七、监控与可观测性

### 7.1 四大支柱

```
1. Metrics（指标）
   - 请求量 / QPS
   - 响应延迟（P50, P95, P99）
   - 错误率
   - Token 消耗量
   - 活跃会话数
   - Lane 队列深度

2. Logging（日志）
   - 结构化日志（JSON 格式）
   - 全链路 Trace ID 关联
   - 分级：INFO / WARN / ERROR

3. Tracing（链路追踪）
   - 从 Gateway 到 LLM API 的完整调用链
   - 每个 Skill 执行的耗时和结果
   - 上下文压缩的触发和效果

4. Alerting（告警）
   - 错误率突增
   - 响应时间劣化
   - Token 用量异常
   - 安全事件
```

### 7.2 核心监控大盘

```
┌─────────────────────────────────────────────────────────┐
│                  Agent System Dashboard                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  QPS: 1,234    Error Rate: 0.3%    Active Sessions: 892│
│                                                         │
│  ┌───────────────────┐  ┌───────────────────┐          │
│  │  Response Latency  │  │  Token Usage      │          │
│  │  P50: 1.2s        │  │  Today: 2.3M      │          │
│  │  P95: 4.8s        │  │  This hour: 120K  │          │
│  │  P99: 12.3s       │  │  Avg/req: 1,850   │          │
│  └───────────────────┘  └───────────────────┘          │
│                                                         │
│  ┌───────────────────┐  ┌───────────────────┐          │
│  │  Tool Call Stats   │  │  Context Overflow  │          │
│  │  Total: 3,456     │  │  Compaction: 89    │          │
│  │  Success: 98.2%   │  │  Truncation: 12    │          │
│  │  Avg time: 320ms  │  │  New session: 3    │          │
│  └───────────────────┘  └───────────────────┘          │
│                                                         │
│  Recent Alerts:                                         │
│  ⚠️  14:23  LLM API latency spike (P95 > 10s)          │
│  ✅  14:25  Auto-recovered: switched to fallback model  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

> **面试考点**：监控设计是系统设计题的"收官"部分。很多候选人会忘记这一块。主动提到四大支柱（Metrics, Logging, Tracing, Alerting）并给出具体指标，展示你不只是"设计系统"而是"运营系统"的思维。

---

## 八、面试实战：完整答题示范

**面试官**：请设计一个类似 OpenClaw 的 Agent 系统。

**参考回答（摘要版）**：

> 好的，在开始设计之前，我想先确认几个需求：这个系统预计服务多少并发用户？需要支持哪些接入渠道？对响应时间有什么要求？
>
> （假设面试官回答：1万并发，支持 Web 和微信，3秒内首 token 响应）
>
> 明白了。我的设计分为四层：
>
> **第一层是 Gateway 层**，负责多渠道接入和消息路由。核心组件包括 WebSocket Manager 管理长连接，Channel Adapter 做渠道格式统一化，以及 Lane Manager 做会话级消息队列。Lane 的设计是一个亮点——每个会话有独立的 Lane，天然保证消息顺序，并且 Lane 直接持有上下文引用，避免了额外的状态管理。
>
> **第二层是 Agent Layer**，核心是 Agent Runner 的执行循环。它的工作流程是：构建上下文 → 调用 LLM → 根据 LLM 响应决定是直接回复还是调用工具 → 如果调用工具则执行后将结果追加到上下文，继续循环。这里有一个关键的设计：Context Overflow 双路径检测——循环前预检和工具调用后即时检测，确保上下文不会超过窗口限制。
>
> **第三层是 Storage Layer**，短期记忆用 Redis（低延迟），长期记忆用 PostgreSQL + 向量索引（支持语义检索），审计日志用 ClickHouse（高写入吞吐）。
>
> **安全方面**，我会设计工具策略管道，分白名单、参数校验、频率限制、审计记录四层。特别要注意提示词注入防护，因为 Skill 拥有系统级权限。
>
> **扩展性方面**，Gateway 通过一致性哈希保证 Session 亲和性，Agent Runner 做无状态化设计可以弹性伸缩，LLM 调用加断路器做容错。
>
> 这个方案的 trade-off 是：Lane-based 设计在中等规模下很优雅，但如果要扩展到百万级并发，需要在 Gateway 层之上加一层 Session 路由器做分片。

---

## 课后练习

### 练习 1：白板设计
在纸上（或白板上）画出完整的 Agent 系统架构图，不看本课内容，限时 15 分钟。然后对比本课架构图，查漏补缺。

### 练习 2：Trade-off 分析
对比以下三种上下文管理方案的优缺点：
- 方案 A：达到上限直接截断最早的消息
- 方案 B：使用 LLM 生成摘要替代早期消息
- 方案 C：保留所有 Tool Calling 结果，只压缩对话消息

### 练习 3：扩展设计
在本课架构基础上，设计一个支持"多 Agent 协同"的扩展方案。需要回答：Agent 间如何通信？共享哪些状态？如何防止幻觉级联放大？

---

**导航**：[上一课 ←](./17-source-code-tour.md) | [下一课 →](./19-resume-guide.md)
