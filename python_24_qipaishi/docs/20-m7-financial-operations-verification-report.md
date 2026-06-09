# M7 财务运营验证报告

## 交付范围

本轮继续 M7，在上一轮商家工作台统计、异常列表和审计查询基础上，补齐财务运营首版：提现状态机、后台人工调账、后台发券和会员消费画像。

已实现：

- 提现流程：
  - `withdrawals` 表
  - `GET /api/v1/withdrawals`
  - `GET /api/v1/withdrawals/me`
  - `POST /api/v1/withdrawals`
  - `POST /api/v1/withdrawals/{withdrawal_id}/approve`
  - `POST /api/v1/withdrawals/{withdrawal_id}/reject`
  - `POST /api/v1/withdrawals/{withdrawal_id}/mark-paid`
  - 提现审批时扣减现金余额，并写入 `wallet_ledgers`
- 后台人工调账：
  - `POST /api/v1/wallets/admin/adjustments`
  - 支持现金余额和赠送余额的人工加款/扣款
  - 写审计日志和钱包流水，流水 `biz_type=manual_adjustment`
- 后台发券：
  - `POST /api/v1/coupons/admin/issue`
  - 支持按券模板给指定会员发券，可选择是否执行单用户领取上限
- 会员运营查询：
  - `GET /api/v1/members`
  - `GET /api/v1/members/{user_id}`
  - 返回余额、订单量、完成订单量、累计消费、优惠券数量和最近订单/流水 ID
- 异常列表增强：
  - `GET /api/v1/operations/exceptions` 支持 `source=withdrawal`
  - 待审核或待打款超过 24 小时的提现单进入异常列表
- Alembic 迁移：
  - `20260515_0012_withdrawals.py`

## 当前边界

- 提现打款目前为人工确认，不直接接真实微信/银行出款接口。
- 提现审批时扣减现金余额，未实现冻结余额字段；如果后续需要“申请即冻结”，需要扩展钱包账户冻结余额。
- 会员查询首版返回聚合画像和最近 ID，后续 Web 后台可进一步接入分页明细。
- 后台发券复用现有券模板，不新增营销活动批量投放规则。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic upgrade head
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
QIPAISHI_DATABASE_URL=sqlite:////tmp/qipaishi_m7_finance_0012.db conda run -n anti-spoofing_scc_175 alembic upgrade head
```

结果：

```text
pytest: 63 passed
ruff: All checks passed
mypy: Success: no issues found in 122 source files
smoke: smoke ok
alembic: 20260515_0012 (head)
OpenAPI paths: 93
```

## 下一步

继续 M7 收尾和 M8 衔接：

1. 增加后台订单改时和更细的人工补偿入口。
2. 将会员、提现、发券和异常列表接入 M8 商家 Web 后台。
3. 后续真实支付/出款接入时，补提现回调、冻结余额和出款失败补偿。
