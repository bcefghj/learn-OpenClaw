# 第15课：自动化工作流：HEARTBEAT 与定时任务

> **第三阶段：进阶实战** | [← 上一课：插件开发](14-plugin-development.md) | [下一课 →](16-security-governance.md)

---

## 本课目标

理解 OpenClaw 的自动化工作流机制，掌握 HEARTBEAT.md 和 BOOT.md 的工作原理，能够设计多 Agent 协同的自动化工作流并实现错误处理与降级方案。

---

## 一、从"被动应答"到"主动执行"

传统 Agent 是**被动的** —— 用户说一句，Agent 回一句。但真实业务场景中，很多任务需要 Agent **主动执行**：

- 每天早上 8 点发送新闻摘要
- 每小时检查服务器状态
- 每周五自动生成周报
- 数据库容量超标时自动告警

把 Agent 想象成一个**值班助理**：

```
被动模式（传统）：                 主动模式（自动化）：
┌──────────────┐                ┌──────────────┐
│              │                │              │
│   等待指令   │                │   定时巡检   │──→ 08:00 晨报
│      ↓       │                │      ↓       │──→ 每小时健康检查
│   用户说话   │                │   事件触发   │──→ 异常自动告警
│      ↓       │                │      ↓       │──→ 周五周报
│   处理回复   │                │   自主执行   │
│      ↓       │                │              │
│   继续等待   │                │              │
│              │                │              │
└──────────────┘                └──────────────┘
  "老板不说话我就不动"            "该做的事情我主动做"
```

OpenClaw 通过 **HEARTBEAT.md** 和 **BOOT.md** 两大机制，把 Agent 从"被动应答者"变成"主动执行者"。

---

## 二、HEARTBEAT.md：Agent 的心跳任务

### 工作原理

HEARTBEAT.md 是一个特殊的 Markdown 文件，OpenClaw 系统**每 30 分钟自动读取并执行**其中的指令。就像人的心脏每隔固定时间跳动一次，Agent 的 HEARTBEAT 每 30 分钟"跳"一次。

```
┌─────────────────────────────────────────────────────┐
│               HEARTBEAT.md 执行机制                   │
│                                                     │
│   时间轴：                                           │
│   ──┬──────┬──────┬──────┬──────┬──────┬──→         │
│     0min  30min  60min  90min  120min 150min        │
│     │      │      │      │      │      │            │
│     ▼      ▼      ▼      ▼      ▼      ▼            │
│   读取    读取    读取    读取    读取    读取          │
│   执行    执行    执行    执行    执行    执行          │
│                                                     │
│   系统行为：                                         │
│   1. 读取 HEARTBEAT.md 文件内容                      │
│   2. 将内容作为"用户消息"注入 Agent                   │
│   3. Agent 按照指令执行任务                           │
│   4. 执行结果记录到日志                              │
│   5. 等待下一次心跳                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### HEARTBEAT.md 示例

```markdown
# Heartbeat Tasks

## 1. Check System Health
Run `shell_exec` to check disk usage, memory, and CPU.
If any metric exceeds 80%, send an alert to the admin channel.

## 2. Fetch Latest News
Use `web_search` to find the top 3 tech news of the day.
Save a brief summary to `/data/news/today.md`.

## 3. Process Pending Tasks
Read `/data/tasks/pending.json` for any queued tasks.
Execute each task and move completed ones to `/data/tasks/done.json`.

## Important
- Keep each task execution under 2 minutes
- If a task fails, log the error and continue with the next task
- Never delete files without explicit configuration
```

### 关键设计细节

```
HEARTBEAT.md 注入方式：

┌──────────────────────────────────────────┐
│          每 30 分钟触发一次                │
│                                          │
│  系统读取 HEARTBEAT.md                   │
│        │                                 │
│        ▼                                 │
│  构造一条"虚拟用户消息"                    │
│  {                                       │
│    role: "user",                         │
│    content: <HEARTBEAT.md 的内容>         │
│    metadata: {                           │
│      source: "heartbeat",               │
│      trigger_time: "2026-03-27T08:00:00" │
│    }                                     │
│  }                                       │
│        │                                 │
│        ▼                                 │
│  注入 Agent 的 ReAct 循环                 │
│  Agent 像处理普通消息一样执行任务          │
│        │                                 │
│        ▼                                 │
│  执行完毕，记录日志，等待下次心跳          │
│                                          │
└──────────────────────────────────────────┘
```

> **面试考点**：HEARTBEAT.md 为什么设计成 Markdown 而不是 cron 表达式或代码？
>
> 1. **一致性**：与 SKILL.md 相同的设计哲学——自然语言指令，LLM 原生理解
> 2. **灵活性**：Agent 可以理解模糊指令（"如果有异常就告警"），不需要精确的条件编码
> 3. **低门槛**：非程序员也能编写定时任务
> 4. **可组合**：Agent 可以根据上下文动态决定是否执行某个任务

---

## 三、BOOT.md：启动时执行的初始化任务

### 工作原理

BOOT.md 是 Agent **启动时自动读取并执行一次**的文件，类似于操作系统的启动脚本（`/etc/rc.local`）或 Shell 的 `.bashrc`。

```
┌───────────────────────────────────────────────────┐
│                 Agent 启动流程                       │
│                                                   │
│   ┌──────────┐                                    │
│   │ Agent    │                                    │
│   │ 启动     │                                    │
│   └────┬─────┘                                    │
│        │                                          │
│        ▼                                          │
│   ┌──────────┐                                    │
│   │ 加载配置  │  openclaw.json, 环境变量            │
│   └────┬─────┘                                    │
│        │                                          │
│        ▼                                          │
│   ┌──────────┐                                    │
│   │ 加载     │  SKILL.md 文件 → system prompt      │
│   │ Skills   │                                    │
│   └────┬─────┘                                    │
│        │                                          │
│        ▼                                          │
│   ┌──────────────┐                                │
│   │ 执行 BOOT.md │  ← 启动钩子，只执行一次          │
│   │ (启动任务)    │                                │
│   └────┬─────────┘                                │
│        │                                          │
│        ▼                                          │
│   ┌──────────┐                                    │
│   │ 就绪     │  开始接收消息 + HEARTBEAT 循环       │
│   └──────────┘                                    │
│                                                   │
└───────────────────────────────────────────────────┘
```

### BOOT.md 示例

```markdown
# Boot Tasks

## Environment Check
1. Verify all required API keys are set (OPENAI_API_KEY, WEATHER_API_KEY)
2. Test connectivity to external services
3. Report any missing configuration to the admin channel

## Initialize Data
1. Read `/data/config/agents.json` to load agent profiles
2. Create today's log directory at `/data/logs/YYYY-MM-DD/`
3. Load user preferences from the database

## Send Boot Notification
Send a message to the admin channel:
"Agent started at {current_time}. All systems operational."
```

### BOOT.md vs HEARTBEAT.md 对比

```
特性              BOOT.md              HEARTBEAT.md
────────────────────────────────────────────────────
执行时机          Agent 启动时          每 30 分钟
执行次数          仅一次                持续循环
典型用途          环境检查、初始化       定时任务、巡检
执行上下文        全新（无对话历史）     继承之前的上下文
失败影响          可能阻止 Agent 启动    跳过本次，下次重试
类比              .bashrc               crontab
```

> **面试考点**：BOOT.md 执行失败时应该如何处理？
>
> 这是一个工程决策问题，有两种策略：
> 1. **严格模式**：BOOT 失败则 Agent 不启动（适合关键业务 Agent）
> 2. **宽松模式**：BOOT 失败记录日志，Agent 仍然启动（适合非关键场景）
> 3. **分级策略**：标记哪些任务是 `critical`（失败则停止）、哪些是 `optional`（失败则跳过）

---

## 四、定时任务的配置方式

虽然 HEARTBEAT.md 固定 30 分钟一次，但可以在文件内部实现更灵活的调度逻辑。

### 基于时间条件的任务调度

```markdown
# Heartbeat Tasks

## Every Heartbeat (每30分钟)
- Check system health metrics
- Process message queue

## Hourly (每小时，整点执行)
Check if current minute is 0-29 (first heartbeat of the hour).
If yes:
- Fetch and cache exchange rates
- Update weather data for configured cities

## Daily (每天一次，早8点)
Check if current time is between 08:00 and 08:29.
If yes:
- Generate daily news summary and send to #general channel
- Clean up temporary files older than 7 days
- Send daily analytics report

## Weekly (每周一次，周五下午)
Check if today is Friday AND current time is between 17:00 and 17:29.
If yes:
- Generate weekly report from daily logs
- Send week summary to all team channels
```

### 在 openclaw.json 中的配置

```json
{
  "automation": {
    "heartbeat": {
      "enabled": true,
      "intervalMinutes": 30,
      "file": "./HEARTBEAT.md",
      "timeout": 300,
      "onError": "log-and-continue"
    },
    "boot": {
      "enabled": true,
      "file": "./BOOT.md",
      "timeout": 60,
      "onError": "strict"
    }
  }
}
```

### 配置项说明

```
┌──────────────────────────────────────────────────┐
│           自动化配置项详解                          │
├──────────────┬───────────────────────────────────┤
│ enabled      │ 是否启用（true/false）              │
├──────────────┼───────────────────────────────────┤
│ intervalMin  │ HEARTBEAT 间隔（默认30分钟）         │
├──────────────┼───────────────────────────────────┤
│ file         │ 文件路径                           │
├──────────────┼───────────────────────────────────┤
│ timeout      │ 单次执行超时（秒）                  │
├──────────────┼───────────────────────────────────┤
│ onError      │ 错误策略：                         │
│              │   "strict" = 失败则停止             │
│              │   "log-and-continue" = 记录并继续   │
│              │   "retry" = 重试（最多3次）          │
└──────────────┴───────────────────────────────────┘
```

---

## 五、实际应用场景

### 场景1：每日新闻摘要

```markdown
# HEARTBEAT.md - 新闻摘要任务

## Daily News Digest
Check if current time is between 08:00 and 08:29.
If yes, perform the following:

1. Use `web_search` to search for:
   - "AI technology news today"
   - "tech industry updates today"
   - "programming language trends"

2. For each search result, use `web_fetch` to get the full article

3. Summarize the top 5 most important stories into a digest with:
   - Headline
   - 2-3 sentence summary
   - Source URL

4. Send the digest to the #daily-news channel

5. Save the digest to `/data/news/{date}.md`
```

**执行流程**：

```
08:00 HEARTBEAT 触发
    │
    ▼
Agent 读取 HEARTBEAT.md
    │
    ▼
检查时间条件 → 08:00-08:29 ✓ 满足
    │
    ▼
调用 web_search("AI technology news today")
    │
    ▼
调用 web_fetch(各个结果URL)
    │
    ▼
LLM 生成新闻摘要
    │
    ▼
调用 send_message(#daily-news, 摘要内容)
    │
    ▼
调用 file_write("/data/news/2026-03-27.md", 摘要)
    │
    ▼
任务完成，等待下次心跳
```

### 场景2：定期数据备份

```markdown
# HEARTBEAT.md - 数据备份任务

## Database Backup (every 6 hours)
Check if current hour is 0, 6, 12, or 18 (first heartbeat of that hour).
If yes:

1. Run `shell_exec` with: `pg_dump mydb > /backups/mydb_{timestamp}.sql`
2. Compress: `gzip /backups/mydb_{timestamp}.sql`
3. Check backup file size - if less than 1KB, something went wrong
4. Delete backups older than 30 days
5. Send backup status report to admin
```

### 场景3：自动化报告

```markdown
# HEARTBEAT.md - 周报生成

## Weekly Report (Friday 17:00)
Check if today is Friday AND time is 17:00-17:29.
If yes:

1. Read all daily logs from `/data/logs/` for this week
2. Read task completion data from `/data/tasks/done.json`
3. Generate a structured weekly report including:
   - Tasks completed vs planned
   - Key achievements
   - Blockers and issues
   - Next week priorities
4. Format as Markdown and save to `/reports/week-{week_number}.md`
5. Send to team channel and email distribution list
```

> **面试考点**：如何保证定时任务的幂等性？
>
> HEARTBEAT 每 30 分钟触发一次，但某些任务（如日报）只应执行一次。如何防止重复执行？
>
> 解决方案：
> 1. **状态文件**：执行完毕后写入标记文件（如 `/data/flags/news_2026-03-27.done`），下次检查标记是否存在
> 2. **数据库记录**：记录每个任务的最后执行时间，只在超过间隔后执行
> 3. **锁机制**：执行前获取分布式锁，执行完释放
> 4. **LLM 判断**：让 Agent 自行检查"这个任务今天是否已经执行过"

---

## 六、多 Agent 协同工作流

在复杂场景下，单个 Agent 可能无法完成所有工作，需要**多个 Agent 协作**。

### 协同模式

```
模式一：流水线（Pipeline）
─────────────────────────
  Agent A ──→ Agent B ──→ Agent C
  (采集数据)   (分析处理)   (生成报告)

模式二：扇出-扇入（Fan-out / Fan-in）
─────────────────────────────────────
              ┌── Agent B (任务1) ──┐
  Agent A ────┼── Agent C (任务2) ──┼──→ Agent E (汇总)
              └── Agent D (任务3) ──┘

模式三：监督者（Supervisor）
──────────────────────────
           Agent A (监督者)
          ┌───┼───┐
          ▼   ▼   ▼
        Agent Agent Agent
         B     C     D
        (工人) (工人) (工人)
```

### 流水线模式实现

```markdown
# Agent A 的 HEARTBEAT.md (数据采集)

## Collect Data
1. Fetch sales data from API
2. Save raw data to `/shared/data/sales_raw.json`
3. Write a signal file `/shared/signals/data_ready.flag`
```

```markdown
# Agent B 的 HEARTBEAT.md (数据分析)

## Analyze Data
1. Check if `/shared/signals/data_ready.flag` exists
2. If yes:
   - Read `/shared/data/sales_raw.json`
   - Perform analysis: trends, anomalies, forecasts
   - Save results to `/shared/data/sales_analysis.json`
   - Delete `/shared/signals/data_ready.flag`
   - Write `/shared/signals/analysis_ready.flag`
3. If no: skip this heartbeat
```

```markdown
# Agent C 的 HEARTBEAT.md (报告生成)

## Generate Report
1. Check if `/shared/signals/analysis_ready.flag` exists
2. If yes:
   - Read `/shared/data/sales_analysis.json`
   - Generate formatted report with charts description
   - Send report to #sales-reports channel
   - Archive data to `/shared/archive/`
   - Delete `/shared/signals/analysis_ready.flag`
3. If no: skip this heartbeat
```

### 协同架构图

```
┌──────────────────────────────────────────────────────┐
│             多 Agent 协同工作流                         │
│                                                      │
│  Agent A          Agent B          Agent C            │
│  (采集)           (分析)           (报告)              │
│  ┌────────┐      ┌────────┐      ┌────────┐          │
│  │HEARTBEAT│     │HEARTBEAT│     │HEARTBEAT│          │
│  │ 30min  │      │ 30min  │      │ 30min  │          │
│  └───┬────┘      └───┬────┘      └───┬────┘          │
│      │               │               │               │
│      ▼               ▼               ▼               │
│  采集数据        检查信号文件     检查信号文件          │
│      │          有 → 分析       有 → 生成报告          │
│      ▼          无 → 跳过       无 → 跳过              │
│  写入数据文件        │               │               │
│  写入信号文件        ▼               ▼               │
│      │          写入分析结果     发送报告              │
│      │          写入信号文件     归档数据              │
│      │               │               │               │
│      └───────────────┴───────────────┘               │
│              通过共享文件系统协调                       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

> **面试考点**：多 Agent 协同有哪些常见的协调机制？
>
> 1. **文件信号（File Signal）**：通过信号文件传递状态，简单但粗粒度
> 2. **消息队列**：通过消息中间件解耦，可靠但增加复杂度
> 3. **共享数据库**：通过数据库记录状态，适合复杂状态管理
> 4. **直接消息**：Agent 之间通过渠道互发消息触发任务
>
> OpenClaw 的文件系统 + HEARTBEAT 轮询方式属于第一种，适合简单场景。复杂场景建议引入消息队列。

---

## 七、工作流的错误处理和降级方案

自动化任务必须考虑"出错了怎么办"，否则一个小错误可能导致整个工作流瘫痪。

### 错误处理策略

```
┌───────────────────────────────────────────────────────┐
│               错误处理分级策略                           │
│                                                       │
│  Level 1: 任务级重试                                    │
│  ─────────────────                                    │
│  单个任务失败 → 等待 → 重试（最多3次）                    │
│  适用：网络超时、API 临时不可用                           │
│                                                       │
│  Level 2: 任务级跳过                                    │
│  ─────────────────                                    │
│  重试3次仍失败 → 记录错误 → 跳过该任务 → 继续后续任务     │
│  适用：非关键任务（如新闻采集失败不影响系统运行）           │
│                                                       │
│  Level 3: 降级执行                                      │
│  ─────────────────                                    │
│  主要功能失败 → 执行降级方案（使用缓存数据/简化输出）      │
│  适用：对外服务不可中断的场景                             │
│                                                       │
│  Level 4: 告警通知                                      │
│  ─────────────────                                    │
│  关键任务失败 → 立即通知管理员 → 等待人工介入              │
│  适用：数据备份失败、安全告警等关键任务                    │
│                                                       │
│  Level 5: 熔断停止                                      │
│  ─────────────────                                    │
│  连续N次失败 → 暂停该类任务 → 防止级联故障                │
│  适用：下游服务彻底宕机，继续重试只会浪费资源              │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 在 HEARTBEAT.md 中编写容错逻辑

```markdown
# Heartbeat Tasks with Error Handling

## Daily Report Generation

### Primary Plan
1. Fetch data from analytics API
2. Generate report using the latest data
3. Send to #reports channel

### Fallback Plan (if primary fails)
If the analytics API is unreachable:
1. Read yesterday's cached data from `/data/cache/analytics_latest.json`
2. Generate report with cached data, clearly marking it as "based on cached data"
3. Send to #reports channel with a warning note
4. Send alert to admin: "Analytics API unreachable, using cached data"

### If Both Plans Fail
1. Send a brief message to #reports: "Daily report generation failed. Admin has been notified."
2. Send detailed error log to admin channel
3. Do NOT retry until next scheduled time
```

### 降级方案设计模板

```
正常流程                    降级流程
────────                   ────────
实时API数据          →     缓存数据（标注时效性）
完整分析报告          →     简化版摘要
多渠道发送            →     仅发送主渠道
图文并茂             →     纯文本格式
个性化推荐            →     通用内容
```

> **面试考点**：如何设计一个健壮的自动化工作流？
>
> 这是系统设计面试的高频题。关键要点：
> 1. **幂等性**：同一任务多次执行结果一致
> 2. **超时控制**：每个任务有明确的超时时间
> 3. **降级方案**：每个关键步骤都有 Plan B
> 4. **可观测性**：完善的日志和监控，出问题能快速定位
> 5. **告警机制**：关键失败立即通知，非关键失败汇总报告
> 6. **熔断器**：连续失败时自动停止，防止雪崩效应

---

## 八、自动化工作流编排的设计思路

### 工作流定义语言

对于复杂的多步骤工作流，可以用结构化的方式定义：

```json
{
  "workflow": "daily-digest",
  "schedule": "08:00",
  "steps": [
    {
      "id": "collect",
      "action": "web_search",
      "params": { "query": "tech news today" },
      "timeout": 60,
      "onError": "skip"
    },
    {
      "id": "analyze",
      "action": "llm_process",
      "input": "${collect.output}",
      "prompt": "Summarize these articles into a digest",
      "timeout": 120,
      "onError": "fallback",
      "fallback": {
        "action": "file_read",
        "params": { "path": "/cache/last_digest.md" }
      }
    },
    {
      "id": "deliver",
      "action": "send_message",
      "params": {
        "channel": "#daily-news",
        "content": "${analyze.output}"
      },
      "timeout": 30,
      "onError": "retry",
      "maxRetries": 3
    }
  ]
}
```

### 工作流状态机

```
┌─────────┐    触发     ┌──────────┐    所有步骤完成   ┌───────────┐
│ PENDING │───────────→│ RUNNING  │─────────────────→│ COMPLETED │
└─────────┘            └────┬─────┘                  └───────────┘
                            │
                       某步骤失败
                            │
                  ┌─────────┴─────────┐
                  │                   │
             可重试/可跳过        不可恢复
                  │                   │
                  ▼                   ▼
            ┌──────────┐       ┌──────────┐
            │ RETRYING │       │  FAILED  │
            └────┬─────┘       └──────────┘
                 │
            重试成功 → 继续 RUNNING
            重试耗尽 → FAILED
```

---

## 本课小结

```
┌────────────────────────────────────────────────────┐
│              核心知识点回顾                          │
├────────────────────────────────────────────────────┤
│                                                    │
│  HEARTBEAT.md                                      │
│    = 每 30 分钟自动读取执行的定时任务文件             │
│    = 内容作为"虚拟用户消息"注入 Agent                │
│    = 可通过时间条件实现灵活调度                      │
│                                                    │
│  BOOT.md                                           │
│    = Agent 启动时执行一次的初始化脚本                │
│    = 类比 .bashrc / rc.local                       │
│                                                    │
│  多 Agent 协同                                     │
│    = 流水线 / 扇出-扇入 / 监督者模式                │
│    = 通过文件信号或消息队列协调                      │
│                                                    │
│  错误处理                                          │
│    = 重试 → 跳过 → 降级 → 告警 → 熔断               │
│    = 幂等性 + 超时控制 + 可观测性                   │
│                                                    │
│  设计关键词：                                       │
│    幂等性、降级方案、熔断器、可观测性                │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 课后练习

### 练习1：HEARTBEAT 设计
为一个"客户支持 Agent"编写 HEARTBEAT.md，要求实现以下定时任务：
- 每 30 分钟检查未回复的工单
- 每小时统计客户满意度评分
- 每天 9:00 生成值班交接报告
- 包含适当的错误处理逻辑

### 练习2：多 Agent 协同设计
设计一个"自动化内容发布"工作流，包含以下 Agent：
- Agent A：内容采集（从多个 RSS 源获取文章）
- Agent B：内容审核（检查质量和合规性）
- Agent C：内容发布（发送到多个渠道）

画出完整的协同架构图，说明信号传递机制和错误处理方案。

### 练习3：降级方案设计
一个 Agent 的 HEARTBEAT 任务是"每 6 小时生成数据分析报告并发送给团队"。请为以下故障场景设计降级方案：
- 数据源 API 不可用
- LLM 服务响应超时
- 消息发送渠道（Slack）宕机
- 多个故障同时发生

要求每个场景给出 Plan A（正常）、Plan B（降级）、Plan C（最小化）三级方案。

---

> [← 上一课：插件开发](14-plugin-development.md) | [下一课：安全治理 →](16-security-governance.md)
