# 第13课：多渠道接入：从 Telegram 到飞书

> **第三阶段：进阶实战** | [← 上一课：MCP 协议](12-mcp-protocol.md) | [下一课 →](14-plugin-development.md)

---

## 本课目标

理解 OpenClaw 多渠道架构的设计原理，掌握 Channel Plugin 的接口抽象方式，能够设计通道抽象层和会话路由策略。

---

## 一、OpenClaw 支持的全部渠道

OpenClaw 是真正的"全渠道" Agent 平台，支持以下消息渠道：

```
┌─────────────────────────────────────────────────┐
│            OpenClaw 渠道支持矩阵                  │
├───────────────┬─────────────────────────────────┤
│ 即时通讯       │ Telegram, WhatsApp, Signal,     │
│               │ iMessage                        │
├───────────────┼─────────────────────────────────┤
│ 团队协作       │ Slack, Discord, Microsoft Teams │
├───────────────┼─────────────────────────────────┤
│ 中国平台       │ 飞书(Lark), 钉钉(DingTalk)      │
├───────────────┼─────────────────────────────────┤
│ 开发者平台     │ API, Webhook, WebSocket          │
├───────────────┼─────────────────────────────────┤
│ Web           │ 内嵌聊天组件                      │
└───────────────┴─────────────────────────────────┘
```

### 为什么支持这么多渠道？

把 Agent 想象成一个全能客服：
- **用户不应该被迫改变习惯** —— 用 Telegram 的就在 Telegram 找 Agent，用飞书的就在飞书里
- **一套 Agent 逻辑，多处触达** —— 避免为每个渠道重写 Agent
- **企业场景刚需** —— 国际团队可能同时用 Slack + 飞书 + Telegram

---

## 二、Channel Plugin 接口设计原理

### 核心问题：如何让一个 Agent 同时对接 10+ 渠道？

答案是**抽象层**——定义一个通用的 Channel 接口，每个渠道只需实现这个接口。

```
┌────────────────────────────────────────────────────┐
│                  Agent Core（核心逻辑）              │
│                                                    │
│   "用户说了什么？" → 思考 → "我要回复什么"           │
│                                                    │
└──────────────────────┬─────────────────────────────┘
                       │
              统一的 Channel 接口
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌─────▼────┐  ┌─────▼────┐
   │Telegram │   │  Slack   │  │  飞书    │  ...
   │ Plugin  │   │  Plugin  │  │  Plugin  │
   └────┬────┘   └────┬─────┘  └────┬─────┘
        │              │              │
   Telegram API   Slack API      飞书 API
```

### Channel 接口定义

```typescript
interface ChannelPlugin {
  // 渠道标识
  readonly channelType: string;    // "telegram" | "slack" | "lark" ...

  // 初始化连接
  connect(config: ChannelConfig): Promise<void>;

  // 接收消息：将渠道原生消息转为统一格式
  onMessage(callback: (message: UnifiedMessage) => void): void;

  // 发送消息：将统一格式转为渠道原生格式并发送
  sendMessage(channelId: string, message: UnifiedMessage): Promise<void>;

  // 发送富媒体
  sendMedia(channelId: string, media: MediaPayload): Promise<void>;

  // 获取渠道能力（是否支持图片、按钮、线程等）
  getCapabilities(): ChannelCapabilities;

  // 断开连接
  disconnect(): Promise<void>;
}
```

### 通用消息格式

```typescript
interface UnifiedMessage {
  id: string;                    // 消息唯一ID
  channelType: string;           // 来源渠道
  channelId: string;             // 渠道内的会话/频道ID
  userId: string;                // 发送者ID
  userName: string;              // 发送者名称
  content: MessageContent;       // 消息内容（见下方）
  timestamp: number;             // 时间戳
  replyTo?: string;              // 回复的消息ID
  metadata?: Record<string, any>; // 渠道特有的额外信息
}

interface MessageContent {
  type: "text" | "image" | "file" | "audio" | "video" | "rich";
  text?: string;
  mediaUrl?: string;
  buttons?: Button[];
  embeds?: Embed[];
}
```

> **面试考点**：如何设计通道抽象层？（系统设计题高频考点）
>
> 回答要点：
> 1. **定义统一接口**：抽象出所有渠道的共同行为（收/发消息、连接/断开）
> 2. **消息格式标准化**：设计能兼容所有渠道的消息结构
> 3. **能力声明**：不同渠道能力不同（有的支持按钮，有的不支持），需要能力查询接口
> 4. **适配器模式**：每个渠道实现一个 Adapter，处理格式转换
> 5. **降级策略**：当目标渠道不支持某能力时如何优雅降级

---

## 三、消息格式标准化

不同渠道的消息格式差异巨大，标准化是多渠道架构的核心挑战。

### 格式转换示例

```
Telegram 原生消息：                    Slack 原生消息：
{                                    {
  "message_id": 123,                   "type": "message",
  "from": {                            "user": "U1234",
    "id": 456,                         "text": "Hello",
    "first_name": "Alice"              "ts": "1716000000.000100",
  },                                   "channel": "C5678"
  "chat": {"id": -789},              }
  "text": "Hello",
  "date": 1716000000
}

        │                                   │
        ▼                                   ▼
   Telegram Adapter                    Slack Adapter
        │                                   │
        └──────────┬────────────────────────┘
                   ▼
          UnifiedMessage：
          {
            "id": "uuid-xxx",
            "channelType": "telegram" | "slack",
            "userId": "456" | "U1234",
            "userName": "Alice" | "...",
            "content": {"type": "text", "text": "Hello"},
            "timestamp": 1716000000
          }
```

### 富媒体降级策略

```
消息类型         Telegram  Slack  Discord  飞书  iMessage
──────────────────────────────────────────────────────
纯文本           ✅        ✅     ✅       ✅    ✅
图片             ✅        ✅     ✅       ✅    ✅
按钮/菜单        ✅        ✅     ✅       ✅    ❌
文件             ✅        ✅     ✅       ✅    ❌
Markdown         ✅        ✅     ✅       ✅    ❌
线程/回复        ✅        ✅     ✅       ✅    ✅
表情回应         ✅        ✅     ✅       ✅    ✅

降级策略示例：
- 按钮 → iMessage：转为编号文本列表 "回复数字选择：1.选项A 2.选项B"
- Markdown → 不支持的渠道：转为纯文本
- 文件 → 不支持的渠道：发送下载链接
```

---

## 四、路由匹配优先级

当一个消息到达 OpenClaw 时，系统需要决定**将它路由到哪个 Agent**。

### 路由决策流程

```
消息到达
    │
    ▼
┌──────────────────────┐
│ 1. 精确匹配           │  channelType + channelId → 特定 Agent
│    (最高优先级)        │  例：Telegram群123 → 专属客服Agent
└──────────┬───────────┘
           │ 未匹配
           ▼
┌──────────────────────┐
│ 2. 渠道匹配           │  channelType → 渠道默认 Agent
│    (中优先级)          │  例：所有Telegram消息 → 通用Agent
└──────────┬───────────┘
           │ 未匹配
           ▼
┌──────────────────────┐
│ 3. 默认路由           │  → 全局默认 Agent
│    (最低优先级)        │
└──────────┬───────────┘
           │ 无默认
           ▼
┌──────────────────────┐
│ 4. 拒绝消息           │  返回错误或忽略
└──────────────────────┘
```

### 路由配置示例

```json
{
  "routing": {
    "rules": [
      {
        "priority": 1,
        "match": {
          "channelType": "telegram",
          "channelId": "group_123"
        },
        "agent": "customer-support-agent"
      },
      {
        "priority": 2,
        "match": {
          "channelType": "slack",
          "channelId": "C_engineering"
        },
        "agent": "devops-agent"
      },
      {
        "priority": 10,
        "match": {
          "channelType": "*"
        },
        "agent": "general-agent"
      }
    ]
  }
}
```

---

## 五、会话隔离粒度设计

### 核心问题

同一个用户 Alice 在 Telegram 和 Discord 上和同一个 Agent 对话，这两个对话应该**共享**还是**隔离**？

```
场景A - 完全隔离：
┌─────────┐     会话1: "帮我写个Python脚本"
│  Alice   │────Telegram──→ [Agent] 上下文：Python需求
│  (同一人) │
│          │────Discord───→ [Agent] 上下文：空（全新对话）
└─────────┘     会话2: "你好"

场景B - 完全共享：
┌─────────┐     会话1: "帮我写个Python脚本"
│  Alice   │────Telegram──→ [Agent] 上下文：Python需求
│  (同一人) │                    ↕ 共享
│          │────Discord───→ [Agent] 上下文：Python需求
└─────────┘     "接上面的需求，再加个GUI"
```

### sessionKey 的设计

sessionKey 决定了会话的隔离粒度：

```
隔离策略              sessionKey 组成                 效果
───────────────────────────────────────────────────────────
渠道级隔离（默认）     channelType:userId              每个渠道独立会话
                      "telegram:alice_123"
                      "discord:alice_456"

用户级共享            userId（跨渠道统一ID）            所有渠道共享会话
                      "alice@email.com"

会话级隔离            channelType:channelId:userId    每个群/频道独立
                      "slack:C_eng:alice"
                      "slack:C_random:alice"

完全隔离              channelType:channelId:          每条消息独立
                      messageId                       （无状态模式）
```

### 配置方式

```json
{
  "session": {
    "isolation": "channel",
    "keyTemplate": "${channelType}:${userId}",
    "ttl": "24h",
    "maxHistory": 100,
    "crossChannelSync": false
  }
}
```

> **面试考点**：如何设计跨渠道的用户身份关联？
>
> 挑战：Alice 在 Telegram 是 `tg_alice_123`，在 Slack 是 `slack_U789`，系统如何知道是同一个人？
>
> 解决方案：
> 1. **统一账号系统**：用户绑定邮箱，各渠道ID映射到同一内部用户ID
> 2. **邀请码关联**：用户在新渠道发送关联码，完成身份绑定
> 3. **管理员手动关联**：后台管理界面手动映射
> 4. **OAuth关联**：通过第三方OAuth统一认证
>
> 这是系统设计面试中"用户身份模型"的经典变种题。

---

## 六、配置一个新渠道的实操步骤

以接入 **飞书（Lark）** 为例：

### 步骤1：安装渠道 Plugin

```bash
/plugins install @openclaw/channel-lark
```

### 步骤2：在飞书开放平台创建应用

```
1. 登录 飞书开放平台 (open.feishu.cn)
2. 创建企业自建应用
3. 开启"机器人"能力
4. 获取 App ID 和 App Secret
5. 配置事件订阅 URL
6. 配置权限：
   - im:message:receive_v1（接收消息）
   - im:message:send_as_bot（发送消息）
```

### 步骤3：配置 openclaw.json

```json
{
  "channels": {
    "lark": {
      "enabled": true,
      "appId": "${LARK_APP_ID}",
      "appSecret": "${LARK_APP_SECRET}",
      "verificationToken": "${LARK_VERIFICATION_TOKEN}",
      "encryptKey": "${LARK_ENCRYPT_KEY}",
      "eventUrl": "https://your-domain.com/webhook/lark"
    }
  }
}
```

### 步骤4：配置路由规则

```json
{
  "routing": {
    "rules": [
      {
        "match": { "channelType": "lark" },
        "agent": "company-assistant"
      }
    ]
  }
}
```

### 步骤5：测试

```
在飞书中 @你的机器人，发送测试消息，
观察 Agent 是否正确接收和回复。
```

### 完整流程图

```
飞书用户发消息
      │
      ▼
飞书服务器 ──webhook──→ OpenClaw 接收端点
                              │
                              ▼
                       Lark Channel Plugin
                       (格式转换为 UnifiedMessage)
                              │
                              ▼
                        路由引擎匹配
                              │
                              ▼
                        Agent 处理消息
                              │
                              ▼
                       Lark Channel Plugin
                       (UnifiedMessage → 飞书格式)
                              │
                              ▼
                  飞书 API ──发送──→ 飞书用户
```

---

## 七、通道抽象层的设计模式

这是面试系统设计题的高频考点，总结核心设计模式：

```
┌─────────────────────────────────────────────────────┐
│               通道抽象层设计要点                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. 适配器模式 (Adapter Pattern)                     │
│     每个渠道一个适配器，转换消息格式                    │
│                                                     │
│  2. 能力协商 (Capability Negotiation)                │
│     查询渠道支持的功能，动态调整输出                    │
│                                                     │
│  3. 优雅降级 (Graceful Degradation)                  │
│     不支持的功能自动转为最接近的替代方案                 │
│                                                     │
│  4. 事件驱动 (Event-Driven)                          │
│     消息到达触发事件，解耦收发逻辑                      │
│                                                     │
│  5. 幂等性设计 (Idempotency)                         │
│     Webhook可能重试，确保同一消息不重复处理              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

> **面试考点**：如果让你设计一个新的渠道抽象层，你会如何处理"渠道特有功能"？
>
> 例如 Slack 有"线程回复"、Telegram 有"内联键盘"、Discord 有"斜杠命令"。
>
> 参考答案：
> - **核心接口只包含共性功能**（发消息、收消息）
> - **扩展接口用于特有功能**（通过 `metadata` 字段或 `ChannelCapabilities`）
> - **不要为了适配一个渠道而污染通用接口**
> - 遵循"**交集做接口，差集做扩展**"的原则

---

## 本课小结

```
┌──────────────────────────────────────────────┐
│              核心知识点回顾                    │
├──────────────────────────────────────────────┤
│                                              │
│  支持渠道：Telegram, WhatsApp, Slack,         │
│           Discord, 飞书, 钉钉, Signal,        │
│           iMessage, Teams, API...            │
│                                              │
│  Channel Plugin 接口：                        │
│    connect / onMessage / sendMessage /        │
│    getCapabilities / disconnect              │
│                                              │
│  UnifiedMessage = 统一消息格式                │
│  路由优先级：精确 > 渠道 > 默认               │
│                                              │
│  sessionKey 设计决定会话隔离粒度              │
│    渠道级 / 用户级 / 会话级 / 完全隔离        │
│                                              │
│  设计关键词：                                 │
│    适配器模式 + 能力协商 + 优雅降级           │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 课后练习

### 练习1：接口设计
为 **钉钉（DingTalk）** 设计 Channel Plugin 的接口实现（伪代码即可）。要求处理以下场景：
- 群消息中 @机器人
- 单聊消息
- 富文本消息（包含图片和链接）

### 练习2：会话隔离方案
设计一个 sessionKey 方案，满足以下需求：
- 同一用户在同一个 Slack 工作区的不同频道，会话**隔离**
- 同一用户在 Telegram 私聊和 Slack DM 中，会话**共享**（需要身份关联）
- 提供 sessionKey 的生成算法和配置格式

### 练习3：系统设计
如果 OpenClaw 需要新增一个"微信公众号"渠道，请完成：
- 列出技术挑战（微信的特殊限制有哪些？）
- 设计消息格式适配方案
- 设计回复的超时处理策略（微信要求5秒内回复）
- 考虑 Agent 思考时间较长时的降级方案

---

> [← 上一课：MCP 协议](12-mcp-protocol.md) | [下一课：插件开发 →](14-plugin-development.md)
