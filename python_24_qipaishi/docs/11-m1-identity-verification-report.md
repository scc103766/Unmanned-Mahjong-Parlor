# M1 租户与权限验证报告

## 交付范围

本轮按 BMAD 路线图进入 M1，完成后续门店、房间、订单、设备和保洁模块所需的身份与数据作用域底座。

已实现：

- Mock 微信登录：`POST /api/v1/auth/wechat-login`
- 开发期租户 bootstrap：`POST /api/v1/auth/dev-bootstrap`
- 当前身份：`GET /api/v1/me` 和 `GET /api/v1/auth/me`
- 租户管理：`GET/POST /api/v1/tenants`、`GET/PATCH /api/v1/tenants/{tenant_id}`
- 租户应用绑定：`GET/POST /api/v1/tenants/{tenant_id}/apps`
- 角色列表：`GET /api/v1/roles`
- 用户查询、角色替换和门店作用域替换：`/api/v1/users/**`
- HMAC 签名 access token，payload 包含 `user_id`、`tenant_id`、角色和门店作用域
- 可复用权限依赖：`get_current_principal`、`require_roles`、`require_store_scope`
- 审计写入工具：`write_audit_log`
- 标准角色迁移：`platform_admin`、`merchant_admin`、`clerk`、`cleaner`、`customer`、`support`

## 安全边界

- `wechat-login` 通过 `client_type + app_id` 查找服务端 `TenantApp`，不直接信任前端传入租户。
- `dev-bootstrap` 仅在非 `prod` 环境开放，用于本地和试开发阶段生成首个租户与管理员 token。
- 平台管理员可跨租户；商家和客服默认只能访问自身 `tenant_id`。
- 店员和保洁后续业务接口应复用 `require_store_scope`，确保门店级数据授权。
- 租户、租户应用、用户角色和门店作用域变更均写审计日志。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:////tmp/qipaishi_m1_migration.db conda run -n anti-spoofing_scc_175 alembic upgrade head
```

结果：

```text
pytest: 6 passed
ruff: All checks passed
mypy: Success: no issues found in 42 source files
smoke: smoke ok
alembic: 20260514_0002 (head)
```

## 下一步

进入 M2 门店、房间和价格配置：

1. 新增 `stores`、`rooms`、`room_price_rules`、`room_blocked_slots`、设备绑定占位表。
2. 商家接口复用 `require_roles("merchant_admin", "clerk")` 和 `require_store_scope`。
3. 顾客接口只暴露可预约门店、房间和价格摘要，不允许前端裁决库存。
4. 所有门店、房间、价格和不可预约时段变更继续写审计。
