# M5/M6 衔接验证报告

## 交付范围

本轮在 M5 设备控制首版基础上，补齐设备侧生产联调所需的直控、重试和防重复能力，并启动 M6 保洁任务闭环首版，让保洁开门复用同一套 `DeviceCommand`。

已实现：

- M5 衔接增强：
  - `POST /api/v1/devices/{device_id}/test`
  - `POST /api/v1/devices/{device_id}/open`
  - `POST /api/v1/devices/{device_id}/close`
  - `POST /api/v1/device-commands/{command_id}/retry`
  - 无 `idempotency_key` 的同设备、同操作者、同业务、同命令 10 秒内自动去重
  - `mock_fail` 设备可稳定模拟失败，便于重试和异常测试
- M6 保洁任务首版：
  - `cleaning_tasks`
  - `cleaning_proofs`
  - 订单完成时自动生成保洁任务
  - `GET /api/v1/cleaning/tasks`
  - `POST /api/v1/cleaning/tasks/{task_id}/accept`
  - `POST /api/v1/cleaning/tasks/{task_id}/start`
  - `POST /api/v1/cleaning/tasks/{task_id}/open-door`
  - `POST /api/v1/cleaning/tasks/{task_id}/complete`
  - `POST /api/v1/cleaning/tasks/{task_id}/review`
  - `POST /api/v1/cleaning/tasks/{task_id}/settle`
- 保洁设备授权：
  - 保洁任务状态为 `accepted` 或 `in_progress` 时可开房门
  - 仅任务分配的保洁员可执行任务开门
  - 保洁开门写入 `device_commands` 和审计日志
- Alembic 迁移：`20260515_0009_cleaning_workflow.py`

## 当前边界

- 保洁任务已经具备核心状态机，但房态联动、清洁 SLA、投诉、结算金额还未细化。
- 设备命令已有短时间去重和失败重试，但还未做设备供应商级限流、指数退避和告警聚合。
- 商家直控设备已经支持测试、开、关；后续真实供应商接入时需要按 provider 分派 adapter。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic upgrade head
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
QIPAISHI_DATABASE_URL=sqlite:////tmp/qipaishi_m5_m6_bridge.db conda run -n anti-spoofing_scc_175 alembic upgrade head
```

结果：

```text
pytest: 45 passed
ruff: All checks passed
mypy: Success: no issues found in 102 source files
smoke: smoke ok
alembic: 20260515_0009 (head)
OpenAPI paths: 73
```

## 下一步

继续 M6 完整化：

1. 房间清洁状态与可预约策略联动。
2. 保洁任务取消、驳回后重新派单、投诉和结算金额。
3. 保洁任务 SLA、积压列表和 Hermes 只读摘要。
4. 设备真实 provider adapter 和设备失败告警聚合。
