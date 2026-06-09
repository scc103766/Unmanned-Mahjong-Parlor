# M7 商家运营统计验证报告

## 交付范围

本轮进入 M7，先交付可直接支撑商家后台和平台后台的运营统计 API。实现策略是不新增聚合表，优先基于订单、支付、退款、钱包流水、房间、设备命令、保洁任务和审计日志这些事实表实时聚合，保证统计口径可追溯。

已实现：

- 商家工作台统计：
  - `GET /api/v1/analytics/dashboard`
  - 支持按 `tenant_id`、`store_id`、`start_at`、`end_at` 查询
  - 返回订单量、已支付/使用中/已完成/已取消订单数
  - 返回支付收入、退款金额、净收入、钱包充值金额
  - 返回会员数、房间数、活跃房间数、脏房数
  - 返回房间使用小时数和使用率
  - 返回保洁待处理、超时、已完成、投诉数量
  - 返回设备失败命令数量
- 房间使用率统计：
  - `GET /api/v1/analytics/rooms/usage`
  - 按房间返回订单数、使用小时数和使用率
- 保洁统计：
  - `GET /api/v1/analytics/cleaning`
  - 返回保洁任务各状态数量、超时数量和已结算金额
- 平台/商家异常列表：
  - `GET /api/v1/operations/exceptions`
  - 支持支付卡住、退款失败/卡住、设备命令失败、保洁超时、保洁投诉
  - 支持按租户、门店、来源和时间过滤
- 审计查询：
  - `GET /api/v1/operations/audit-logs`
  - 支持按租户、操作者、动作、目标类型、时间和数量限制过滤
- 权限边界：
  - 商家、店员、客服可查租户内运营统计
  - 平台管理员可通过 `tenant_id` 查询指定租户统计，异常和审计可跨租户查看
- 新增测试：
  - M7 路由注册
  - 商家工作台聚合口径
  - 房间使用率计算
  - 支付、退款、设备、保洁异常来源

## 当前边界

- 本轮未新增聚合表和缓存，统计基于事实表实时计算；后续数据量上来后可增加日聚合表。
- 提现申请、审核、打款确认、驳回尚未实现，会作为 M7 财务运营下一步补齐。
- 后台订单处理已有取消、续费、换房、人工完成和退款入口；更细的改时、人工补偿入口后续继续增强。
- 会员列表、消费记录和优惠券发放已有用户、订单、优惠券基础模块，后续需要补专门后台查询接口。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
```

结果：

```text
pytest: 59 passed
ruff: All checks passed
mypy: Success: no issues found in 112 source files
smoke: smoke ok
alembic: 20260515_0011 (head)
OpenAPI paths: 84
```

## 下一步

继续 M7 财务运营和后台操作补齐：

1. 实现提现申请、审核、驳回和打款确认。
2. 增加会员列表、消费记录和后台优惠券发放 API。
3. 增加更细的后台订单改时和人工补偿入口。
4. 为 M8 商家 Web 后台接入工作台、异常列表和审计查询。
