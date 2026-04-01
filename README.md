<p align="center">
  <img src="assets/logo.svg" width="120" alt="Learn OpenClaw Logo"/>
</p>

<h1 align="center">🦞 learn-OpenClaw —— 面试导向完全学习指南</h1>

<p align="center">
  <strong>零基础 → 理解原理 → 实战上手 → 写进简历 → 征服面试官</strong>
</p>

<p align="center">
  <img src="comics/comic-01-what-is-agent.png" width="600" alt="漫画：机器猫介绍AI Agent"/>
</p>

<p align="center">
  <a href="#课程导航">课程导航</a> •
  <a href="#为什么要学-openclaw">为什么学</a> •
  <a href="#学习路线图">路线图</a> •
  <a href="#面试专区">面试专区</a> •
  <a href="#参考资源">资源</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/课程-20节-blue?style=for-the-badge" alt="20节课"/>
  <img src="https://img.shields.io/badge/八股文-110题-purple?style=for-the-badge" alt="110题八股文"/>
  <img src="https://img.shields.io/badge/面试题-50题-red?style=for-the-badge" alt="50题面试"/>
  <img src="https://img.shields.io/badge/STAR面试稿-10场景-green?style=for-the-badge" alt="STAR"/>
  <img src="https://img.shields.io/badge/漫画插图-10张-orange?style=for-the-badge" alt="漫画"/>
  <img src="https://img.shields.io/badge/零基础友好-2026-yellow?style=for-the-badge" alt="零基础"/>
</p>

---

## 这是什么？

> **OpenClaw** 是 2026 年最火的开源 AI Agent 项目（GitHub 33万+ Star），黄仁勋在 GTC 大会上称之为"AI 界的 Windows"。

本仓库是一份**从零开始、面向面试**的 OpenClaw 完全学习指南。无需任何 AI/编程基础，20 节课带你从"什么是 AI"走到"面试官问什么都能答"。

### 适合谁？

| 你的情况 | 本课程能帮你什么 |
|---------|--------------|
| 完全小白，没接触过 AI | 从 AI 基本概念讲起，手把手带入门 |
| 想转型 AI 方向 | 系统学习 Agent 架构，建立技术体系 |
| 准备面试，想写进简历 | 提供简历模板 + 面试题库 + 项目描述 |
| 会用但不懂原理 | 深入源码级架构分析，知其所以然 |

---

## 为什么要学 OpenClaw？

```
2026年春招，字节/阿里/腾讯/美团等大厂面试高频考点

面试官问：「你了解 OpenClaw 吗？」
❌ "就是个 AI 助手吧..."
✅ "OpenClaw 采用 Fat Gateway 架构，核心是 ReAct 循环..."

面试官问：「它和 ChatGPT 有什么区别？」
❌ "功能更多？"
✅ "ChatGPT 是对话闭环，OpenClaw 是执行闭环。它有自己的控制面和数据面..."
```

---

## 学习路线图

```
                    🦞 OpenClaw 学习路线图
    
    ┌─────────────────────────────────────────────────┐
    │          第一阶段：基础认知（第1-5课）              │
    │  AI基础 → Agent概念 → OpenClaw定位 → 安装 → 初体验 │
    └──────────────────────┬──────────────────────────┘
                           │
                           ▼
    ┌─────────────────────────────────────────────────┐
    │          第二阶段：核心架构（第6-10课）             │
    │  Gateway → Agent Runner → ReAct → Context → Memory│
    └──────────────────────┬──────────────────────────┘
                           │
                           ▼
    ┌─────────────────────────────────────────────────┐
    │          第三阶段：进阶实战（第11-15课）            │
    │  Skills → MCP → 多渠道 → 插件开发 → 自动化工作流   │
    └──────────────────────┬──────────────────────────┘
                           │
                           ▼
    ┌─────────────────────────────────────────────────┐
    │          第四阶段：面试冲刺（第16-20课）            │
    │  安全 → 源码 → 系统设计 → 简历包装 → 模拟面试     │
    └─────────────────────────────────────────────────┘
```

---

## 课程导航

### 第一阶段：基础认知 🌱

> 从零开始，建立对 AI Agent 和 OpenClaw 的整体认知

| 课号 | 标题 | 关键词 | 预计时长 |
|:---:|------|-------|:------:|
| 01 | [什么是 AI、大模型和 Agent？](lessons/01-what-is-ai-agent.md) | AI基础, LLM, Agent概念 | 45min |
| 02 | [Agent 的核心概念：Tool Calling 与 ReAct](lessons/02-agent-core-concepts.md) | Tool Calling, ReAct循环, System Prompt | 60min |
| 03 | [OpenClaw 是什么？为什么它这么火？](lessons/03-what-is-openclaw.md) | 项目定位, 发展历史, 核心能力 | 45min |
| 04 | [动手安装 OpenClaw](lessons/04-install-openclaw.md) | 环境配置, Node.js, 安装部署 | 60min |
| 05 | [第一次对话：Hello OpenClaw！](lessons/05-first-conversation.md) | CLI交互, Dashboard, 基础命令 | 45min |

### 第二阶段：核心架构 🏗️

> 深入理解 OpenClaw 的技术架构，这是面试的重中之重

| 课号 | 标题 | 关键词 | 预计时长 |
|:---:|------|-------|:------:|
| 06 | [整体架构：Fat Gateway 模式](lessons/06-gateway-architecture.md) | Gateway, 控制面/数据面, WebSocket | 60min |
| 07 | [Agent Runner：消息如何被处理](lessons/07-agent-runner.md) | Agent Runner, 消息链路, Lane队列 | 60min |
| 08 | [ReAct 循环：Agent 的大脑回路](lessons/08-react-loop.md) | ReAct循环, 推理-行动, 工具调用链 | 60min |
| 09 | [Context Window：最核心的工程约束](lessons/09-context-window.md) | 上下文窗口, Compaction, 裁剪策略 | 60min |
| 10 | [Memory 系统：让 AI 拥有记忆](lessons/10-memory-system.md) | SOUL.md, MEMORY.md, 向量搜索 | 60min |

### 第三阶段：进阶实战 🔧

> 掌握进阶功能，积累实战经验

| 课号 | 标题 | 关键词 | 预计时长 |
|:---:|------|-------|:------:|
| 11 | [Skills 系统与 ClawHub 生态](lessons/11-skills-system.md) | Skills, ClawHub, SKILL.md | 60min |
| 12 | [MCP 协议：Agent 的通用语言](lessons/12-mcp-protocol.md) | MCP协议, 工具标准化, Server/Client | 60min |
| 13 | [多渠道接入：从 Telegram 到飞书](lessons/13-multi-channel.md) | Channel Plugin, 消息路由, 会话隔离 | 60min |
| 14 | [插件开发：写你的第一个 Plugin](lessons/14-plugin-development.md) | Plugin架构, 能力注册, Hook系统 | 90min |
| 15 | [自动化工作流：HEARTBEAT 与定时任务](lessons/15-automation-workflow.md) | HEARTBEAT.md, 自动化, 工作流编排 | 60min |

### 第四阶段：面试冲刺 🎯

> 面向面试的针对性准备，确保能从容应对面试官的所有问题

| 课号 | 标题 | 关键词 | 预计时长 |
|:---:|------|-------|:------:|
| 16 | [安全与治理：企业级落地的核心挑战](lessons/16-security-governance.md) | 权限控制, 沙箱隔离, 安全审计 | 60min |
| 17 | [源码导读：关键模块逐行分析](lessons/17-source-code-tour.md) | TypeScript, 源码结构, 核心函数 | 90min |
| 18 | [系统设计题：如何设计一个 Agent 系统](lessons/18-system-design.md) | 架构设计, 高可用, 扩展性 | 90min |
| 19 | [简历包装：如何展示 OpenClaw 项目经验](lessons/19-resume-guide.md) | 简历模板, STAR法则, 项目描述 | 60min |
| 20 | [模拟面试：50 道高频面试题全解析](lessons/20-mock-interview.md) | 面试题库, 答题框架, 高分策略 | 120min |

---

## 面试专区

> 面试是本课程的终极目标，这里是精华中的精华

### 核心面试材料

| 材料 | 说明 | 适合阶段 |
|------|------|---------|
| [八股文大全（110+ 题）](interview/baguweng.md) | 分 9 大类的面试题 + 详细答案，约 4.8 万字 | 面试前重点刷 |
| [面试题库（50 题）](interview/questions.md) | 入门→中级→高级分层，每题附得分点 | 系统复习 |
| [STAR 面试稿（10 场景）](interview/star-interview-scripts.md) | 完整口述稿 + 追问应对 | 面试前练习 |

### 简历与求职

| 材料 | 说明 |
|------|------|
| [简历模板：3 种方向](interview/resume-template.md) | 部署运维 / Agent开发 / 源码贡献 |
| [小白简历撰写教程](interview/resume-writing-guide.md) | 从零写简历，含完整范例 |
| [项目介绍话术](interview/project-introduction.md) | 30秒/1分钟/3分钟版本 |
| [面试官视角](interview/interviewer-perspective.md) | 他们到底想考什么？ |
| [2026 岗位市场分析](interview/job-market-2026.md) | 薪资、岗位、行业分布 |

---

## 快速开始

```bash
# 1. 克隆本仓库
git clone https://github.com/bcefghj/learn-OpenClaw.git

# 2. 按照课程顺序学习
# 从 lessons/01-what-is-ai-agent.md 开始

# 3. 每节课后完成练习题
# 练习题在每课末尾的「动手练习」部分

# 4. 面试前重点复习面试专区
# interview/ 目录下的内容

# 5. 生成 HTML 版本（可选）
python3 scripts/build-html.py
# 打开 docs/index.html 即可阅读

# 6. 生成 PDF 版本（需安装 pandoc）
python3 scripts/build-pdf.py
```

---

## 参考资源

### 官方资源
- [OpenClaw GitHub](https://github.com/openclaw/openclaw) - 官方仓库（33万+ Star）
- [OpenClaw 官方文档](https://docs.openclaw.ai) - 官方文档
- [ClawHub](https://clawhub.com) - 官方技能市场

### 学习资源
- [awesome-openclaw-tutorial](https://github.com/xianyu110/awesome-openclaw-tutorial) - 最全中文教程（3400+ Star）
- [openclaw-tutorial by Datawhale](https://github.com/datawhalechina/openclaw-tutorial) - 一周速成教程
- [hand-on-openclaw](https://github.com/datawhalechina/hand-on-openclaw) - 实战手册
- [openclaw-course-from-scratch](https://github.com/cloudzun/openclaw-course-from-scratch) - 从零开始课程

### 面试资源
- [面试鸭 OpenClaw 题库](https://www.mianshiya.com/bank/2031640554575519745) - 26 道企业真题
- [OpenClaw 底层架构拆解](https://cloud.tencent.com/developer/article/2632386) - 腾讯云技术文章
- [面试官视角：OpenClaw 到底考什么](https://www.gankinterview.cn/zh-CN/blog/what-is-the-interviewer-really-testing-when-asking-about-openclaw) - 面试策略

### 技术深度
- [OpenClaw 架构深度剖析](https://enricopiovano.com/blog/openclaw-architecture-deep-dive) - 六层架构分析
- [Agent Runner 函数级剖析](https://openclaw-docs.dx3n.cn/beginner-openclaw-guide/25-函数级剖析-agent-runner-execution) - 源码级分析
- [OpenClaw 源码解析：Gateway 启动](https://www.ququ123.top/2026/03/openclaw-gateway-startup/) - Gateway 源码

---

## 学习建议

1. **不要跳课**：每节课的内容是层层递进的，跳过前面的基础会导致后面听不懂
2. **动手实践**：每节课都有实践环节，一定要亲自动手操作
3. **做笔记**：把关键架构图和概念用自己的话总结一遍
4. **刷面试题**：学完每个阶段后，及时做对应的面试题
5. **模拟面试**：找朋友互相模拟面试，或者对着镜子自己讲

---

## 漫画插图

本仓库包含 10 张可爱风格漫画插图，穿插在课程中帮助理解核心概念：

<p align="center">
  <img src="comics/comic-02-react-loop.png" width="400" alt="ReAct循环"/>
  <img src="comics/comic-03-gateway.png" width="400" alt="Gateway"/>
</p>
<p align="center">
  <img src="comics/comic-05-skills.png" width="400" alt="Skills"/>
  <img src="comics/comic-10-celebrate.png" width="400" alt="毕业"/>
</p>

[查看全部漫画 →](comics/README.md)

---

## 多格式导出

| 格式 | 说明 | 命令 |
|------|------|------|
| Markdown | 直接在 GitHub 阅读 | - |
| HTML | 美观的单页网站 | `python3 scripts/build-html.py` |
| PDF | 打印友好版本 | `python3 scripts/build-pdf.py` |

---

## 项目结构

```
learn-OpenClaw/
├── lessons/          # 20节课程（每节 2000-5000 字）
├── interview/        # 面试材料（八股文、STAR面试稿、简历模板等）
├── comics/           # 10张漫画插图
├── practice/         # 实践项目指南
├── scripts/          # PDF/HTML 导出脚本
├── docs/             # 导出的 HTML/PDF
├── references/       # 学习资源汇总
└── assets/           # 静态资源
```

---

## 更多资源

- [学习资源汇总](references/learning-resources.md)
- [面试资源导航](references/interview-resources.md)
- [实践项目指南](practice/README.md)

---

## 贡献

欢迎提交 Issue 和 PR！如果觉得有帮助，请给个 Star

## License

MIT License

---

<p align="center">
  <img src="comics/comic-10-celebrate.png" width="500" alt="恭喜你从小白到面试达人"/>
</p>
<p align="center">
  <sub>Made with care for every job seeker in 2026</sub>
</p>
