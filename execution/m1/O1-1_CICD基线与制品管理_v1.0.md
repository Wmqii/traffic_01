# O1-1 CI/CD基线与制品管理（v1.0）

## 1. 文档信息
- 文档编号：`O1-1`
- 文档版本：`v1.0`
- 生效日期：`2026-03-26`
- 责任 Agent：`Ops-Agent`

## 2. 目标
- 建立可执行的 CI 基线，保证 M1 文档与执行资产可持续校验。
- 建立制品管理规则，确保每次发布有可追踪产物与保留策略。
- 打通“提交 -> 校验 -> 归档”最小流水线闭环。

## 3. CI/CD 基线范围
- CI（持续集成）：
  - 必备文件完整性检查
  - 执行资产（任务板/日志）结构检查
  - 产物归档（Artifacts）
- CD（持续交付）：
  - 文档制品打包（Zip）
  - 发布记录写入与版本标识

## 4. 流水线定义

### 4.1 CI 流水线（`.github/workflows/ci.yml`）
- 触发：`push`、`pull_request`、`workflow_dispatch`
- 任务：
  - 执行 `scripts/ci/smoke_check.ps1`
  - 上传执行资产与制品清单

### 4.2 发布流水线（`.github/workflows/release_docs.yml`）
- 触发：`workflow_dispatch`
- 输入：`version`
- 任务：
  - 打包 `execution/`、核心方案文档与 CSV
  - 上传发布制品

## 5. 制品管理规则

| 制品类型 | 路径 | 命名规则 | 保留策略 |
|---|---|---|---|
| 执行资产 | `execution/**` | 原文件名 | 180天 |
| 文档包 | `dist/release-<version>.zip` | 版本号命名 | 365天 |
| 校验结果 | `ops/artifacts/ci_smoke_result.json` | 固定名（按提交覆盖） | 90天 |
| 制品清单 | `ops/artifacts/artifact_manifest_v1.json` | 版本化 | 长期保留 |

## 6. 准入与准出标准
- 准入：目录结构与执行文档已存在，脚本可运行。
- 准出：
  - 基线校验脚本本地执行 `PASS`
  - 流水线模板文件创建完成
  - 发布与制品规则文档化
  - 评审记录完成并归档

## 7. 关联文件
- [.github/workflows/ci.yml](d:\小桌面\交通拥堵\.github\workflows\ci.yml)
- [.github/workflows/release_docs.yml](d:\小桌面\交通拥堵\.github\workflows\release_docs.yml)
- [smoke_check.ps1](d:\小桌面\交通拥堵\scripts\ci\smoke_check.ps1)
- [artifact_manifest_v1.json](d:\小桌面\交通拥堵\ops\artifacts\artifact_manifest_v1.json)
- [O1-1_验证记录_2026-03-26.md](d:\小桌面\交通拥堵\execution\m1\O1-1_验证记录_2026-03-26.md)
- [M1_评审记录_2026-03-26_第3轮.md](d:\小桌面\交通拥堵\execution\m1\M1_评审记录_2026-03-26_第3轮.md)

