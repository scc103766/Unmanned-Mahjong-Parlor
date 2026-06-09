# M4 支付核心验证报告

## 交付范围

本轮在 M3 完整后正式进入 M4，先完成支付和退款的核心表、mock 微信支付 provider 风格接口，以及支付回调确认订单的最小闭环。

已实现：

- 支付单：`payments`
- 支付事件：`payment_events`
- 退款单：`refunds`
- Alembic 迁移：`20260514_0005_payment_core.py`
- Mock 微信预支付：
  - `POST /api/v1/payments/wechat/prepay`
  - 支持 `idempotency_key`
  - 仅允许 `pending_payment` 订单创建支付单
- Mock 微信支付回调：
  - `POST /api/v1/payments/wechat/callback`
  - 通过 `provider_event_id` 做事件幂等
  - 支付成功后确认订单，并将房间锁从待支付转为占用
- 支付查询：
  - `GET /api/v1/payments/{payment_id}`
- 退款申请：
  - `POST /api/v1/payments/{payment_id}/refund`
  - 校验支付单已支付
  - 校验累计退款不超过支付金额

## 当前边界

- 本阶段仍是 mock 微信支付，用于替代 M3 的 `mock-pay` 继续联调。
- 支付回调接口目前没有真实微信签名验签；真实 provider 接入时必须补签名验证、证书/平台证书处理和回调重放防护。
- 退款当前只创建退款单，不模拟退款回调落账；后续 M4 继续补退款 provider 和回调状态机。
- 余额、优惠券、团购码还未进入本轮，属于 M4 后续小步。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic upgrade head
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
QIPAISHI_DATABASE_URL=sqlite:////tmp/qipaishi_m4_payment_migration.db conda run -n anti-spoofing_scc_175 alembic upgrade head
```

结果：

```text
pytest: 20 passed
ruff: All checks passed
mypy: Success: no issues found in 71 source files
smoke: smoke ok
alembic: 20260514_0005 (head)
OpenAPI paths: 40
```

## 下一步

继续 M4：

1. 将 M3 的 `mock-pay` 标记为开发辅助接口，主线改用 `payments/wechat/prepay` + `payments/wechat/callback`。
2. 补退款回调和支付关闭接口。
3. 建立余额账户和余额流水。
4. 建立优惠券模板、用户券、锁券、核销和退回流程。
5. 建立团购码验证、锁定、核销和退回流程。
