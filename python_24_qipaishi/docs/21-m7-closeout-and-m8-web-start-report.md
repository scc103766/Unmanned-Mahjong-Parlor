# M7 收尾与 M8 Web 启动报告

## 交付范围

本轮完成 M7 收尾，并启动 M8 Web 开发。后端补齐后台订单改时和统一人工补偿入口；前端创建 `web/` 首版工程，提供可预览的商家运营工作台。

已实现：

- 后台订单改时：
  - `POST /api/v1/orders/{order_id}/reschedule/quote`
  - `POST /api/v1/orders/{order_id}/reschedule`
  - 支持 `pending_payment` 和 `paid` 订单改时
  - 改时会重算价格、记录差额订单明细、重建房间时间锁并写审计
  - 库存冲突检查支持排除当前订单自身时间锁
- 统一人工补偿：
  - `POST /api/v1/operations/compensations`
  - 支持现金余额补偿、赠送余额补偿和可选后台发券
  - 复用钱包流水和优惠券模板，并写审计
- M8 Web W0 首版：
  - `web/package.json`
  - `web/index.html`
  - `web/src/main.js`
  - `web/src/styles.css`
  - `web/README.md`
  - 首屏为商家运营工作台，包含指标、异常、提现、会员和人工补偿入口
  - 可填写 API Base 和 Token 连接 `/api/v1/**`，无 Token 时展示本地演示数据

## 当前边界

- M8 当前为无依赖静态首版，先保证页面可启动和 API 对接结构清晰；后续可升级为 Vue 3 + Vite + TypeScript。
- 商家工作台页面只完成首屏壳和核心数据对接，尚未实现完整路由、权限守卫和所有业务页面。
- 后台订单改时只开放给未开始使用的 `pending_payment`、`paid` 订单；使用中订单仍通过续费、换房、完成等既有接口处理。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
python3 -m json.tool web/package.json
```

结果：

```text
pytest: 64 passed
ruff: All checks passed
mypy: Success: no issues found in 122 source files
smoke: smoke ok
alembic: 20260515_0012 (head)
OpenAPI paths: 96
web preview: http://127.0.0.1:5173 -> 200
```

## 下一步

继续 M8：

1. 将 `web/` 升级到 Vue 3 + Vite + TypeScript 正式结构。
2. 增加登录态、权限守卫、API client 和错误处理。
3. 完成商家后台工作台、订单列表、会员列表、提现列表和异常列表页面。
4. 并行启动顾客 H5 与保洁移动网页的核心流程页面。
