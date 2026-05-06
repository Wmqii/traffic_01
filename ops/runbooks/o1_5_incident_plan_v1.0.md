# O1-5 应急预案（v1.0）

## 1. 文档信息
- 文档编号：`O1-5-INCIDENT`
- 版本：`v1.0`
- 日期：`2026-03-27`
- 责任 Agent：`Ops-Agent`
- 阶段：`M4`

## 2. 目标
- 在故障出现后 5 分钟内（`MTTR <= 300s`）恢复核心链路。
- 对故障发现、升级、处置、复盘形成标准动作与可审计记录。

## 3. 应急等级
- `P1`：核心服务不可用或关键数据链路中断（立即升级，5 分钟内恢复）。
- `P2`：部分功能降级，存在可替代路径（30 分钟内恢复）。
- `P3`：非核心功能异常或告警噪声（当日修复）。

## 4. 角色与职责
- `Ops-Agent`：故障响应指挥，执行恢复命令，更新运行状态。
- `Backend-Agent`：接口与服务修复，定位应用错误。
- `Algo-Agent`：模型与推理链路回退/恢复。
- `PM-Agent`：跨团队协调、对外状态同步、里程碑调整。
- `Test-Agent`：恢复后门禁验证与证据归档。

## 5. 触发条件
- `health` 连续失败。
- 监控出现 `critical` 告警。
- 灰度窗口内成功率低于 99% 或 P95 >= 1000ms。

## 6. 处置流程
1. **发现与确认（0-1分钟）**
- 读取监控告警与运行状态。
- 执行快速检查：`monitoring_check.ps1`。

2. **隔离与止血（1-2分钟）**
- 停止异常实例：`stop_env.ps1`。
- 如灰度期间触发，立即执行回滚流程。

3. **恢复服务（2-5分钟）**
- 启动恢复：`start_env.ps1`。
- 立即执行 `smoke_api.ps1` 与 `monitoring_check.ps1`。
- 若失败，升级为 `P1` 并执行上一个稳定版本恢复。

4. **验证与关闭（5分钟后）**
- 核心链路通过后更新状态为已恢复。
- 归档证据文件并补齐 `testlog/releaselog`。

## 7. 应急命令模板
```powershell
.\ops\scripts\stop_env.ps1 -EnvName dev
.\ops\scripts\start_env.ps1 -EnvName dev -NoInstall
.\ops\scripts\smoke_api.ps1 -EnvName dev
.\ops\scripts\monitoring_check.ps1 -EnvName dev
```

## 8. 演练与复盘要求
- 每次里程碑至少 1 次完整应急演练。
- 演练证据统一归档为：`ops/artifacts/o1_5_runbook_drill_<env>.json`
- 复盘记录最少包含：故障时间线、根因、恢复耗时、改进项。

