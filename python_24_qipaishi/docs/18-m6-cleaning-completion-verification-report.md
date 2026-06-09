# M6 保洁完整化验证报告

## 交付范围

本轮在 M5/M6 衔接版本的保洁任务首版基础上，补齐保洁和房态联动的核心闭环，让订单完成后的房间清洁状态、可预约策略、返工、投诉、结算和保洁看板具备可运营的服务端能力。

已实现：

- 房间清洁状态：
  - `rooms.cleaning_status`
  - 新房间默认 `clean`
  - 订单完成并生成保洁任务时，房间自动标记为 `dirty`
  - 保洁审核通过后，房间自动恢复为 `clean`
- 可预约策略联动：
  - 脏房默认不可预约
  - 可用性冲突原因返回 `room_needs_cleaning`
  - 门店 `cleaning_settings.allow_dirty_booking` 或 `allow_unclean_booking` 可放行脏房预约
- 保洁任务完整化：
  - 订单完成自动生成保洁任务
  - 订单取消且已开始使用时自动生成保洁任务
  - 商家可人工触发保洁任务：`POST /api/v1/orders/{order_id}/cleaning-task`
  - 保洁员取消接单：`POST /api/v1/cleaning/tasks/{task_id}/unaccept`
  - 商家取消未终态保洁任务：`POST /api/v1/cleaning/tasks/{task_id}/cancel`
  - 驳回任务支持重新派单：`POST /api/v1/cleaning/tasks/{task_id}/reassign`
  - 已提交、已完成、已结算任务支持投诉：`POST /api/v1/cleaning/tasks/{task_id}/complain`
  - 结算支持金额：`settlement_amount`
  - 投诉和取消记录原因和时间：`complaint_reason`、`complained_at`、`cancel_reason`、`canceled_at`
- 保洁开门授权：
  - 保洁开门要求任务为 `accepted` 或 `in_progress`
  - 仅任务分配的保洁员可开门
  - 开门时间限制在任务计划开始前 15 分钟到计划结束后 8 小时内
- 保洁运营摘要：
  - `GET /api/v1/cleaning/summary`
  - 返回待处理、进行中、超时、投诉数量和超时任务 ID
- Alembic 迁移：
  - `20260515_0010_cleaning_completion.py`
  - `20260515_0011_cleaning_cancellation.py`

## 当前边界

- 保洁任务已有超时判断、摘要接口和默认开门窗口，但还未引入自动告警、推送通知、升级规则和 SLA 配置表。
- 投诉已经进入任务状态机，但还未拆出独立投诉工单、赔付和客服处理记录。
- 结算金额已落库，但提现、保洁员账户和月结批处理将在 M7 商家运营/财务阶段继续扩展。
- Hermes Agent 目前可基于 API 做只读摘要，后续可在 M7 接入经营统计和异常解释。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic upgrade head
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
QIPAISHI_DATABASE_URL=sqlite:////tmp/qipaishi_m6_completion_0011.db conda run -n anti-spoofing_scc_175 alembic upgrade head
```

结果：

```text
pytest: 55 passed
ruff: All checks passed
mypy: Success: no issues found in 104 source files
smoke: smoke ok
alembic: 20260515_0011 (head)
OpenAPI paths: 79
```

## 下一步

进入 M7 商家运营统计：

1. 建立商家工作台摘要 API，覆盖订单、收入、退款、房间使用率、设备异常和保洁积压。
2. 补会员、充值规则、提现申请和财务对账接口。
3. 将保洁投诉、设备失败、支付退款异常纳入统一运营异常列表。
4. 为 Hermes Agent 暴露只读运营摘要和异常解释数据源。
