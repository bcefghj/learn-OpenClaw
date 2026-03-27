# 第12课：MCP 协议：Agent 的通用语言

> **第三阶段：进阶实战** | [← 上一课：Skills 系统](11-skills-system.md) | [下一课 →](13-multi-channel.md)

---

## 本课目标

理解 MCP（Model Context Protocol）协议的设计理念和技术架构，掌握 OpenClaw 中 MCP 的集成方式，能够分析 MCP 工具定义并对比直接 API 调用的优劣。

---

## 一、什么是 MCP（Model Context Protocol）

MCP 是由 **Anthropic** 创建的**开放标准协议**，定义了 AI Agent 与外部工具/服务之间的通信规范。

### USB 接口的比喻

```
没有 MCP 的世界（混乱）：
┌────────┐    专用接口A    ┌──────────┐
│ Agent  │────────────────│ 搜索服务  │
│        │    专用接口B    ├──────────┤
│        │────────────────│ 数据库    │
│        │    专用接口C    ├──────────┤
│        │────────────────│ 文件系统  │
│        │    专用接口D    ├──────────┤
│        │────────────────│ 邮件服务  │
└────────┘                └──────────┘
  每个服务都需要定制开发适配器，N个服务 = N种接口

有 MCP 的世界（统一）：
┌────────┐                ┌──────────┐
│ Agent  │    ┌───────┐   │ 搜索服务  │
│        │────│  MCP  │───│ 数据库    │
│        │    │ 协议  │   │ 文件系统  │
│        │    └───────┘   │ 邮件服务  │
└────────┘     统一接口    └──────────┘
  一个协议连接所有服务，就像 USB 连接所有设备
```

就像 USB 让你不用关心插的是鼠标、键盘还是U盘一样，MCP 让 Agent 不用关心对接的是搜索引擎、数据库还是文件系统 —— **统一的协议，统一的调用方式**。

> **面试考点**：为什么需要 MCP 这样的标准化协议？
> 1. **降低集成成本**：新服务只需实现 MCP 接口，所有兼容 Agent 都能使用
> 2. **生态互通**：不同厂商的 Agent 可以共享同一个工具市场
> 3. **质量保障**：标准化的工具定义让 Agent 更准确地理解和调用工具
> 4. **可发现性**：Agent 可以动态发现和加载新工具

---

## 二、MCP 的 Server/Client 架构

```
┌─────────────────────────────────────────────────────┐
│                    MCP 架构全景                       │
│                                                     │
│  ┌──────────────┐         ┌──────────────────────┐  │
│  │  MCP Client  │         │    MCP Server         │  │
│  │  (Agent侧)   │         │    (工具/服务侧)       │  │
│  │              │         │                      │  │
│  │  ┌────────┐ │  JSON-  │  ┌────────────────┐  │  │
│  │  │ 发现   │──────────────│ 工具注册表      │  │  │
│  │  │ 模块   │ │  RPC    │  │ (tools/list)   │  │  │
│  │  └────────┘ │         │  └────────────────┘  │  │
│  │              │         │                      │  │
│  │  ┌────────┐ │  请求/  │  ┌────────────────┐  │  │
│  │  │ 调用   │──────────────│ 工具执行器      │  │  │
│  │  │ 模块   │ │  响应   │  │ (tools/call)   │  │  │
│  │  └────────┘ │         │  └────────────────┘  │  │
│  │              │         │                      │  │
│  │  ┌────────┐ │         │  ┌────────────────┐  │  │
│  │  │ 上下文 │──────────────│ 资源提供器      │  │  │
│  │  │ 管理   │ │         │  │ (resources)    │  │  │
│  │  └────────┘ │         │  └────────────────┘  │  │
│  └──────────────┘         └──────────────────────┘  │
│                                                     │
│         传输层：stdio / HTTP+SSE / WebSocket         │
└─────────────────────────────────────────────────────┘
```

### 核心概念

| 概念 | 角色 | 说明 |
|------|------|------|
| **MCP Client** | 消费方 | Agent 侧，发起工具发现和调用请求 |
| **MCP Server** | 提供方 | 工具/服务侧，注册并执行工具 |
| **Tools** | 能力 | Server 暴露的可调用函数 |
| **Resources** | 数据 | Server 提供的上下文数据（文件、数据库记录等） |
| **Prompts** | 模板 | Server 提供的提示模板 |

### 通信流程

```
Agent (Client)                    MCP Server
    │                                 │
    │──── 1. initialize ─────────────>│  建立连接
    │<─── 1a. capabilities ──────────│  返回能力列表
    │                                 │
    │──── 2. tools/list ─────────────>│  发现可用工具
    │<─── 2a. tool definitions ──────│  返回工具定义
    │                                 │
    │──── 3. tools/call ─────────────>│  调用具体工具
    │     {name, arguments}           │
    │<─── 3a. result ────────────────│  返回执行结果
    │     {content}                   │
    │                                 │
    │──── 4. tools/call ─────────────>│  可以多次调用
    │<─── 4a. result ────────────────│
    │                                 │
```

---

## 三、OpenClaw 中的 MCP 集成

OpenClaw 是目前**最大的 MCP 兼容平台**。在 OpenClaw 的生态中：

**每一个 ClawHub Skill 就是一个 MCP Server。**

```
┌─────────────────────────────────────────────┐
│              OpenClaw Agent                  │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │         MCP Client（内置）           │    │
│  │                                     │    │
│  │  自动连接所有已安装的 Skills         │    │
│  └──────┬──────────┬──────────┬────────┘    │
│         │          │          │              │
│    ┌────▼───┐ ┌────▼───┐ ┌───▼────┐        │
│    │ Skill  │ │ Skill  │ │ Skill  │        │
│    │  A     │ │  B     │ │  C     │  ...   │
│    │(MCP    │ │(MCP    │ │(MCP    │        │
│    │Server) │ │Server) │ │Server) │        │
│    └────────┘ └────────┘ └────────┘        │
│                                             │
│    ClawHub 5700+ Skills = 5700+ MCP Servers │
└─────────────────────────────────────────────┘
```

当你执行 `/skills install @author/skill-name` 时，实际上是：
1. 从 ClawHub 下载 Skill 包
2. 注册为一个 MCP Server
3. Agent 的 MCP Client 自动发现并连接该 Server
4. Server 暴露的 Tools 自动变成 Agent 可用的工具

---

## 四、MCP 工具定义的格式和规范

### 标准 MCP 工具定义

```json
{
  "name": "web_search",
  "description": "Search the web for real-time information about any topic. Returns summarized results and relevant URLs.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query to look up"
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum number of results to return",
        "default": 5
      },
      "language": {
        "type": "string",
        "description": "Preferred language for results (ISO 639-1 code)",
        "default": "en"
      }
    },
    "required": ["query"]
  }
}
```

### 定义规范要点

```
MCP 工具定义的三要素：
┌──────────────────────────────────────────┐
│                                          │
│  1. name        工具唯一标识符            │
│     └── 小写，下划线分隔，语义明确        │
│                                          │
│  2. description 自然语言描述              │
│     └── 告诉 Agent 何时、为何使用此工具   │
│     └── 这是 Agent 决策的关键依据！       │
│                                          │
│  3. inputSchema JSON Schema 参数定义      │
│     └── 类型、描述、默认值、必填项        │
│     └── Agent 据此自动构造调用参数        │
│                                          │
└──────────────────────────────────────────┘
```

> **面试考点**：`description` 字段为什么如此重要？
> Agent 在决定使用哪个工具时，主要依据就是 `description`。一个模糊的描述会导致 Agent 误用工具或完全忽略它。好的 description 应该回答三个问题：
> 1. 这个工具**做什么**？
> 2. **什么时候**应该使用它？
> 3. 调用后会**返回什么**？

---

## 五、MCP vs 直接 API 调用

| 对比维度 | MCP 协议 | 直接 API 调用 |
|----------|----------|--------------|
| **集成成本** | 低 —— 统一协议 | 高 —— 每个API都不同 |
| **工具发现** | 自动 —— `tools/list` | 手动 —— 查文档写代码 |
| **参数校验** | 内置 —— JSON Schema | 自行实现 |
| **生态复用** | 强 —— ClawHub共享 | 弱 —— 各自实现 |
| **灵活性** | 受协议约束 | 完全自由 |
| **性能** | 有协议开销 | 直接调用更快 |
| **错误处理** | 标准化错误格式 | 各API自定义 |
| **安全模型** | 协议层权限控制 | 各自实现 |

### 什么时候该用 MCP？

```
应该用 MCP：                    可以直接 API：
─────────────                  ──────────────
✓ 需要 Agent 动态使用          ✗ 固定的后端调用
✓ 希望社区能复用               ✗ 内部系统专用
✓ 需要多个 Agent 共享          ✗ 单一应用使用
✓ 工具可能被替换               ✗ 紧耦合不可替换
```

---

## 六、实例：web-search Skill 的 MCP 实现

以 `@anthropic/web-search` Skill 为例，看看一个完整的 MCP 工具链路：

### 1. SKILL.md（提示层）

```markdown
# Web Search Skill

When the user asks a question that requires up-to-date information,
use the `web_search` tool to find relevant results.

## Guidelines
- Prefer specific, detailed search queries over vague ones
- Always cite sources with URLs in your response
- If first search doesn't find relevant results, refine and retry
- Maximum 3 search attempts per user query
```

### 2. MCP Server 定义（协议层）

```json
{
  "name": "@anthropic/web-search",
  "version": "2.1.0",
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web for real-time information",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": { "type": "string" },
          "max_results": { "type": "integer", "default": 5 }
        },
        "required": ["query"]
      }
    }
  ]
}
```

### 3. 调用链路

```
用户: "今天北京天气怎么样?"
         │
         ▼
┌─────────────────────┐
│ Agent 阅读 SKILL.md │  → 知道遇到时事问题要用 web_search
│ 决定使用 web_search  │
└─────────┬───────────┘
          │
          ▼  MCP tools/call
┌─────────────────────┐
│ MCP Server 执行搜索  │  → web_search({query: "北京今天天气"})
│ 返回搜索结果         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Agent 整理结果       │  → 根据 SKILL.md 的指令，引用来源
│ 回复用户             │
└─────────────────────┘
```

> **面试考点**：如果同时安装了两个都提供 web_search 的 Skill 会怎样？
> 这涉及**工具冲突解决**问题：
> - OpenClaw 使用**优先级机制**：后安装的覆盖先安装的
> - 也可以在配置中显式指定优先级
> - Agent 在工具列表中只会看到最终生效的那一个
> - 类似编程中的"名称遮蔽（name shadowing）"

---

## 七、MCP 的生态和未来发展

### 当前生态

```
MCP 兼容平台：
├── OpenClaw     ── 最大的 MCP 平台，5700+ Skills
├── Claude       ── Anthropic 官方 AI 助手
├── Cursor       ── AI 编程 IDE
├── Windsurf     ── AI 编程工具
├── VS Code      ── 通过 Copilot 扩展
└── 更多平台持续接入中...
```

### 发展趋势

1. **协议标准化**：MCP 正在成为 AI Agent 工具调用的事实标准
2. **Server 生态爆发**：越来越多服务商提供 MCP Server
3. **多模态支持**：从文本扩展到图像、音频、视频
4. **安全增强**：更细粒度的权限控制和审计
5. **性能优化**：流式传输、批量调用、缓存策略

> **面试考点**：MCP 的主要挑战是什么？
> 1. **协议版本兼容**：如何平滑升级而不破坏现有生态
> 2. **性能开销**：序列化/反序列化的额外成本
> 3. **安全信任**：如何验证第三方 MCP Server 的安全性
> 4. **标准博弈**：与其他类似协议（如 OpenAI 的 function calling）的竞争

---

## 本课小结

```
┌──────────────────────────────────────────────┐
│              核心知识点回顾                    │
├──────────────────────────────────────────────┤
│                                              │
│  MCP = Model Context Protocol                │
│      = AI Agent 的 "USB 接口"                │
│                                              │
│  架构 = Client (Agent) ←→ Server (工具)       │
│  传输 = stdio / HTTP+SSE / WebSocket         │
│                                              │
│  在 OpenClaw 中：                             │
│    每个 ClawHub Skill = 一个 MCP Server       │
│    安装 Skill = 连接新的 MCP Server           │
│    5700+ Skills = 5700+ MCP Servers          │
│                                              │
│  工具定义 = name + description + inputSchema  │
│  description 是 Agent 决策的关键依据          │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 课后练习

### 练习1：协议理解
画出一个完整的 MCP 调用时序图，从用户发送消息开始，到最终收到回复为止。标注每一步涉及的协议操作（initialize、tools/list、tools/call 等）。

### 练习2：工具定义编写
为一个"翻译服务"编写 MCP 工具定义（JSON 格式），要求：
- 支持源语言和目标语言参数
- 支持批量翻译（文本数组）
- 包含清晰的 description
- 定义合理的默认值和必填项

### 练习3：对比分析
一家公司有50个内部 API 服务，正在考虑是否将它们全部封装为 MCP Server。请从**成本、收益、风险**三个维度分析，给出你的建议。在什么条件下应该迁移，什么条件下应该保持现状？

---

> [← 上一课：Skills 系统](11-skills-system.md) | [下一课：多渠道接入 →](13-multi-channel.md)
