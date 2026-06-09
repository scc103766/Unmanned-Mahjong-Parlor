# M8 Web 正式工程化验证报告

## 交付范围

本轮将 `web/` 从静态首版升级为 Vue 3 + Vite + TypeScript 正式工程，并接入 M7 已完成的商家运营能力。

已实现：

- 工程底座：
  - `vite.config.ts`
  - `tsconfig.json`
  - `src/main.ts`
  - `src/App.vue`
  - `package.json` 构建、类型检查和预览脚本
- 应用分层：
  - `src/app/router`：商家后台路由
  - `src/app/stores`：Pinia 会话状态和本地持久化
  - `src/app/permissions`：基于角色的路由守卫
  - `src/core/api`：Axios API client、响应解包、错误封装和接口类型
  - `src/layouts/merchant`：商家后台主布局
  - `src/modules/merchant/views`：运营页面
  - `src/shared/utils`：金额、百分比、时间和状态格式化
- 商家后台页面：
  - 运营总览：收入、订单、会员、房间利用率、保洁/设备摘要、异常和待提现
  - 订单管理：订单列表、后台改时试算和确认
  - 会员运营：会员消费画像、余额/券概览、统一人工补偿
  - 提现审核：状态筛选、通过、驳回和打款确认
  - 异常与审计：异常来源筛选、异常列表和审计日志
  - 连接设置：API 地址、开发登录、当前身份读取
- 联调边界：
  - 有 Bearer Token 时调用 `/api/v1/**` 后端接口
  - 无 Bearer Token 时使用本地演示数据，便于前端独立预览
  - `dev-bootstrap` 会写入租户、用户、角色和 token，适合本地开发联调

## 覆盖的后端接口

- `POST /api/v1/auth/dev-bootstrap`
- `GET /api/v1/auth/me`
- `GET /api/v1/analytics/dashboard`
- `GET /api/v1/analytics/rooms/usage`
- `GET /api/v1/analytics/cleaning`
- `GET /api/v1/operations/exceptions`
- `GET /api/v1/operations/audit-logs`
- `POST /api/v1/operations/compensations`
- `GET /api/v1/orders`
- `POST /api/v1/orders/{order_id}/reschedule/quote`
- `POST /api/v1/orders/{order_id}/reschedule`
- `GET /api/v1/members`
- `GET /api/v1/withdrawals`
- `POST /api/v1/withdrawals/{withdrawal_id}/approve`
- `POST /api/v1/withdrawals/{withdrawal_id}/reject`
- `POST /api/v1/withdrawals/{withdrawal_id}/mark-paid`

## 当前边界

- M8 本轮重点是正式前端工程化和商家运营后台；顾客 H5、保洁移动网页和平台后台仍待后续 M8 子阶段展开。
- 当前 UI 使用轻量自研样式，尚未引入 Element Plus、图表库或端到端测试。
- 前端权限守卫用于体验层导航约束，最终权限、租户隔离、资金和设备操作仍以后端裁决为准。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
conda run -n anti-spoofing_scc_175 pytest tests/test_m8_web_engineering.py -q
npm install
npm run build
```

结果：

```text
ruff: All checks passed
mypy: Success, 122 source files
pytest: 68 passed
smoke: smoke ok
alembic: 20260515_0012 (head)
M8 web structure test: 3 passed
npm install: 80 packages, 0 vulnerabilities
npm build: vite build passed
web dev preview: http://localhost:5173/ -> 200
api dev server: http://127.0.0.1:8000/health -> 200, CORS allows 5173
```

## 下一步

1. 完成 M8 顾客 H5：选房、价格试算、下单、支付、订单详情和开门入口。
2. 完成 M8 保洁移动页：任务列表、接单、开始、开门、上传凭证、完成和审核反馈。
3. 补平台后台：租户、角色、应用绑定、异常、审计和人工补偿。
4. 引入 Vitest/Playwright，对关键运营页面和权限流做自动化验证。
