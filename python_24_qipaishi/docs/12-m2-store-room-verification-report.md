# M2 门店房间配置验证报告

## 交付范围

本轮完成门店、房间、价格规则和不可预约时段的后端基础能力，为 M3 可用性、价格试算和预约订单状态机提供配置数据。

已实现：

- 门店模型与接口：`stores`
- 房间模型与接口：`rooms`
- 房间价格规则：`room_price_rules`
- 房间不可预约时段：`room_blocked_slots`
- Alembic 迁移：`20260514_0003_store_room_config.py`
- API：
  - `GET /api/v1/stores`
  - `POST /api/v1/stores`
  - `GET /api/v1/stores/{store_id}`
  - `PATCH /api/v1/stores/{store_id}`
  - `GET /api/v1/rooms`
  - `POST /api/v1/rooms`
  - `GET /api/v1/rooms/{room_id}`
  - `PATCH /api/v1/rooms/{room_id}`
  - `POST /api/v1/rooms/{room_id}/price-rules`
  - `POST /api/v1/rooms/{room_id}/blocked-slots`
- 门店和房间写操作审计。
- 租户隔离：非平台用户只能访问自身 `tenant_id` 下的数据。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic upgrade head
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
QIPAISHI_DATABASE_URL=sqlite:////tmp/qipaishi_m2_migration.db conda run -n anti-spoofing_scc_175 alembic upgrade head
```

结果：

```text
pytest: 9 passed
ruff: All checks passed
mypy: Success: no issues found in 51 source files
smoke: smoke ok
alembic: 20260514_0003 (head)
```

## 下一步

进入 M3 预约订单核心：

1. 建立 `room_time_locks`、`orders` 和 `order_items`。
2. 实现 Availability Service，综合门店营业参数、房间不可预约时段和有效订单锁。
3. 实现 Pricing Service，基于 `room_price_rules` 返回价格明细。
4. 实现预订单和待支付库存锁，增加并发冲突测试。
5. 订单状态机从 `pending_payment`、`paid`、`in_use`、`completed`、`cancelled` 起步。
