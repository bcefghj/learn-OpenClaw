# 第五课：第一次对话——Hello OpenClaw！

[← 返回课程目录](../README.md) | [上一课：安装 OpenClaw](./04-install-openclaw.md) | [下一课：Gateway 架构 →](./06-gateway-architecture.md)

---

## 本课目标

学完这一课，你将能够：
- 使用 CLI 模式与 OpenClaw 进行对话
- 使用 Dashboard 进行可视化管理
- 理解 OpenClaw 的返回结果结构
- 安装第一个 Skill 并使用它
- 用 OpenClaw 完成一个实际任务
- 在面试中展示你有真实的 OpenClaw 使用经验

---

## 一、CLI 模式：命令行交互

### 1.1 启动 OpenClaw

打开终端，输入：

```bash
openclaw
```

你会看到欢迎界面：

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│   $ openclaw                                         │
│                                                      │
│   🐾 OpenClaw v1.x.x                                │
│   ──────────────────────────────────                 │
│   Provider: openai | Model: gpt-4o                   │
│   Memory: enabled | Skills: 0 loaded                 │
│                                                      │
│   Type your message, or /help for commands.          │
│   Type /exit to quit.                                │
│                                                      │
│   You >                                              │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 1.2 发送第一条消息

试试输入：

```
You > 你好，请做一下自我介绍
```

OpenClaw 的回复可能是这样的：

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  You > 你好，请做一下自我介绍                          │
│                                                      │
│  🐾 OpenClaw >                                       │
│                                                      │
│  你好！我是 OpenClaw，你的个人 AI 助手。               │
│                                                      │
│  我可以帮你做很多事情：                                │
│  - 🔍 搜索互联网信息                                  │
│  - 📁 读写本地文件                                    │
│  - 💻 执行代码                                        │
│  - 📧 发送邮件和消息                                   │
│  - 📅 管理日程                                        │
│  - ... 以及更多（取决于安装的 Skills）                  │
│                                                      │
│  有什么我可以帮你的吗？                                │
│                                                      │
│  ─────────────────────────────────────────            │
│  tokens: 156 | latency: 823ms | model: gpt-4o       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 1.3 理解返回结果

注意回复底部的信息栏：

```
tokens: 156 | latency: 823ms | model: gpt-4o
```

| 字段 | 含义 | 为什么重要 |
|------|------|-----------|
| **tokens** | 这次回复消耗的 token 数量 | 直接影响费用 |
| **latency** | 响应延迟（毫秒） | 体现 Agent 的响应速度 |
| **model** | 使用的 LLM 模型 | 不同模型能力和价格不同 |

当 Agent 调用了工具时，你会看到更详细的信息：

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  You > 今天北京天气怎么样？                            │
│                                                      │
│  🔧 [Tool Call] web_search("北京 今天 天气")          │
│  ✅ [Tool Result] 搜索返回 5 条结果 (342ms)           │
│                                                      │
│  🐾 OpenClaw >                                       │
│                                                      │
│  今天北京天气晴朗，气温 12°C ~ 26°C，西北风 2 级。     │
│  空气质量良好，PM2.5 指数 45。                         │
│  适合户外活动，建议穿轻薄外套。                        │
│                                                      │
│  ─────────────────────────────────────────            │
│  tokens: 289 | latency: 1.2s | model: gpt-4o        │
│  tools: web_search x1                                │
│                                                      │
└──────────────────────────────────────────────────────┘
```

可以看到，Agent 先调用了 `web_search` 工具，拿到搜索结果后再组织回答——这就是上一课学的 **ReAct 循环** 在实际运行！

---

## 二、Dashboard 模式：可视化管理

### 2.1 启动 Dashboard

```bash
openclaw dashboard
```

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  $ openclaw dashboard                                │
│                                                      │
│  🐾 OpenClaw Dashboard starting...                   │
│  ✅ Server running at http://localhost:3000           │
│                                                      │
│  Open your browser and navigate to:                  │
│  👉 http://localhost:3000                             │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 2.2 Dashboard 界面概览

打开浏览器访问 `http://localhost:3000`：

```
┌──────────────────────────────────────────────────────────────┐
│  🐾 OpenClaw Dashboard                              [设置]   │
├──────────┬───────────────────────────────────────────────────┤
│          │                                                   │
│  对话列表  │              对话区域                              │
│          │                                                   │
│ ┌──────┐ │  ┌─────────────────────────────────────────┐     │
│ │ 新对话 │ │  │  🐾 你好！有什么可以帮你的？              │     │
│ ├──────┤ │  └─────────────────────────────────────────┘     │
│ │ 对话1 │ │                                                   │
│ │ 对话2 │ │                                                   │
│ │ 对话3 │ │                                                   │
│ │ ...  │ │                                                   │
│ │      │ │                                                   │
│ │      │ │                                                   │
│ ├──────┤ │  ┌─────────────────────────────────────────┐     │
│ │Skills│ │  │  输入消息...                      [发送] │     │
│ │Memory│ │  └─────────────────────────────────────────┘     │
│ │设置   │ │                                                   │
│ └──────┘ │                                                   │
│          │                                                   │
└──────────┴───────────────────────────────────────────────────┘
```

Dashboard 的主要功能：

| 功能区 | 说明 |
|--------|------|
| **对话列表** | 查看和管理所有历史对话 |
| **对话区域** | 和 Agent 实时交互 |
| **Skills 管理** | 浏览、安装、卸载 Skills |
| **Memory 查看** | 查看 Agent 记住了什么 |
| **设置** | 修改 LLM、模型、渠道等配置 |

> **CLI vs Dashboard 怎么选？**
> - **CLI**：适合快速提问和脚本自动化，开发者首选
> - **Dashboard**：适合日常使用和管理，可视化操作更直观

---

## 三、基础命令一览表

### 3.1 CLI 内置命令

在 CLI 模式下，以 `/` 开头的是内置命令：

```
┌──────────────────────────────────────────────────────────────┐
│                    CLI 命令速查表                              │
│                                                              │
│  命令              │ 说明                    │ 示例           │
│  ─────────────────┼─────────────────────────┼──────────────  │
│  /help            │ 显示帮助信息             │ /help          │
│  /exit            │ 退出 OpenClaw            │ /exit          │
│  /clear           │ 清空当前对话             │ /clear         │
│  /model           │ 切换 LLM 模型           │ /model gpt-4.5 │
│  /skills          │ 列出已安装的 Skills      │ /skills        │
│  /skill install   │ 安装一个 Skill          │ /skill install  │
│                   │                         │ web-search     │
│  /skill remove    │ 卸载一个 Skill          │ /skill remove   │
│                   │                         │ web-search     │
│  /memory          │ 查看记忆状态             │ /memory        │
│  /memory clear    │ 清除所有记忆             │ /memory clear  │
│  /config          │ 查看当前配置             │ /config        │
│  /export          │ 导出当前对话             │ /export chat   │
│  /verbose         │ 开启详细模式(显示推理)    │ /verbose on    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 终端命令（在终端中直接使用）

```bash
# 启动交互式对话
openclaw

# 启动 Dashboard
openclaw dashboard

# 直接提问（不进入交互模式）
openclaw ask "今天天气怎么样？"

# 查看版本
openclaw --version

# 查看帮助
openclaw --help

# 查看配置
openclaw config show

# 修改配置
openclaw config set llm.model gpt-4.5

# 测试 LLM 连接
openclaw ping

# 引导配置
openclaw onboard

# 安装 Skill
openclaw skill install <skill-name>

# 列出可用 Skills
openclaw skill list

# 搜索 Skills
openclaw skill search <keyword>
```

---

## 四、Skills 初体验：安装第一个技能

### 4.1 什么是 Skills？

上一课说过，Skills 就像手机上的 App——每安装一个 Skill，Agent 就多一项能力。

### 4.2 浏览可用的 Skills

```bash
openclaw skill search web
```

```
┌──────────────────────────────────────────────────────┐
│                  搜索结果: "web"                       │
│                                                      │
│  1. web-search         ★★★★★  (12.3k installs)      │
│     搜索互联网内容，获取实时信息                        │
│                                                      │
│  2. web-browse         ★★★★☆  (8.7k installs)       │
│     浏览和抓取网页内容                                 │
│                                                      │
│  3. web-screenshot     ★★★★☆  (5.2k installs)       │
│     对网页截图                                        │
│                                                      │
│  4. web-monitor        ★★★☆☆  (2.1k installs)       │
│     监控网页变化并通知                                 │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 4.3 安装 web-search Skill

```bash
openclaw skill install web-search
```

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  $ openclaw skill install web-search                 │
│                                                      │
│  📦 Installing web-search...                         │
│  ✅ web-search@1.2.0 installed successfully!         │
│                                                      │
│  New tools available:                                │
│  - web_search: 搜索互联网内容                         │
│  - web_news: 搜索最新新闻                             │
│                                                      │
│  Try it: "帮我搜索一下最近的 AI 新闻"                  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 4.4 安装更多 Skills

```bash
# 安装文件操作技能
openclaw skill install file-ops

# 安装代码执行技能
openclaw skill install code-runner

# 查看已安装的 Skills
openclaw skill list
```

```
┌──────────────────────────────────────────────────────┐
│                  已安装的 Skills                       │
│                                                      │
│  ┌─────────────┬────────┬──────────────────────┐     │
│  │ Skill       │ 版本   │ 提供的工具             │     │
│  ├─────────────┼────────┼──────────────────────┤     │
│  │ web-search  │ 1.2.0  │ web_search, web_news │     │
│  │ file-ops    │ 2.0.1  │ file_read, file_write│     │
│  │             │        │ file_list, file_delete│     │
│  │ code-runner │ 1.5.0  │ run_python, run_js   │     │
│  │             │        │ run_shell             │     │
│  └─────────────┴────────┴──────────────────────┘     │
│                                                      │
│  共 3 个 Skills, 8 个工具可用                          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 五、实战：用 OpenClaw 完成一个任务

### 5.1 任务一：搜索网页信息

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  You > 帮我搜索一下 2026 年最受欢迎的编程语言排行             │
│                                                              │
│  🔧 [Tool Call] web_search("2026 最受欢迎编程语言排行")       │
│  ✅ [Tool Result] 返回 8 条结果 (456ms)                      │
│                                                              │
│  🐾 OpenClaw >                                               │
│                                                              │
│  根据 TIOBE 2026 年 3 月的编程语言排行榜：                    │
│                                                              │
│  | 排名 | 语言       | 份额   | 趋势  |                     │
│  |------|-----------|--------|-------|                     │
│  | 1    | Python    | 28.3%  | ↑     |                     │
│  | 2    | JavaScript| 15.7%  | →     |                     │
│  | 3    | Java      | 12.1%  | ↓     |                     │
│  | 4    | TypeScript| 8.9%   | ↑     |                     │
│  | 5    | Rust      | 6.2%   | ↑↑    |                     │
│                                                              │
│  Python 连续三年蝉联第一，主要得益于 AI/ML 领域的爆发。       │
│  Rust 增长最快，在系统编程领域越来越受欢迎。                   │
│                                                              │
│  ─────────────────────────────────────────────               │
│  tokens: 412 | latency: 2.1s | tools: web_search x1        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 任务二：操作本地文件

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  You > 帮我在桌面创建一个 notes.md 文件，写入今天的学习笔记    │
│                                                              │
│  🔧 [Tool Call] file_write(                                  │
│       path: "~/Desktop/notes.md",                            │
│       content: "# 学习笔记 - 2026-03-27\n\n..."             │
│     )                                                        │
│  ✅ [Tool Result] 文件创建成功 (12ms)                         │
│                                                              │
│  🐾 OpenClaw >                                               │
│                                                              │
│  已在桌面创建 notes.md 文件，内容如下：                        │
│                                                              │
│  ```markdown                                                 │
│  # 学习笔记 - 2026-03-27                                     │
│                                                              │
│  ## 今日学习内容                                              │
│  - OpenClaw 安装和基础使用                                    │
│  - CLI 模式和 Dashboard 模式                                  │
│  - Skills 系统初体验                                          │
│                                                              │
│  ## 待办事项                                                  │
│  - [ ] 阅读 OpenClaw 源码                                    │
│  - [ ] 尝试开发自定义 Skill                                   │
│  ```                                                         │
│                                                              │
│  ─────────────────────────────────────────────               │
│  tokens: 198 | latency: 1.8s | tools: file_write x1        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 5.3 任务三：多步骤复合任务

这个例子展示了 Agent 的 ReAct 多轮循环：

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  You > 帮我搜索 OpenClaw 最新版本的更新内容，                  │
│        总结成中文，保存到 ~/Desktop/openclaw-updates.md       │
│                                                              │
│  🔧 [Tool Call #1] web_search("OpenClaw latest release      │
│     changelog 2026")                                         │
│  ✅ [Tool Result #1] 返回 6 条结果 (521ms)                   │
│                                                              │
│  🔧 [Tool Call #2] web_search("OpenClaw GitHub releases")   │
│  ✅ [Tool Result #2] 返回 4 条结果 (398ms)                   │
│                                                              │
│  🔧 [Tool Call #3] file_write(                               │
│       path: "~/Desktop/openclaw-updates.md",                 │
│       content: "# OpenClaw 最新版本更新摘要\n\n..."          │
│     )                                                        │
│  ✅ [Tool Result #3] 文件创建成功 (15ms)                      │
│                                                              │
│  🐾 OpenClaw >                                               │
│                                                              │
│  已完成！做了以下三件事：                                      │
│                                                              │
│  1. 搜索了 OpenClaw 最新版本信息                              │
│  2. 将更新内容翻译总结为中文                                   │
│  3. 保存到 ~/Desktop/openclaw-updates.md                     │
│                                                              │
│  主要更新包括：                                               │
│  - 新增 Canvas 协作模式                                       │
│  - 支持 Claude 4 和 Gemini 2.5 Pro                           │
│  - Memory 系统性能提升 40%                                    │
│  - 新增 15 个官方 Skills                                      │
│                                                              │
│  ─────────────────────────────────────────────               │
│  tokens: 687 | latency: 4.3s                                │
│  tools: web_search x2, file_write x1                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

注意这次 Agent 自主执行了**三步操作**——两次搜索和一次文件写入，这就是 ReAct 循环的真实体现。

---

## 六、开启详细模式：观察 Agent 的思考过程

### 6.1 用 /verbose 命令

在 CLI 中输入 `/verbose on` 可以看到 Agent 的完整推理过程：

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  You > /verbose on                                           │
│  ✅ Verbose mode enabled. You can see the agent's thinking.  │
│                                                              │
│  You > 3 的 15 次方是多少？                                   │
│                                                              │
│  💭 [Thought] 用户问 3^15 的值。这是一个数学计算，           │
│     我可以直接计算，也可以用 code-runner 确保精确。            │
│     为了保证准确，我用 code-runner 执行计算。                  │
│                                                              │
│  🔧 [Action] run_python("print(3 ** 15)")                   │
│                                                              │
│  👀 [Observation] 输出: 14348907                             │
│                                                              │
│  💭 [Thought] 计算结果是 14348907，任务完成。                 │
│                                                              │
│  🐾 OpenClaw >                                               │
│                                                              │
│  3 的 15 次方 = **14,348,907**                               │
│                                                              │
│  ─────────────────────────────────────────────               │
│  tokens: 203 | latency: 1.5s | tools: run_python x1        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

在详细模式下，你能清楚地看到：
- **Thought**：Agent 在想什么
- **Action**：Agent 决定做什么
- **Observation**：Agent 看到了什么结果

这对于**理解 Agent 原理**和**调试问题**非常有帮助。

> **面试考点：** OpenClaw 的 verbose 模式有什么用？
> 答：verbose 模式会展示 Agent 完整的 **ReAct 推理过程**——包括 Thought（思考）、Action（行动）和 Observation（观察）三个阶段。这对于调试 Agent 行为、理解它为什么做出某个决策、以及排查工具调用错误非常有帮助。

---

## 七、本课要点回顾

```
┌──────────────────────────────────────────────────────┐
│                    知识点总结                          │
│                                                      │
│  1. 两种交互模式                                      │
│     CLI: openclaw（快速交互）                         │
│     Dashboard: openclaw dashboard（可视化管理）       │
│                                                      │
│  2. 返回结果结构                                      │
│     tokens / latency / model / tools                 │
│                                                      │
│  3. 基础命令                                          │
│     /help /clear /model /skills /memory /verbose     │
│                                                      │
│  4. Skills 系统                                       │
│     search → install → use                           │
│     每个 Skill 提供一组工具                            │
│                                                      │
│  5. 实战能力                                          │
│     搜索网页 / 操作文件 / 多步骤复合任务               │
│     Agent 自主运行 ReAct 循环完成任务                  │
│                                                      │
│  6. Verbose 模式                                     │
│     观察 Thought → Action → Observation 完整流程     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 八、课后练习

### 练习 1：动手实操（实践题）

启动 OpenClaw，完成以下任务（每个任务截图你和 Agent 的对话）：

1. 让 OpenClaw 做一下自我介绍
2. 安装 `web-search` Skill，然后让 OpenClaw 搜索一条新闻
3. 开启 `/verbose on`，让 OpenClaw 做一道数学题，观察它的思考过程

### 练习 2：概念理解（选择题）

当 OpenClaw 处理"帮我搜索最新新闻并保存到文件"这个请求时，它至少需要安装哪些 Skills？

A. 只需要 web-search
B. 只需要 file-ops
C. 需要 web-search 和 file-ops
D. 不需要任何 Skills，OpenClaw 自带这些能力

<details>
<summary>点击查看答案</summary>

**答案：C**

解析：这个任务需要两个操作——搜索网页和写入文件。`web-search` Skill 提供搜索互联网的能力（`web_search` 工具），`file-ops` Skill 提供文件操作的能力（`file_write` 工具）。缺少任何一个，Agent 都无法完成完整的任务。Agent 的能力完全取决于它安装了哪些 Skills——这就是 Skills 插件化设计的精髓。

</details>

### 练习 3：面试模拟（开放题）

面试官问："你实际使用过 OpenClaw 吗？能说说你的使用体验吗？"

请基于本课学到的内容，组织一段有说服力的回答。

<details>
<summary>点击查看参考答案</summary>

**参考答案要点：**

"是的，我在本地安装并使用过 OpenClaw。

安装过程很简单，`npm install -g openclaw` 一行命令就搞定了。通过 `openclaw onboard` 引导配置了 LLM Provider 和 API Key。

OpenClaw 支持两种交互模式——CLI 模式适合快速提问和脚本自动化，Dashboard 模式提供了 Web 界面方便日常管理。

我觉得最有意思的是它的 **Skills 系统**。Skills 就像手机上的 App，每安装一个 Skill，Agent 就多一项能力。比如我安装了 `web-search` 和 `file-ops` 两个 Skills 后，就可以让 Agent 帮我搜索网上的资料并自动保存到本地文件——整个过程 Agent 会自主进行多轮 ReAct 循环，先搜索、再整理、最后写入文件。

我还使用了 `/verbose` 模式观察 Agent 的推理过程，能清楚地看到每一步的 Thought、Action 和 Observation，这对理解 Agent 的工作原理非常有帮助。

总体来说，OpenClaw 的上手体验比 LangChain 这类开发框架简单得多，但又比直接用 ChatGPT 灵活得多。它真正实现了从'聊天'到'执行'的跨越——不只是回答你的问题，而是帮你把事情做了。"

</details>

---

## 恭喜你！

你已经完成了 OpenClaw 入门的前五课！现在你已经：
- 理解了 AI、大模型和 Agent 的基础概念
- 掌握了 Tool Calling 和 ReAct 的核心原理
- 了解了 OpenClaw 的定位和架构
- 在本地安装并运行了 OpenClaw
- 完成了第一次实际对话

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│              🎉 入门阶段完成！                         │
│                                                      │
│   ┌─────────┐                                        │
│   │ 第一课   │ ✅ AI / LLM / Agent 基础概念           │
│   ├─────────┤                                        │
│   │ 第二课   │ ✅ Tool Calling 与 ReAct               │
│   ├─────────┤                                        │
│   │ 第三课   │ ✅ OpenClaw 介绍                       │
│   ├─────────┤                                        │
│   │ 第四课   │ ✅ 安装 OpenClaw                       │
│   ├─────────┤                                        │
│   │ 第五课   │ ✅ 第一次对话（当前）                    │
│   └─────────┘                                        │
│                                                      │
│   接下来进入进阶阶段：                                 │
│   第六课：Gateway 架构深入分析                         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

[← 返回课程目录](../README.md) | [上一课：安装 OpenClaw](./04-install-openclaw.md) | [下一课：Gateway 架构 →](./06-gateway-architecture.md)
