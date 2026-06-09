# M3 预约订单核心验证报告

## 交付范围

本轮完成预约订单核心链路的完整首版后端能力：可用性检查、价格试算、预订单、正式下单契约、待支付库存锁、续费、换房、待支付过期释放和基础订单状态机。

已实现：

- 订单模型：`orders`
- 订单明细：`order_items`
- 房间时段锁：`room_time_locks`
- Alembic 迁移：`20260514_0004_order_booking_core.py`
- Pricing Service：
  - 按房间 active 价格规则报价
  - 支持工作日覆盖价
  - 支持最小时长
  - 返回可解释价格明细
- Availability Service：
  - 校验时间范围
  - 检查房间不可预约时段
  - 检查未过期待支付锁和已占用锁
  - 返回冲突原因
- 订单状态机首版：
  - `pending_payment`
  - `paid`
  - `in_use`
  - `completed`
  - `cancelled`
- 续费能力：
  - `renew/quote` 只计算订单结束后的增量时段
  - `renew` 追加订单明细并为增量时段创建占用锁
- 换房能力：
  - `change-room/quote` 试算新房间同一时段价格和差额
  - `change-room` 同事务释放旧锁并创建新房间锁
- 待支付过期释放：
  - 过期待支付订单置为 `cancelled`
  - 待支付锁置为 `expired`
- API：
  - `GET /api/v1/availability/rooms`
  - `POST /api/v1/pricing/quote`
  - `GET /api/v1/orders`
  - `POST /api/v1/orders/preorder`
  - `POST /api/v1/orders`
  - `POST /api/v1/orders/expire-pending`
  - `GET /api/v1/orders/{order_id}`
  - `POST /api/v1/orders/{order_id}/renew/quote`
  - `POST /api/v1/orders/{order_id}/renew`
  - `POST /api/v1/orders/{order_id}/change-room/quote`
  - `POST /api/v1/orders/{order_id}/change-room`
  - `POST /api/v1/orders/{order_id}/cancel`
  - `POST /api/v1/orders/{order_id}/mock-pay`
  - `POST /api/v1/orders/{order_id}/start`
  - `POST /api/v1/orders/{order_id}/complete`

## 业务边界

- `preorder` 创建 `pending_payment` 订单，并同步创建 `pending_payment` 房间时段锁。
- 待支付锁默认 15 分钟过期。
- `mock-pay` 仅用于 M3/M4 前的开发联调，会将订单置为 `paid`，并将时段锁置为 `occupied`。
- 取消订单会释放待支付或已占用锁。
- 完成订单会释放当前锁；后续 M6 会接入保洁任务和房态联动。
- 续费只检查当前订单结束后的新增时段，不和原订单时段重复冲突。
- 换房限制在同一门店内，新房间必须处于 active 状态，且目标时段没有冲突。
- M3 的换房差额只记录在订单明细中；差额支付、退款和资金闭环进入 M4/M7 处理。
- 当前仍是应用层重叠检查；生产 PostgreSQL 阶段建议补排他约束或事务锁加强并发安全。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic upgrade head
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
QIPAISHI_DATABASE_URL=sqlite:////tmp/qipaishi_m3_full_migration.db conda run -n anti-spoofing_scc_175 alembic upgrade head
```

结果：

```text
pytest: 16 passed
ruff: All checks passed
mypy: Success: no issues found in 65 source files
smoke: smoke ok
alembic: 20260514_0004 (head)
OpenAPI paths: 36
```

## 下一步

进入 M4 支付、资金与营销：

1. 建立 `payments`、`payment_events` 和 `refunds`。
2. 将当前 `mock-pay` 收敛到支付 provider 层，保留 mock provider 用于测试。
3. 支付成功回调幂等确认订单，并把锁从待支付转为占用。
4. 将 M3 的 `expire-pending` 服务接入 Worker 周期任务。
5. 再进入余额、优惠券和团购码核销。
