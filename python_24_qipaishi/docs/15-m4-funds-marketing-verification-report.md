# M4 资金与营销验证报告

## 交付范围

本轮继续 M4，在支付核心之后补齐余额账户、余额流水、优惠券和团购码的后端基础能力，并把营销抵扣接入支付预下单、支付成功、支付关闭和退款回调。

已实现：

- 支付补充：
  - `POST /api/v1/payments/{payment_id}/close`
  - `POST /api/v1/payments/refunds/callback`
  - `POST /api/v1/payments/wechat/prepay` 支持 `group_buy_code_id`、`coupon_id`、`wallet_amount`
  - 支付单保存原始金额、微信实付金额和抵扣快照
  - 抵扣顺序：团购码 -> 优惠券 -> 余额 -> mock 微信支付
  - 支付关闭会取消待支付订单并释放锁
  - 退款回调通过 `provider_event_id` 幂等处理
  - 支付回调和退款回调支持 HMAC 签名、时间窗和 nonce 字段，生产环境默认要求签名
  - 退款创建支持 `idempotency_key`，并通过数据库唯一约束保证同租户幂等
  - 微信实付累计退满后退回余额、优惠券和团购码；零元抵扣支付支持零金额退款单触发权益退回
- 余额：
  - `wallet_accounts`
  - `wallet_ledgers`
  - `GET /api/v1/wallets/me`
  - `POST /api/v1/wallets/recharge`
  - `GET /api/v1/wallets/me/ledgers`
- 优惠券：
  - `coupon_templates`
  - `coupons`
  - `GET/POST /api/v1/coupon-templates`
  - `GET /api/v1/coupons/me`
  - `POST /api/v1/coupons/claim`
  - `POST /api/v1/coupons/{coupon_id}/lock`
  - `POST /api/v1/coupons/{coupon_id}/use`
  - `POST /api/v1/coupons/{coupon_id}/return`
- 团购码：
  - `group_buy_codes`
  - `GET/POST /api/v1/group-buy/codes`
  - `POST /api/v1/group-buy/verify`
  - `POST /api/v1/group-buy/codes/{code_id}/lock`
  - `POST /api/v1/group-buy/codes/{code_id}/use`
  - `POST /api/v1/group-buy/codes/{code_id}/return`
- Alembic 迁移：
  - `20260515_0006_wallet_coupon_group_buy.py`
  - `20260515_0007_payment_hardening.py`

## 当前边界

- 余额充值仍是 mock 充值，用于开发期闭环和后续支付 provider 接入前验证流水口径。
- 优惠券、团购码和余额已经接入支付金额拆分，但当前仍以单支付单快照为主，后续如果支持多支付单或复杂售后，需要补更细的资金分摊表。
- 退款规则当前采用 M4 简化口径：微信实付部分支持部分退款；微信实付退满后再退回余额和营销权益。
- 当前 HMAC 签名用于 mock provider 和生产联调占位；真实微信支付仍需按微信平台证书、公钥、回调报文和请求头完成正式验签。

## 生产化配置

新增环境变量：

- `QIPAISHI_PAYMENT_CALLBACK_SECRET`：mock provider 回调 HMAC 密钥，默认仅适合开发。
- `QIPAISHI_PAYMENT_CALLBACK_SIGNATURE_REQUIRED`：是否强制回调签名；`dev/local/test` 默认关闭，其他环境默认开启。
- `QIPAISHI_PAYMENT_CALLBACK_TOLERANCE_SECONDS`：回调时间戳允许偏差，默认 300 秒。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic upgrade head
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
QIPAISHI_DATABASE_URL=sqlite:////tmp/qipaishi_m4_full_migration.db conda run -n anti-spoofing_scc_175 alembic upgrade head
```

结果：

```text
pytest: 31 passed
ruff: All checks passed
mypy: Success: no issues found in 89 source files
smoke: smoke ok
alembic: 20260515_0007 (head)
OpenAPI paths: 56
```

## 下一步

M4 后续只保留真实外部渠道接入项，主体可进入 M5 设备控制：

1. 真实微信支付和退款 provider：平台证书、公钥验签、主动查单、主动关单和退款查询。
2. 退款运营审批流和对账导出。
3. 引入数据库级集成测试后，补支付抵扣、退款返还和余额流水的事务级用例。
4. 进入 M5：设备、门锁、电源命令表、mock 适配器、订单授权开门。
