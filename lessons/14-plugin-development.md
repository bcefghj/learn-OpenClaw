# 第14课：插件开发：写你的第一个 Plugin

> **第三阶段：进阶实战** | [← 上一课：多渠道接入](13-multi-channel.md) | [下一课 →](15-automation-workflow.md)

---

## 本课目标

理解 OpenClaw 的 Plugin 架构和四种插件类型，掌握 Plugin 的开发流程和生命周期，能够独立开发一个包含工具注册和 Hook 扩展的完整插件。

---

## 一、Plugin 架构概述

如果说 Skills 是"操作手册"，那 Plugin 就是"功能模块"。Plugin 是 OpenClaw 最强大的扩展机制，它可以注册新能力、拦截处理流程、接入外部服务。

### 四种 Plugin 类型

```
┌────────────────────────────────────────────────────────────┐
│                   Plugin 四种类型                            │
├────────────────┬───────────────────────────────────────────┤
│                │                                           │
│  Plain-        │  纯能力型：只提供新能力（工具、渠道等）       │
│  capability    │  例：天气查询工具、图片生成服务               │
│                │  特点：不干预处理流程，只提供可调用的能力      │
│                │                                           │
├────────────────┼───────────────────────────────────────────┤
│                │                                           │
│  Hybrid-       │  混合型：既提供能力，又通过 Hook 扩展流程    │
│  capability    │  例：数据库Plugin（提供查询工具 + 记录审计）  │
│                │  特点：最灵活，能力 + 流程扩展兼备           │
│                │                                           │
├────────────────┼───────────────────────────────────────────┤
│                │                                           │
│  Hook-only     │  仅钩子型：只通过 Hook 扩展处理流程         │
│                │  例：消息过滤器、日志记录器、权限检查器       │
│                │  特点：不提供新工具，只拦截和修改现有流程     │
│                │                                           │
├────────────────┼───────────────────────────────────────────┤
│                │                                           │
│  Non-          │  无能力型：不直接提供功能                    │
│  capability    │  例：配置加载器、环境变量注入器               │
│                │  特点：辅助性插件，为其他组件提供支持         │
│                │                                           │
└────────────────┴───────────────────────────────────────────┘
```

### Plugin 类型决策树

```
你的 Plugin 需要提供新工具吗？
├── 是 → 需要拦截处理流程吗？
│        ├── 是 → Hybrid-capability
│        └── 否 → Plain-capability
└── 否 → 需要拦截处理流程吗？
         ├── 是 → Hook-only
         └── 否 → Non-capability
```

---

## 二、Plugin 可以注册的能力类型

```
┌──────────────────────────────────────────────┐
│         Plugin 可注册的能力类型                │
├──────────────┬───────────────────────────────┤
│ channels     │ 新的消息渠道                    │
│              │ 例：接入微信、LINE等            │
├──────────────┼───────────────────────────────┤
│ model        │ 新的 LLM 提供商                │
│ providers    │ 例：接入本地Ollama、自托管模型   │
├──────────────┼───────────────────────────────┤
│ tools        │ Agent可调用的新工具             │
│              │ 例：天气API、数据库查询          │
├──────────────┼───────────────────────────────┤
│ skills       │ 打包的SKILL.md文件             │
│              │ 例：附带使用指南的工具包         │
├──────────────┼───────────────────────────────┤
│ speech       │ 语音识别/合成能力              │
│              │ 例：接入Whisper、TTS服务        │
├──────────────┼───────────────────────────────┤
│ image        │ 图像生成/处理能力              │
│ generation   │ 例：接入DALL-E、Stable Diffusion│
└──────────────┴───────────────────────────────┘
```

> **面试考点**：Plugin 的能力注册机制是如何实现的？
>
> 核心思想是**注册表模式（Registry Pattern）**：
> 1. OpenClaw 核心维护一个全局注册表
> 2. Plugin 启动时将自己的能力注册到对应类别
> 3. Agent 运行时从注册表查询可用能力
> 4. 这实现了 Plugin 和核心的**松耦合**

---

## 三、Plugin 开发全流程

以一个 **"随机笑话生成器"** Plugin 为例，演示完整开发流程。

### 步骤1：创建 Plugin 目录结构

```
my-joke-plugin/
├── index.ts          # 入口文件
├── package.json      # 包配置
├── tools/
│   └── get-joke.ts   # 工具实现
└── SKILL.md          # 使用指南（可选）
```

### 步骤2：定义 Plugin 入口

```typescript
// index.ts
import { Plugin, PluginContext } from '@openclaw/sdk';
import { getJokeTool } from './tools/get-joke';

export default class JokePlugin implements Plugin {
  name = 'joke-plugin';
  version = '1.0.0';
  type = 'plain-capability';

  async onLoad(ctx: PluginContext): Promise<void> {
    // 注册工具
    ctx.registerTool(getJokeTool);

    console.log('Joke Plugin loaded!');
  }

  async onUnload(): Promise<void> {
    console.log('Joke Plugin unloaded.');
  }
}
```

### 步骤3：实现工具

```typescript
// tools/get-joke.ts
import { Tool, ToolResult } from '@openclaw/sdk';

export const getJokeTool: Tool = {
  name: 'get_joke',
  description: 'Get a random joke. Use when the user asks for a joke or needs cheering up.',
  parameters: {
    type: 'object',
    properties: {
      category: {
        type: 'string',
        description: 'Joke category: programming, dad, general',
        enum: ['programming', 'dad', 'general'],
        default: 'general'
      },
      language: {
        type: 'string',
        description: 'Language for the joke',
        default: 'en'
      }
    }
  },

  async execute(params: { category: string; language: string }): Promise<ToolResult> {
    const response = await fetch(
      `https://joke-api.example.com/random?category=${params.category}&lang=${params.language}`
    );
    const joke = await response.json();

    return {
      success: true,
      content: `${joke.setup}\n\n${joke.punchline}`
    };
  }
};
```

### 步骤4：配置 package.json

```json
{
  "name": "@myname/joke-plugin",
  "version": "1.0.0",
  "description": "A plugin that tells random jokes",
  "main": "index.ts",
  "openclaw": {
    "type": "plugin",
    "pluginType": "plain-capability",
    "capabilities": ["tools"]
  }
}
```

### 步骤5：注册到 openclaw.json

```json
{
  "plugins": [
    {
      "name": "@myname/joke-plugin",
      "enabled": true,
      "config": {
        "defaultCategory": "programming"
      }
    }
  ]
}
```

---

## 四、Plugin 的注册和生命周期

```
┌─────────────────────────────────────────────────────┐
│              Plugin 生命周期                          │
│                                                     │
│   ┌──────────┐                                      │
│   │ 发现     │  系统扫描 openclaw.json 中的插件配置    │
│   └────┬─────┘                                      │
│        │                                            │
│        ▼                                            │
│   ┌──────────┐                                      │
│   │ 加载     │  导入插件代码，校验接口合规              │
│   └────┬─────┘                                      │
│        │                                            │
│        ▼                                            │
│   ┌──────────┐                                      │
│   │ 初始化   │  调用 onLoad()，注册能力和 Hook        │
│   └────┬─────┘                                      │
│        │                                            │
│        ▼                                            │
│   ┌──────────┐                                      │
│   │ 运行中   │  插件正常工作，响应调用和事件           │
│   └────┬─────┘                                      │
│        │                                            │
│        ▼                                            │
│   ┌──────────┐                                      │
│   │ 卸载     │  调用 onUnload()，清理资源             │
│   └──────────┘                                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 生命周期钩子

```typescript
interface Plugin {
  name: string;
  version: string;

  // 插件加载时调用 - 注册能力、初始化资源
  onLoad(ctx: PluginContext): Promise<void>;

  // 插件卸载时调用 - 清理资源、关闭连接
  onUnload(): Promise<void>;

  // 配置更新时调用（可选）
  onConfigChange?(newConfig: Record<string, any>): Promise<void>;

  // 健康检查（可选）
  healthCheck?(): Promise<HealthStatus>;
}
```

> **面试考点**：Plugin 加载顺序如何控制？依赖冲突如何解决？
>
> 1. **加载顺序**：通过 `openclaw.json` 中的 `priority` 字段或声明式依赖
> 2. **依赖解析**：类似 npm 的依赖树解析，Plugin 可声明依赖其他 Plugin
> 3. **冲突检测**：如果两个 Plugin 注册同名工具，后加载的覆盖先加载的
> 4. **循环依赖**：系统检测并报错，要求开发者解除循环

---

## 五、Hook 系统详解

Hook 是 Plugin 扩展 OpenClaw 处理流程的核心机制，类似于 Web 框架中的**中间件（Middleware）**。

### Hook 的执行模型

```
用户消息到达
      │
      ▼
┌─────────────────────────────────────────┐
│          Hook 管道 (Pipeline)            │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ Hook 1  │→ │ Hook 2  │→ │ Hook 3  │ │
│  │ 日志    │  │ 权限    │  │ 过滤    │ │
│  └─────────┘  └─────────┘  └─────────┘ │
│                                         │
└──────────────────┬──────────────────────┘
                   │
                   ▼
            Agent 核心处理
                   │
                   ▼
┌─────────────────────────────────────────┐
│        Hook 管道 (Response)              │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ Hook 3  │→ │ Hook 2  │→ │ Hook 1  │ │
│  │ 格式化  │  │ 审计    │  │ 日志    │ │
│  └─────────┘  └─────────┘  └─────────┘ │
│                                         │
└──────────────────┬──────────────────────┘
                   │
                   ▼
             回复发送给用户
```

### 可用的 Hook 点

```
Hook 名称                   触发时机                   典型用途
─────────────────────────────────────────────────────────────
beforeMessageReceive       消息被 Agent 处理之前        过滤、鉴权、日志
afterMessageReceive        消息被 Agent 处理之后        审计、统计
beforeToolCall             工具被调用之前               权限检查、参数校验
afterToolCall              工具调用完成之后             结果缓存、日志
beforeResponse             Agent 回复发送之前           内容审核、格式化
afterResponse              Agent 回复发送之后           日志、触发后续动作
onError                    处理过程中出错               错误报告、降级
onSessionStart             新会话开始                   初始化用户上下文
onSessionEnd               会话结束                     清理资源、保存摘要
```

### Hook 注册示例

```typescript
// 一个内容审核 Hook
export default class ContentFilterPlugin implements Plugin {
  name = 'content-filter';
  type = 'hook-only';

  async onLoad(ctx: PluginContext): Promise<void> {
    // 在 Agent 回复发送之前进行内容审核
    ctx.registerHook('beforeResponse', async (context, next) => {
      const response = context.response;

      // 检查是否包含敏感内容
      if (containsSensitiveContent(response.text)) {
        // 替换敏感内容
        context.response.text = sanitize(response.text);
        console.log('Sensitive content filtered');
      }

      // 调用下一个 Hook（中间件模式）
      await next();
    });

    // 在工具调用之前检查权限
    ctx.registerHook('beforeToolCall', async (context, next) => {
      const { toolName, userId } = context;

      if (!hasPermission(userId, toolName)) {
        throw new Error(`User ${userId} not authorized to use ${toolName}`);
      }

      await next();
    });
  }
}
```

> **面试考点**：Hook/中间件模式相比硬编码逻辑有什么优势？
>
> 1. **可插拔**：新增/移除功能不需要修改核心代码
> 2. **可排序**：通过优先级控制执行顺序
> 3. **可组合**：多个 Hook 组合实现复杂逻辑
> 4. **关注点分离**：日志、鉴权、过滤各自独立
> 5. **开闭原则**：对扩展开放，对修改关闭

---

## 六、工具的权限控制：策略管道分层设计

OpenClaw 的权限控制不是简单的"允许/拒绝"，而是一个**分层策略管道**：

```
工具调用请求
      │
      ▼
┌─────────────────────────────────┐
│  Layer 1: 全局策略               │
│  "这个工具是否被全局禁用?"        │
│  例：shell_exec 在生产环境禁用    │
└──────────────┬──────────────────┘
               │ 通过
               ▼
┌─────────────────────────────────┐
│  Layer 2: 用户/角色策略          │
│  "该用户是否有权使用此工具?"      │
│  例：只有管理员可以用 file_write  │
└──────────────┬──────────────────┘
               │ 通过
               ▼
┌─────────────────────────────────┐
│  Layer 3: 渠道策略               │
│  "此渠道是否允许使用此工具?"      │
│  例：公共Slack频道不允许 shell    │
└──────────────┬──────────────────┘
               │ 通过
               ▼
┌─────────────────────────────────┐
│  Layer 4: 参数策略               │
│  "工具参数是否在允许范围内?"      │
│  例：file_read 只能读 /safe/ 目录│
└──────────────┬──────────────────┘
               │ 通过
               ▼
          执行工具调用
```

### 策略配置示例

```json
{
  "toolPolicies": {
    "global": {
      "shell_exec": {
        "enabled": true,
        "allowedCommands": ["ls", "cat", "grep", "find"],
        "blockedCommands": ["rm -rf", "sudo", "chmod"]
      }
    },
    "roles": {
      "admin": {
        "shell_exec": { "enabled": true, "allowedCommands": ["*"] }
      },
      "user": {
        "shell_exec": { "enabled": false }
      }
    },
    "channels": {
      "slack:C_public": {
        "shell_exec": { "enabled": false },
        "file_write": { "enabled": false }
      }
    }
  }
}
```

> **面试考点**：为什么要分层设计权限策略？
>
> 1. **层级覆盖**：细粒度策略覆盖粗粒度策略（参数级 > 渠道级 > 用户级 > 全局）
> 2. **默认安全**：全局默认最严格，逐层放宽
> 3. **可审计**：每层策略独立记录，方便排查权限问题
> 4. **关注点分离**：安全团队管全局策略，业务团队管用户策略

---

## 七、实战：开发一个天气查询 Plugin

### 完整代码

```typescript
// weather-plugin/index.ts
import { Plugin, PluginContext, Tool, ToolResult } from '@openclaw/sdk';

export default class WeatherPlugin implements Plugin {
  name = 'weather-plugin';
  version = '1.0.0';
  type = 'hybrid-capability';

  private apiKey: string = '';

  async onLoad(ctx: PluginContext): Promise<void> {
    this.apiKey = ctx.config.apiKey;

    // 注册天气查询工具
    ctx.registerTool({
      name: 'get_weather',
      description: 'Get current weather and forecast for a city. Use when user asks about weather conditions.',
      parameters: {
        type: 'object',
        properties: {
          city: {
            type: 'string',
            description: 'City name, e.g. "Beijing", "New York"'
          },
          units: {
            type: 'string',
            enum: ['celsius', 'fahrenheit'],
            default: 'celsius',
            description: 'Temperature unit'
          },
          days: {
            type: 'integer',
            default: 1,
            description: 'Number of forecast days (1-7)'
          }
        },
        required: ['city']
      },
      execute: this.getWeather.bind(this)
    });

    // 注册 Hook：记录天气查询日志
    ctx.registerHook('afterToolCall', async (context, next) => {
      if (context.toolName === 'get_weather') {
        console.log(`Weather queried: ${context.params.city} by ${context.userId}`);
      }
      await next();
    });
  }

  private async getWeather(params: {
    city: string;
    units: string;
    days: number;
  }): Promise<ToolResult> {
    try {
      const url = `https://api.weather.example.com/v1/forecast?city=${encodeURIComponent(params.city)}&units=${params.units}&days=${params.days}&key=${this.apiKey}`;

      const response = await fetch(url);

      if (!response.ok) {
        return {
          success: false,
          error: `Weather API error: ${response.status}`
        };
      }

      const data = await response.json();

      const result = {
        city: data.city,
        current: {
          temperature: data.current.temp,
          condition: data.current.condition,
          humidity: data.current.humidity,
          wind: data.current.wind
        },
        forecast: data.forecast.map((day: any) => ({
          date: day.date,
          high: day.high,
          low: day.low,
          condition: day.condition
        }))
      };

      return {
        success: true,
        content: JSON.stringify(result, null, 2)
      };
    } catch (error) {
      return {
        success: false,
        error: `Failed to fetch weather: ${error}`
      };
    }
  }

  async onUnload(): Promise<void> {
    // 清理工作
  }
}
```

### 配套 SKILL.md

```markdown
# Weather Query Skill

When the user asks about weather, use the `get_weather` tool.

## Guidelines
- Always ask for the city name if not specified
- Default to celsius for Chinese users, fahrenheit for US users
- Present weather in a friendly, readable format
- Include suggestions based on weather (e.g., "bring an umbrella")
```

### 安装和配置

```json
{
  "plugins": [
    {
      "name": "@myname/weather-plugin",
      "enabled": true,
      "config": {
        "apiKey": "${WEATHER_API_KEY}"
      }
    }
  ]
}
```

---

## 八、Plugin 开发最佳实践

```
┌────────────────────────────────────────────────────┐
│            Plugin 开发最佳实践                      │
├────────────────────────────────────────────────────┤
│                                                    │
│  1. 单一职责：一个 Plugin 只做一件事               │
│                                                    │
│  2. 错误隔离：Plugin 的错误不应该影响 Agent 核心    │
│     → try/catch 包裹所有外部调用                   │
│                                                    │
│  3. 配置外部化：API Key 等敏感信息通过环境变量传入  │
│     → 永远不要硬编码密钥                           │
│                                                    │
│  4. 优雅降级：外部服务不可用时返回有意义的错误信息  │
│     → 而不是让整个 Agent 崩溃                      │
│                                                    │
│  5. 资源清理：onUnload 中关闭连接、清理定时器       │
│     → 防止内存泄漏                                 │
│                                                    │
│  6. 日志规范：使用结构化日志，包含 Plugin 名称       │
│     → 方便排查问题                                 │
│                                                    │
│  7. 版本兼容：明确声明兼容的 OpenClaw 版本          │
│     → 避免 API 变更导致的问题                      │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 本课小结

```
┌──────────────────────────────────────────────────┐
│              核心知识点回顾                        │
├──────────────────────────────────────────────────┤
│                                                  │
│  四种 Plugin 类型：                               │
│    Plain-capability  纯能力型                     │
│    Hybrid-capability 混合型                       │
│    Hook-only         仅钩子型                     │
│    Non-capability    无能力型                     │
│                                                  │
│  可注册能力：channels, model providers,           │
│    tools, skills, speech, image generation        │
│                                                  │
│  生命周期：发现 → 加载 → 初始化 → 运行 → 卸载     │
│                                                  │
│  Hook = 中间件模式                                │
│    before/after + MessageReceive/ToolCall/        │
│    Response + onError/onSessionStart/End          │
│                                                  │
│  权限控制 = 分层策略管道                           │
│    全局 → 用户/角色 → 渠道 → 参数                 │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## 课后练习

### 练习1：类型判断
以下场景分别应该使用哪种类型的 Plugin？请说明理由：
1. 一个将所有 Agent 回复翻译成用户首选语言的插件
2. 一个提供 GitHub API 操作的插件
3. 一个检测并拦截垃圾消息的插件
4. 一个从 Vault 加载密钥到环境变量的插件

### 练习2：Hook 设计
设计一个 "对话速率限制" Plugin（Hook-only 类型），要求：
- 限制每个用户每分钟最多发送 20 条消息
- 超限时返回友好提示，而不是硬拒绝
- 管理员用户不受限制
- 写出核心 Hook 注册代码

### 练习3：完整 Plugin 开发
开发一个 "GitHub Issue 管理" Plugin（Hybrid-capability），要求：
- 提供 `create_issue`、`list_issues`、`close_issue` 三个工具
- 使用 `beforeToolCall` Hook 检查用户是否有 GitHub 权限
- 使用 `afterToolCall` Hook 在 Slack 频道发送通知
- 写出完整的目录结构和核心代码

---

> [← 上一课：多渠道接入](13-multi-channel.md) | [下一课：自动化工作流 →](15-automation-workflow.md)
