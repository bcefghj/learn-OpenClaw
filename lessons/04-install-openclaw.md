# 第四课：动手安装 OpenClaw

[← 返回课程目录](../README.md) | [上一课：OpenClaw 是什么](./03-what-is-openclaw.md) | [下一课：第一次对话 →](./05-first-conversation.md)

---

## 本课目标

学完这一课，你将能够：
- 在自己的电脑上成功安装 OpenClaw
- 完成初始配置（选择 LLM Provider、设置 API Key）
- 理解 `openclaw.json` 配置文件的结构
- 排查常见安装问题
- 面试中展示你有实际动手经验

---

## 一、环境要求

### 1.1 硬件要求

OpenClaw 本身是一个轻量级的 Node.js 应用，对硬件要求不高：

| 资源 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 双核 | 四核及以上 |
| 内存 | 2GB 可用 | 4GB+ 可用 |
| 硬盘 | 500MB | 1GB+ |
| 网络 | 能访问 LLM API | 稳定的网络连接 |

### 1.2 软件要求

```
┌──────────────────────────────────────────────────────┐
│                    软件依赖                            │
│                                                      │
│  必须安装:                                            │
│  ┌────────────────────────────────────────┐           │
│  │  Node.js 24（推荐）或 22.16+            │           │
│  │  npm（随 Node.js 一起安装）              │           │
│  └────────────────────────────────────────┘           │
│                                                      │
│  可选安装:                                            │
│  ┌────────────────────────────────────────┐           │
│  │  Git（用于从源码安装）                    │           │
│  │  Docker（用于容器化部署）                 │           │
│  └────────────────────────────────────────┘           │
│                                                      │
│  支持的操作系统:                                       │
│  ┌────────────────────────────────────────┐           │
│  │  macOS 13+ (Ventura 及以上)             │           │
│  │  Windows 10/11                         │           │
│  │  Ubuntu 20.04+ / Debian 11+            │           │
│  │  其他主流 Linux 发行版                   │           │
│  └────────────────────────────────────────┘           │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 二、安装 Node.js

### 2.1 macOS 安装（使用 Homebrew）

**第一步：安装 Homebrew（如果没有的话）**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**第二步：安装 Node.js 24**

```bash
brew install node@24
```

**第三步：验证安装**

```bash
node --version
# 期望输出: v24.x.x

npm --version
# 期望输出: 10.x.x 或更高
```

**如果你已经有旧版本的 Node.js：**

```bash
brew upgrade node
```

> **小贴士：** 推荐使用 **nvm**（Node Version Manager）管理多版本 Node.js：
> ```bash
> # 安装 nvm
> curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
>
> # 安装 Node.js 24
> nvm install 24
> nvm use 24
>
> # 验证
> node --version
> ```

### 2.2 Windows 安装

**方式一：官网下载安装包（推荐新手）**

```
┌──────────────────────────────────────────────────────┐
│                  Windows 安装步骤                      │
│                                                      │
│  1. 打开浏览器，访问 https://nodejs.org               │
│                                                      │
│  2. 下载 LTS 版本（24.x.x）                          │
│     ┌────────────────────────────┐                   │
│     │  [Download Node.js 24 LTS] │ ← 点这个按钮     │
│     └────────────────────────────┘                   │
│                                                      │
│  3. 双击 .msi 安装包                                  │
│     → Next → 勾选 "Add to PATH" → Next → Install    │
│                                                      │
│  4. 打开 PowerShell 或 CMD，验证：                    │
│     > node --version                                 │
│     > npm --version                                  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**方式二：使用 winget（Windows 包管理器）**

```powershell
winget install OpenJS.NodeJS.LTS
```

**方式三：使用 nvm-windows**

```powershell
# 先从 https://github.com/coreybutler/nvm-windows 下载安装 nvm-windows
# 然后：
nvm install 24
nvm use 24
```

### 2.3 Linux 安装（Ubuntu/Debian）

**方式一：使用 NodeSource 仓库（推荐）**

```bash
# 添加 NodeSource 仓库
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -

# 安装 Node.js
sudo apt-get install -y nodejs

# 验证
node --version
npm --version
```

**方式二：使用 nvm**

```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash

# 重新加载 shell 配置
source ~/.bashrc

# 安装 Node.js 24
nvm install 24
nvm use 24
```

---

## 三、安装 OpenClaw

### 3.1 npm 全局安装（推荐）

这是最简单的安装方式，一行命令搞定：

```bash
npm install -g openclaw
```

安装完成后验证：

```bash
openclaw --version
# 期望输出: openclaw vX.X.X
```

```
┌──────────────────────────────────────────────────────┐
│                    安装过程示意                        │
│                                                      │
│  $ npm install -g openclaw                           │
│                                                      │
│  ⠋ Downloading openclaw...                           │
│  ⠙ Installing dependencies...                        │
│  ⠹ Building native modules...                        │
│  ✔ openclaw@X.X.X installed successfully!            │
│                                                      │
│  $ openclaw --version                                │
│  openclaw vX.X.X                                     │
│                                                      │
│  ✅ 安装成功！                                        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 3.2 其他安装方式

**使用 npx（不全局安装，临时使用）：**

```bash
npx openclaw
```

**从源码安装（适合想贡献代码的开发者）：**

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
npm install
npm run build
npm link
```

**使用 Docker：**

```bash
docker run -d --name openclaw \
  -p 3000:3000 \
  -v openclaw-data:/data \
  openclaw/openclaw:latest
```

---

## 四、初始配置：openclaw onboard

### 4.1 运行引导配置

安装完成后，运行引导命令进行首次配置：

```bash
openclaw onboard
```

这个命令会启动一个**交互式引导**，一步步带你完成配置：

```
┌──────────────────────────────────────────────────────────────┐
│                  openclaw onboard 引导流程                     │
│                                                              │
│  $ openclaw onboard                                          │
│                                                              │
│  🐾 Welcome to OpenClaw!                                     │
│  Let's set up your personal AI assistant.                    │
│                                                              │
│  ┌─ Step 1/4: Choose LLM Provider ────────────────────┐      │
│  │                                                    │      │
│  │  Which LLM would you like to use?                  │      │
│  │                                                    │      │
│  │  > OpenAI (GPT-4o, GPT-4.5)                       │      │
│  │    Anthropic (Claude 4)                            │      │
│  │    Google (Gemini 2.5)                             │      │
│  │    DeepSeek (DeepSeek R2)                          │      │
│  │    Ollama (Local models)                           │      │
│  │    Custom endpoint                                 │      │
│  │                                                    │      │
│  └────────────────────────────────────────────────────┘      │
│                          ↓                                   │
│  ┌─ Step 2/4: Enter API Key ──────────────────────────┐      │
│  │                                                    │      │
│  │  Enter your OpenAI API key:                        │      │
│  │  > sk-proj-xxxxxxxxxxxxxxxxxxxx                    │      │
│  │                                                    │      │
│  │  ✔ API key verified successfully!                  │      │
│  │                                                    │      │
│  └────────────────────────────────────────────────────┘      │
│                          ↓                                   │
│  ┌─ Step 3/4: Choose Default Model ───────────────────┐      │
│  │                                                    │      │
│  │  Select default model:                             │      │
│  │                                                    │      │
│  │  > gpt-4o (recommended)                            │      │
│  │    gpt-4.5-preview                                 │      │
│  │    gpt-4o-mini (cheaper)                           │      │
│  │                                                    │      │
│  └────────────────────────────────────────────────────┘      │
│                          ↓                                   │
│  ┌─ Step 4/4: Basic Settings ─────────────────────────┐      │
│  │                                                    │      │
│  │  Assistant name: OpenClaw                          │      │
│  │  Language: zh-CN                                   │      │
│  │  Enable memory: Yes                                │      │
│  │                                                    │      │
│  └────────────────────────────────────────────────────┘      │
│                          ↓                                   │
│  ✅ Configuration saved to ~/.openclaw/openclaw.json         │
│  🚀 Run 'openclaw' to start chatting!                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 LLM Provider 选择指南

| Provider | 模型 | 价格 | 适合谁 |
|----------|------|------|--------|
| **OpenAI** | GPT-4o, GPT-4.5 | 中等 | 大多数用户，综合能力强 |
| **Anthropic** | Claude 4 Sonnet/Opus | 中等 | 喜欢长文本处理和编程 |
| **Google** | Gemini 2.5 Pro | 低 | 有 Google Cloud 账号 |
| **DeepSeek** | DeepSeek R2/V3 | 极低 | 预算有限，性价比最高 |
| **Ollama** | Llama 4, Qwen 3... | 免费 | 想本地运行，数据不出电脑 |

> **零基础推荐：** 如果你不知道选什么，选 **OpenAI + GPT-4o** 或 **DeepSeek + DeepSeek R2**（性价比最高）。

### 4.3 如何获取 API Key？

**以 OpenAI 为例：**

```
┌──────────────────────────────────────────────────────┐
│              获取 OpenAI API Key 步骤                  │
│                                                      │
│  1. 访问 https://platform.openai.com                 │
│                                                      │
│  2. 注册/登录账号                                     │
│                                                      │
│  3. 点击左侧 "API Keys"                              │
│                                                      │
│  4. 点击 "Create new secret key"                     │
│     ┌────────────────────────────────────┐           │
│     │ Name: my-openclaw-key              │           │
│     │ [Create secret key]                │           │
│     └────────────────────────────────────┘           │
│                                                      │
│  5. 复制 key（以 sk-proj- 开头）                      │
│     ⚠️ 这个 key 只显示一次！请妥善保管！               │
│                                                      │
│  6. 充值余额（最低 $5）                               │
│     Settings → Billing → Add payment method          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**以 DeepSeek 为例：**

```
┌──────────────────────────────────────────────────────┐
│              获取 DeepSeek API Key 步骤               │
│                                                      │
│  1. 访问 https://platform.deepseek.com               │
│                                                      │
│  2. 注册/登录（支持手机号注册）                        │
│                                                      │
│  3. 点击 "API Keys" → "Create API Key"               │
│                                                      │
│  4. 复制生成的 key                                    │
│                                                      │
│  5. 充值（新用户通常有免费额度）                       │
│                                                      │
│  💡 DeepSeek 的价格只有 OpenAI 的 1/10 左右           │
│     非常适合学习和实验                                 │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 五、配置文件详解：openclaw.json

### 5.1 配置文件位置

`openclaw onboard` 完成后，配置文件保存在：

```
~/.openclaw/openclaw.json

macOS:   /Users/你的用户名/.openclaw/openclaw.json
Windows: C:\Users\你的用户名\.openclaw\openclaw.json
Linux:   /home/你的用户名/.openclaw/openclaw.json
```

### 5.2 配置文件结构

```json
{
  "version": "1.0",
  "assistant": {
    "name": "OpenClaw",
    "language": "zh-CN",
    "personality": "helpful, concise"
  },
  "llm": {
    "provider": "openai",
    "model": "gpt-4o",
    "apiKey": "sk-proj-xxxxxxxxxxxxxxxx",
    "temperature": 0.7,
    "maxTokens": 4096
  },
  "memory": {
    "enabled": true,
    "shortTerm": {
      "maxMessages": 50
    },
    "longTerm": {
      "enabled": true,
      "storage": "local"
    }
  },
  "skills": [],
  "channels": {
    "cli": { "enabled": true },
    "dashboard": { "enabled": true, "port": 3000 }
  }
}
```

### 5.3 重要配置项说明

```
┌──────────────────────────────────────────────────────────────┐
│                    配置项速查表                                │
│                                                              │
│  配置路径                      │ 说明             │ 建议值    │
│  ─────────────────────────────┼──────────────────┼──────────│
│  assistant.name               │ 助手名称          │ 自定义    │
│  assistant.language           │ 默认语言          │ zh-CN    │
│  llm.provider                 │ LLM 供应商        │ openai   │
│  llm.model                    │ 默认模型          │ gpt-4o   │
│  llm.apiKey                   │ API 密钥          │ 你的 key │
│  llm.temperature              │ 创造力(0-1)       │ 0.7      │
│  llm.maxTokens                │ 最大输出长度       │ 4096     │
│  memory.enabled               │ 启用记忆          │ true     │
│  memory.longTerm.enabled      │ 启用长期记忆       │ true     │
│  channels.dashboard.port      │ Dashboard 端口    │ 3000     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**temperature 参数详解：**

```
temperature = 0.0          temperature = 0.7          temperature = 1.0
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│  确定性回答    │          │  平衡模式     │          │  创造性模式    │
│  每次回答相同  │          │  有变化但可控  │          │  高度随机     │
│  适合：       │          │  适合：       │          │  适合：       │
│  - 事实查询   │          │  - 日常对话    │          │  - 创意写作   │
│  - 代码生成   │          │  - 通用助手    │          │  - 头脑风暴   │
└──────────────┘          └──────────────┘          └──────────────┘
```

> **面试考点：** temperature 参数的作用是什么？
> 答：temperature 控制 LLM 输出的**随机性/创造性**。值为 0 时输出最确定（适合代码、事实回答），值越高越随机有创意（适合写作、头脑风暴）。通常默认 0.7 是比较好的平衡值。

---

## 六、常见安装问题排查

### 6.1 问题排查速查表

```
┌──────────────────────────────────────────────────────────────┐
│                    常见问题排查                                │
│                                                              │
│  问题                          │ 解决方案                     │
│  ─────────────────────────────┼────────────────────────────  │
│  "command not found: node"    │ Node.js 未安装或未加入 PATH   │
│                               │ → 重新安装或 source ~/.zshrc │
│  ─────────────────────────────┼────────────────────────────  │
│  "command not found: openclaw"│ 全局安装失败或 PATH 问题      │
│                               │ → npm install -g openclaw    │
│                               │ → 或检查 npm bin -g 路径     │
│  ─────────────────────────────┼────────────────────────────  │
│  npm WARN EBADENGINE          │ Node.js 版本太低             │
│                               │ → 升级到 22.16+ 或 24        │
│  ─────────────────────────────┼────────────────────────────  │
│  EACCES permission denied     │ npm 全局安装权限不足          │
│                               │ → 见 6.2 解决方案            │
│  ─────────────────────────────┼────────────────────────────  │
│  API key verification failed  │ API Key 无效或已过期         │
│                               │ → 检查 Key 和账户余额        │
│  ─────────────────────────────┼────────────────────────────  │
│  网络连接超时                  │ 无法访问 LLM API             │
│                               │ → 检查网络/代理设置          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 npm 权限问题解决

**macOS/Linux 上遇到 `EACCES` 错误：**

```bash
# 方案一：修改 npm 全局目录（推荐）
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'

# 添加到 PATH（macOS/zsh 用户）
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc

# 添加到 PATH（Linux/bash 用户）
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# 重新安装 OpenClaw
npm install -g openclaw

# 方案二：使用 sudo（不太推荐但简单）
sudo npm install -g openclaw
```

### 6.3 Node.js 版本检查

```bash
# 检查当前版本
node --version

# 如果版本低于 22.16，需要升级
# macOS:
brew upgrade node

# 使用 nvm:
nvm install 24
nvm use 24
nvm alias default 24
```

### 6.4 网络问题（中国大陆用户）

```bash
# 设置 npm 镜像源
npm config set registry https://registry.npmmirror.com

# 重新安装
npm install -g openclaw

# 如果 LLM API 访问有问题，可以在配置文件中设置代理
# 或者使用国内的 LLM（如 DeepSeek、Qwen）
```

---

## 七、验证安装成功

完成安装和配置后，运行以下命令验证一切正常：

```bash
# 1. 检查版本
openclaw --version

# 2. 检查配置
openclaw config show

# 3. 测试连接
openclaw ping
```

期望看到的输出：

```
┌──────────────────────────────────────────────────────┐
│                  验证安装成功                          │
│                                                      │
│  $ openclaw --version                                │
│  openclaw v1.x.x                                     │
│  ✅ 版本正确                                          │
│                                                      │
│  $ openclaw config show                              │
│  Provider: openai                                    │
│  Model: gpt-4o                                       │
│  Memory: enabled                                     │
│  ✅ 配置正确                                          │
│                                                      │
│  $ openclaw ping                                     │
│  🏓 Pong! LLM connection successful (234ms)          │
│  ✅ 连接正常                                          │
│                                                      │
│  一切就绪！进入下一课开始对话吧！                       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

> **面试考点：** 安装 OpenClaw 需要哪些环境依赖？
> 答：OpenClaw 基于 Node.js 运行，需要 **Node.js 24（推荐）或 22.16 以上版本**。安装方式是 `npm install -g openclaw`，然后通过 `openclaw onboard` 进行引导配置，包括选择 LLM Provider、配置 API Key、选择默认模型等。配置信息保存在 `~/.openclaw/openclaw.json` 中。

---

## 八、本课要点回顾

```
┌──────────────────────────────────────────────────────┐
│                    知识点总结                          │
│                                                      │
│  1. 环境要求                                          │
│     Node.js 24（推荐）或 22.16+                       │
│                                                      │
│  2. 安装命令                                          │
│     npm install -g openclaw                          │
│                                                      │
│  3. 初始配置                                          │
│     openclaw onboard → 选 Provider → 填 API Key      │
│                                                      │
│  4. 配置文件                                          │
│     ~/.openclaw/openclaw.json                        │
│     包含 LLM 设置、记忆设置、渠道设置                   │
│                                                      │
│  5. 常见问题                                          │
│     权限问题用 ~/.npm-global 解决                     │
│     版本问题用 nvm 管理                               │
│     网络问题用镜像源或国内 LLM                         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 九、课后练习

### 练习 1：动手实操（实践题）

在你的电脑上完成 OpenClaw 的安装，并截图证明：
1. `node --version` 的输出
2. `openclaw --version` 的输出
3. `openclaw config show` 的输出

### 练习 2：配置理解（选择题）

`openclaw.json` 中的 `temperature` 设置为 0.2，最可能的使用场景是？

A. 创意写作助手
B. 代码生成助手
C. 故事创作助手
D. 头脑风暴助手

<details>
<summary>点击查看答案</summary>

**答案：B**

解析：temperature = 0.2 表示较低的随机性，输出更确定、更精准。这种设置适合需要准确性的场景，如代码生成、事实查询、数据分析等。创意写作和头脑风暴需要更高的 temperature（0.8-1.0）来增加多样性。

</details>

### 练习 3：问题排查（情景题）

你的同事在 macOS 上运行 `npm install -g openclaw` 时遇到了以下错误：

```
npm ERR! Error: EACCES: permission denied, mkdir '/usr/local/lib/node_modules/openclaw'
```

请给出至少两种解决方案。

<details>
<summary>点击查看参考答案</summary>

**方案一：修改 npm 全局安装目录（推荐）**

```bash
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
npm install -g openclaw
```

**方案二：使用 sudo**

```bash
sudo npm install -g openclaw
```

**方案三：使用 nvm 管理 Node.js（根本解决）**

使用 nvm 安装的 Node.js 不会有权限问题，因为 nvm 将 Node.js 安装在用户目录下。

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
source ~/.zshrc
nvm install 24
npm install -g openclaw
```

**方案四：修改目录权限（不太推荐）**

```bash
sudo chown -R $(whoami) /usr/local/lib/node_modules
npm install -g openclaw
```

</details>

---

[← 返回课程目录](../README.md) | [上一课：OpenClaw 是什么](./03-what-is-openclaw.md) | [下一课：第一次对话 →](./05-first-conversation.md)
