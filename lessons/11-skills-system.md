# 第11课：Skills 系统与 ClawHub 生态

> **第三阶段：进阶实战** | [← 上一课](10-conversation-management.md) | [下一课 →](12-mcp-protocol.md)

---

## 本课目标

理解 OpenClaw 三层能力体系（Tools → Skills → Plugins）的设计哲学，掌握 Skills 的编写方式和 ClawHub 生态的使用方法。

---

![漫画：Skills就是AI的技能包](../comics/comic-05-skills.png)

## 一、三层能力体系全景

想象你在组装一台电脑：

- **Tools** = 各个零件（CPU、内存、硬盘）—— 最基础的功能单元
- **Skills** = 驱动程序 —— 告诉系统如何使用这些零件
- **Plugins** = 整套解决方案 —— 打包好的功能包，开箱即用

```
┌─────────────────────────────────────────────────┐
│                  OpenClaw Agent                  │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │            Plugins（功能包）                │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │         Skills（Markdown 指令）      │  │  │
│  │  │  ┌───────────────────────────────┐  │  │  │
│  │  │  │      Tools（类型化函数）        │  │  │  │
│  │  │  │                               │  │  │  │
│  │  │  │  file_read()  shell_exec()    │  │  │  │
│  │  │  │  web_fetch()  send_msg()      │  │  │  │
│  │  │  │  ...约20个内置工具...           │  │  │  │
│  │  │  └───────────────────────────────┘  │  │  │
│  │  │                                     │  │  │
│  │  │  SKILL.md → 注入 system prompt      │  │  │
│  │  │  教会 Agent 如何组合使用 Tools       │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  │                                           │  │
│  │  channels + model providers + hooks + ... │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 二、Tools：基础能力层

Tools 是 Agent 可以调用的**类型化函数**，每个 Tool 有明确的输入参数和输出格式。

### 内置 Tools（约20个）

| 类别 | 工具名 | 功能 |
|------|--------|------|
| 文件操作 | `file_read`, `file_write`, `file_edit` | 读写编辑文件 |
| 系统执行 | `shell_exec` | 执行 Shell 命令 |
| 网络请求 | `web_fetch` | 抓取网页内容 |
| 搜索 | `web_search`, `grep`, `glob` | 搜索网络和文件 |
| 消息 | `send_message` | 发送消息 |
| 图像 | `generate_image` | 生成图片 |
| 其他 | `read_lints`, `todo_write` 等 | 辅助功能 |

### Tool 的定义格式

```json
{
  "name": "web_fetch",
  "description": "Fetch content from a URL and return readable text",
  "parameters": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "description": "The URL to fetch"
      }
    },
    "required": ["url"]
  }
}
```

> **面试考点**：Tools 和普通 API 的区别是什么？
> - Tools 是**面向 Agent 设计**的，有自然语言描述帮助 Agent 理解何时使用
> - Tools 的参数是**类型化**的（JSON Schema），Agent 可以自动构造调用参数
> - Tools 通过统一接口暴露，Agent 不需要知道底层实现

---

## 三、Skills：知识注入层

Skills 是 OpenClaw 最有特色的设计。一个 Skill 就是一个 **SKILL.md** 文件，它被注入到 Agent 的 system prompt 中，教会 Agent 一项新能力。

### 为什么用 Markdown？

把 Agent 想象成一个新入职的实习生：
- **Tools** 是办公桌上的工具（电脑、打印机、电话）
- **Skills** 是操作手册 —— 用自然语言写的指南，告诉实习生如何用这些工具完成具体任务

Markdown 的优势：
1. **人类可读可写** —— 不需要编程知识就能创建
2. **LLM 原生友好** —— 大模型对自然语言指令的理解最好
3. **版本管理方便** —— 纯文本文件，Git 友好

### SKILL.md 完整示例

以下是一个 "代码审查" Skill 的完整示例：

```markdown
# Code Review Skill

You are a senior code reviewer. When the user asks you to review code,
follow these steps:

## Tools Available
- `file_read`: Read source files
- `grep`: Search for patterns in code
- `shell_exec`: Run linters or tests

## Review Process

1. **Read the file** using `file_read` to understand the full context
2. **Check for common issues**:
   - Unused imports
   - Missing error handling
   - Security vulnerabilities (SQL injection, XSS, etc.)
   - Performance anti-patterns
3. **Run the linter** using `shell_exec` with the appropriate command
4. **Provide feedback** in this format:

### Feedback Format
- 🔴 Critical: Must fix before merge
- 🟡 Warning: Should fix but not blocking
- 🟢 Suggestion: Nice to have improvement

## Important Rules
- Always explain WHY something is a problem, not just WHAT
- Provide a corrected code snippet for each issue
- Be constructive and respectful in tone
```

### SKILL.md 解析

```
┌──────────────── SKILL.md 结构 ────────────────┐
│                                                │
│  # 标题                                        │
│  ├── 角色设定（你是谁，做什么）                   │
│  │                                              │
│  ## 可用工具                                    │
│  ├── 列出该 Skill 会用到的 Tools                 │
│  │                                              │
│  ## 执行流程                                    │
│  ├── 分步骤的详细指令                            │
│  │                                              │
│  ## 输出格式                                    │
│  ├── 定义输出的结构和样式                        │
│  │                                              │
│  ## 重要规则                                    │
│  └── 边界条件和约束                              │
│                                                │
└────────────────────────────────────────────────┘
```

关键要素：
- **角色定义**：让 Agent 知道自己在扮演什么角色
- **工具声明**：明确该 Skill 需要哪些 Tools
- **流程指令**：Step-by-step 的执行步骤
- **输出格式**：标准化输出，保证一致性
- **约束规则**：防止 Agent 偏离预期行为

> **面试考点**：SKILL.md 注入 system prompt 的机制是什么？
> - Agent 启动时，系统读取配置中注册的所有 SKILL.md 文件
> - 文件内容被**拼接**到 system prompt 中
> - Agent 在每次对话时都能"看到"这些指令
> - 这就是为什么 Skills 本质上是**提示工程（Prompt Engineering）的文件化**

---

## 四、ClawHub 技能市场

ClawHub 是 OpenClaw 的技能市场，拥有 **5700+ MCP Skills**，类似于 npm 或 pip 的包管理生态。

### 安装 Skill

```bash
/skills install @anthropic/web-search
/skills install @openai/code-interpreter
/skills install @community/weather-tool
```

### 在 openclaw.json 中注册

```json
{
  "name": "my-agent",
  "skills": [
    {
      "name": "@anthropic/web-search",
      "version": "^2.1.0",
      "config": {
        "maxResults": 10,
        "safeSearch": true
      }
    },
    {
      "name": "@community/weather-tool",
      "version": "^1.0.0"
    }
  ]
}
```

### 热门 Skills 分类

```
┌─────────────────────────────────────────────┐
│          ClawHub 热门分类 (5700+)            │
├──────────────┬──────────────────────────────┤
│ 🔍 Web Search │ 搜索引擎集成、实时信息检索    │
├──────────────┼──────────────────────────────┤
│ 💻 Coding     │ 代码生成、审查、调试、测试     │
├──────────────┼──────────────────────────────┤
│ 📁 Files      │ 文件处理、格式转换、批量操作   │
├──────────────┼──────────────────────────────┤
│ 📊 Productivity│ 日历、邮件、任务管理         │
├──────────────┼──────────────────────────────┤
│ ⚙️ Automation │ 工作流编排、定时任务、监控     │
├──────────────┼──────────────────────────────┤
│ 🎨 Image Gen  │ 图片生成、编辑、风格迁移      │
├──────────────┼──────────────────────────────┤
│ 📝 Writing    │ 文章撰写、翻译、摘要          │
├──────────────┼──────────────────────────────┤
│ 🗄️ Database   │ SQL查询、数据分析、可视化     │
└──────────────┴──────────────────────────────┘
```

### 如何选择和评估一个 Skill

评估一个 Skill 时，关注以下指标：

```
评估维度                 权重    检查项
─────────────────────────────────────────
1. 功能匹配度            ★★★★★  是否解决你的实际需求
2. 下载量/Star数         ★★★★   社区认可度
3. 维护活跃度            ★★★★   最近更新时间、issue响应
4. 文档质量              ★★★    README是否清晰完整
5. 安全审计              ★★★    是否有恶意代码风险
6. 依赖复杂度            ★★     是否引入过多外部依赖
7. 版本兼容性            ★★     是否兼容你的OpenClaw版本
```

> **面试考点**：如何设计一个 Skill 市场的搜索和推荐系统？
> 这是系统设计题的常见变种。需要考虑：
> - 基于关键词的全文搜索
> - 基于使用场景的语义搜索
> - 协同过滤推荐（安装了A的用户也安装了B）
> - 质量排名算法（下载量、评分、活跃度加权）

---

## 五、自定义 Skill 开发

### 创建你自己的 Skill

```bash
mkdir my-skill
cd my-skill
touch SKILL.md
```

在 SKILL.md 中编写你的 Skill 内容，然后在 `openclaw.json` 中本地注册：

```json
{
  "skills": [
    {
      "name": "my-custom-skill",
      "path": "./skills/my-skill/SKILL.md"
    }
  ]
}
```

### 发布到 ClawHub

```bash
/skills publish my-skill
```

发布前的检查清单：
- [ ] SKILL.md 内容完整，角色、流程、格式都定义清楚
- [ ] 包含 README.md 说明用途和用法
- [ ] 测试过 Agent 能正确理解和执行指令
- [ ] 没有硬编码的密钥或敏感信息

---

## 六、Skills 与 Prompt Engineering 的关系

```
传统 Prompt Engineering          OpenClaw Skills
─────────────────────           ─────────────────
手动拼接 prompt                  文件化管理
每次对话重新写                   一次编写，持续复用
难以版本控制                     Git 管理，可回溯
个人知识难以共享                  ClawHub 市场分享
无标准格式                       SKILL.md 规范
```

Skills 本质上是**结构化的、可复用的、可分享的 Prompt Engineering**。

> **面试考点**：Skills 系统相比硬编码能力有什么优势？
> 1. **灵活性**：修改 Markdown 文件即可更新能力，无需重新部署
> 2. **可组合性**：多个 Skills 可以组合使用
> 3. **民主化**：非程序员也能编写 Skills 扩展 Agent 能力
> 4. **生态效应**：ClawHub 市场让能力可以复用和共享

---

## 本课小结

```
┌────────────────────────────────────────────┐
│              核心知识点回顾                  │
├────────────────────────────────────────────┤
│                                            │
│  Tools   = 基础函数（约20个内置）            │
│  Skills  = Markdown指令（注入system prompt） │
│  Plugins = 功能包（打包分发）               │
│                                            │
│  SKILL.md = 角色 + 工具 + 流程 + 格式 + 规则│
│  ClawHub  = 5700+ Skills 的市场             │
│  安装命令 = /skills install @author/name    │
│                                            │
└────────────────────────────────────────────┘
```

---

## 课后练习

### 练习1：概念辨析
请用自己的话解释 Tools、Skills、Plugins 三者的关系，并各举一个实际例子说明它们的区别。

### 练习2：编写 SKILL.md
编写一个 "周报生成器" 的 SKILL.md，要求：
- 定义角色为周报撰写助手
- 使用 `file_read` 读取本周工作日志
- 使用 `web_fetch` 获取项目管理平台的任务状态
- 输出格式化的周报内容
- 至少包含3条约束规则

### 练习3：设计题
如果你要设计一个 Skill 的**热更新机制**（修改 SKILL.md 后 Agent 立即感知变化），你会如何实现？请考虑：
- 文件变更检测方案
- 如何在不中断对话的情况下更新 system prompt
- 版本回滚策略

---

> [← 上一课：会话管理](10-conversation-management.md) | [下一课：MCP 协议 →](12-mcp-protocol.md)
