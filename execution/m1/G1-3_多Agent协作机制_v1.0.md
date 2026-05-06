# G1-3 多 Agent 协作机制（v1.0）

## 1. 文档信息
- 文档编号：`G1-3`
- 文档版本：`v1.0`
- 生效日期：`2026-03-26`
- 责任 Agent：`PM-Agent`

## 2. Agent 编组与职责

| Agent | 主责范围 | 不负责范围 |
|---|---|---|
| PM-Agent | 计划、优先级、验收与升级 | 业务代码实现 |
| Data-Agent | 数据接入/治理/特征 | 前端页面与可视化 |
| Algo-Agent | 预测建模/归因/评估 | 发布运维 |
| Backend-Agent | API/鉴权/服务集成 | 模型训练 |
| Frontend-Agent | UI/WebGIS/ECharts 交互 | 后端业务逻辑 |
| Test-Agent | 测试门禁/回归/质量结论 | 需求优先级裁决 |
| Ops-Agent | CI/CD/部署/监控/回滚 | 功能需求设计 |
| Doc-Agent | 文档标准化与归档 | 功能实现 |

## 3. 任务流转状态机

`To Do -> In Progress -> In Review -> Blocked -> Done`

状态定义：
- `To Do`：已排期，未开始。
- `In Progress`：正在执行。
- `In Review`：已提交，等待评审或验收。
- `Blocked`：存在阻塞，必须附带 blocker 描述。
- `Done`：完成并通过阶段门禁。

## 4. 节奏机制
- 每日站会：09:30（10 分钟）
- 每周里程碑会：周五 16:00
- 阶段门禁会：每个阶段结束前 1 个工作日

## 5. 协同规则
- 目录所有权：Agent 仅修改其责任目录，跨目录变更需 PM-Agent 审批。
- 契约优先：接口与事件 Schema 先评审后实现。
- 变更留痕：所有关键动作写入日志（worklog/testlog/releaselog）。
- 升级机制：
  - 阻塞 > 4 小时：标记 `Blocked` 并通知 PM-Agent
  - 阻塞 > 24 小时：发起升级会议并调整排期

## 6. 评审机制

| 评审类型 | 触发条件 | 参与角色 | 输出 |
|---|---|---|---|
| 设计评审 | 新增核心模块/接口契约 | PM + Backend + Algo + Frontend + Test | 评审结论与行动项 |
| 代码评审 | 合并主分支前 | 开发 + Test | 评审意见与修复记录 |
| 阶段评审 | 阶段门禁前 | PM + Test + Ops + Doc | 准出/不准出结论 |

## 7. 日报模板

```text
日期:
Agent:
今日完成:
进行中:
阻塞项:
明日计划:
风险提示:
证据路径:
```

## 8. Definition of Done（DoD）
- 对应任务文档/代码已提交并可追溯。
- 测试结论存在且通过门禁阈值。
- 日志已写入并包含证据路径。
- 对外影响已通知相关 Agent。

## 9. 附件索引
- [03_M1启动批次任务板.csv](d:\小桌面\交通拥堵\execution\03_M1启动批次任务板.csv)
- [worklog.csv](d:\小桌面\交通拥堵\execution\logs\worklog.csv)
- [testlog.csv](d:\小桌面\交通拥堵\execution\logs\testlog.csv)
- [releaselog.csv](d:\小桌面\交通拥堵\execution\logs\releaselog.csv)

