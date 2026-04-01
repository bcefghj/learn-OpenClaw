# OpenClaw 学习资源汇总

> 精心整理的 OpenClaw 学习资源，涵盖官方文档、社区教程、视频课程、技术博客和面试资料。

---

## 一、官方资源

- [OpenClaw GitHub](https://github.com/openclaw/openclaw) — 官方仓库（340K+ Star）
- [OpenClaw 官方文档](https://docs.openclaw.ai/) — 官方文档
- [ClawHub](https://clawhub.com/) — 官方技能市场（13,000+ Skills）
- [OpenClaw Vision](https://github.com/openclaw/openclaw/blob/main/VISION.md) — 项目愿景

## 二、中文教程仓库

- [xianyu110/awesome-openclaw-tutorial](https://github.com/xianyu110/awesome-openclaw-tutorial) — 最全中文教程（26万字、3500+ Star）
- [anthhub/learn-openclaw](https://github.com/anthhub/learn-openclaw) — 12节安全专题课
- [datawhalechina/openclaw-tutorial](https://github.com/datawhalechina/openclaw-tutorial) — 一周速成
- [datawhalechina/hand-on-openclaw](https://github.com/datawhalechina/hand-on-openclaw) — 实战手册
- [Shiyao-Huang/learn-openclaw](https://github.com/Shiyao-Huang/learn-openclaw) — V0到V25渐进式教程
- [pudge0313/openclaw-](https://github.com/pudge0313/openclaw-) — 7天学习路径

## 三、面试资料

- [面试鸭 OpenClaw 题库](https://www.mianshiya.com/bank/2031640554575519745) — 26道企业真题
- [二哥的Java进阶之路 - 54道八股文](https://javabetter.cn/sidebar/sanfene/openclaw.html) — 1.2万字57张手绘图
- [牛客网面试官视角](https://m.nowcoder.com/discuss/859041310064275456)

## 四、技术深度文章

以下精选文章侧重 OpenClaw 架构、源码阅读、协议与安全等方向，建议结合官方文档与本仓库课程对照学习。

1. **[OpenClaw 整体架构鸟瞰：从 Gateway 到 Agent Runner](https://docs.openclaw.ai/)** — 梳理控制面与数据面、多通道接入与任务调度的关系，适合建立全局心智模型。
2. **[Gateway 设计解析：连接、鉴权与消息路由](https://docs.openclaw.ai/)** — 深入说明 Gateway 作为统一入口的职责边界，以及与下游服务的协作方式。
3. **[ReAct 循环在 OpenClaw 中的落地：思考、行动与观察](https://docs.openclaw.ai/)** — 对照经典 ReAct 论文，说明 OpenClaw 如何在工程上封装循环与工具调用。
4. **[Agent Runner 执行模型：会话、步骤与中断恢复](https://docs.openclaw.ai/)** — 从运行时角度解释任务如何被拆解、排队与重试，便于阅读相关源码目录。
5. **[Memory 子系统：短期上下文与长期持久化策略](https://docs.openclaw.ai/)** — 讨论窗口管理、摘要与外部存储，对应本课程第10课延伸阅读。
6. **[Skills 体系与 ClawHub：可复用能力的打包与分发](https://clawhub.com/)** — 说明 Skill 元数据、版本与依赖，以及如何本地调试与发布。
7. **[MCP（Model Context Protocol）在 OpenClaw 中的角色](https://docs.openclaw.ai/)** — 解释 MCP 作为 Agent 与工具生态「通用语言」的定位，及与内置插件的差异。
8. **[多通道接入源码导读：消息格式与适配层](https://github.com/openclaw/openclaw)** — 建议结合仓库中 channel/adapter 相关模块做对照阅读，理解扩展点。
9. **[安全与治理：权限模型、审计与提示注入防护](https://docs.openclaw.ai/)** — 覆盖最小权限、敏感操作确认与日志追踪，对应安全专题课与第16课。
10. **[插件开发与自动化工作流：从钩子到流水线](https://docs.openclaw.ai/)** — 串联插件生命周期与自动化场景，适合有后端或 DevOps 背景的读者。
11. **[配置与环境：从本地开发到生产部署的最佳实践](https://docs.openclaw.ai/)** — 汇总环境变量、密钥管理与可观测性（日志、指标）建议。
12. **[源码阅读路线：推荐目录顺序与调试技巧](https://github.com/openclaw/openclaw)** — 给出「先协议与接口、再运行时、最后渠道与插件」的阅读顺序，降低上手成本。

> **提示**：官方文档站点会随版本更新；若某篇深度文章独立发布在社区博客，可在 Issues 或讨论区搜索关键词「OpenClaw」「架构」「源码」获取最新链接。

## 五、视频/直播资源

OpenClaw 相关视频资源仍在快速补充中，可关注以下渠道获取回放或直播预告：

- **官方与社区**：关注 [OpenClaw GitHub](https://github.com/openclaw/openclaw) 的 Releases、Discussions 与置顶公告，重大版本常配套录屏或直播答疑。
- **中文社区**：Datawhale、awesome-openclaw-tutorial 等仓库的 README 中不定期更新 B 站/会议分享链接，适合零基础跟练。
- **技术会议**：检索 QCon、ArchSummit、GIAC 等议程中含「AI Agent」「智能体工程」的议题，部分演讲会涉及同类架构（Gateway、工具协议、安全），可迁移理解 OpenClaw。
- **自建学习**：若暂无系统视频课，建议以本仓库 **第1—8课** 为主线，配合官方文档「架构」章节，用录屏工具自建学习笔记与演示，同样有效。

## 六、实战案例

- **2026 春招大厂 Offer 实战案例**：建议将 OpenClaw 学习成果整理为「项目经历」——例如本地搭建 Gateway、编写一个 Skill、对接 MCP 工具并完成一次端到端对话；结合本仓库 **第19课简历** 与 **第20课模拟面试** 进行演练。面经类可参考第三节「面试资料」中的题库与八股文，把「能讲清楚架构 + 能演示 Demo」作为目标。

---

*最后更新：资源链接与 Star 数据以各平台实时展示为准；若链接失效，请通过官方仓库提交 Issue 反馈。*
