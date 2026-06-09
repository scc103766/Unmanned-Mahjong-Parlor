# Python 24H 无人棋牌室管理系统

本目录用于承接 `../24h_qipaishi` 的 BMAD 梳理结果，制定 Python 版本的后续开发计划。当前目标调整为先建设 Python 后端 + 网页端的无人棋牌室系统，功能与参考项目一致，并具备更完整的服务端能力、审计能力和多租户部署能力。App 作为后续深化移植阶段。

## 文档地图

- [docs/index.md](docs/index.md)：规划入口与文档索引。
- [docs/00-bmad-input-summary.md](docs/00-bmad-input-summary.md)：当前 BMAD 产物摘要与关键结论。
- [docs/01-development-plan.md](docs/01-development-plan.md)：分阶段开发计划、里程碑和验收边界。
- [docs/02-python-architecture-plan.md](docs/02-python-architecture-plan.md)：Python 技术架构、模块边界和运行拓扑。
- [docs/03-domain-model-plan.md](docs/03-domain-model-plan.md)：核心领域模型、状态机和业务约束。
- [docs/04-api-implementation-plan.md](docs/04-api-implementation-plan.md)：API 分组、参考项目兼容策略和接口优先级。
- [docs/05-epics-and-backlog.md](docs/05-epics-and-backlog.md)：可拆分执行的 Epic、Story 和首轮 Sprint。
- [docs/06-next-development-roadmap.md](docs/06-next-development-roadmap.md)：后续落地路线图、Sprint 拆解、验收和上线检查。
- [docs/07-web-client-plan.md](docs/07-web-client-plan.md)：当前网页端开发计划和后续 App 迁移策略。
- [docs/07-app-client-plan.md](docs/07-app-client-plan.md)：后续 PC 与手机端 App 迁移储备计划。
- [docs/08-environment-download-checklist.md](docs/08-environment-download-checklist.md)：M0 环境下载、依赖补全和验证命令清单。
- [docs/09-m0-verification-report.md](docs/09-m0-verification-report.md)：M0 后端、迁移和 Flutter 储备验证结果。
- [docs/10-hermes-agent-usage-plan.md](docs/10-hermes-agent-usage-plan.md)：Hermes Agent 在研发、运维、运营和后续智能助手中的使用边界。
- [docs/11-m1-identity-verification-report.md](docs/11-m1-identity-verification-report.md)：M1 租户、身份、角色、门店作用域和审计底座验证结果。
- [docs/12-m2-store-room-verification-report.md](docs/12-m2-store-room-verification-report.md)：M2 门店、房间、价格规则和不可预约时段验证结果。
- [docs/13-m3-booking-core-verification-report.md](docs/13-m3-booking-core-verification-report.md)：M3 可用性、价格试算、预订单、库存锁和订单状态机验证结果。
- [docs/14-m4-payment-core-verification-report.md](docs/14-m4-payment-core-verification-report.md)：M4 支付单、支付事件、退款单和 mock 微信支付核心验证结果。
- [docs/15-m4-funds-marketing-verification-report.md](docs/15-m4-funds-marketing-verification-report.md)：M4 余额、优惠券、团购码、支付抵扣、退款返还和生产化加固验证结果。
- [docs/16-m5-device-control-verification-report.md](docs/16-m5-device-control-verification-report.md)：M5 设备、设备命令、mock adapter 和订单授权开门开电验证结果。
- [docs/17-m5-m6-bridge-verification-report.md](docs/17-m5-m6-bridge-verification-report.md)：M5/M6 设备重试去重、商家直控设备和保洁任务首版验证结果。
- [docs/18-m6-cleaning-completion-verification-report.md](docs/18-m6-cleaning-completion-verification-report.md)：M6 房态清洁联动、脏房预约策略、保洁返工、投诉、结算和摘要验证结果。
- [docs/19-m7-merchant-operations-verification-report.md](docs/19-m7-merchant-operations-verification-report.md)：M7 商家工作台统计、房间使用率、保洁统计、异常列表和审计查询验证结果。
- [docs/20-m7-financial-operations-verification-report.md](docs/20-m7-financial-operations-verification-report.md)：M7 提现、人工调账、后台发券、会员消费画像和提现异常验证结果。
- [docs/21-m7-closeout-and-m8-web-start-report.md](docs/21-m7-closeout-and-m8-web-start-report.md)：M7 后台订单改时、统一人工补偿和 M8 Web 首版工作台启动验证结果。
- [docs/22-m8-web-engineering-verification-report.md](docs/22-m8-web-engineering-verification-report.md)：M8 Vue/Vite/TypeScript 正式前端工程、路由、登录态、API client 和商家运营页面验证结果。
- [docs/23-environment-readiness-check.md](docs/23-environment-readiness-check.md)：`anti-spoofing_scc_175` 环境依赖、aiosqlite、前后端构建和本地联调体检。
- [docs/24-codex-project-session-isolation.md](docs/24-codex-project-session-isolation.md)：Codex 按项目隔离会话、同项目共享上下文、跨项目显式指定的启动方案。
- [_bmad-output/planning-artifacts/python-development-plan.md](_bmad-output/planning-artifacts/python-development-plan.md)：BMAD 风格的开发计划交接件。

## 当前状态

- 参考项目已经完成 BMAD 文档化。
- M0 已完成：当前目录包含 FastAPI 后端骨架、首批迁移、smoke 校验脚本和 Flutter App 储备空壳工程。
- M1 已启动并完成身份底座首版：支持 mock 微信登录、开发期 bootstrap、租户/应用绑定、角色、用户门店作用域、签名 token 和审计写入工具。
- M2 已完成后端基础首版：支持门店、房间、价格规则和不可预约时段配置 API，并延续租户隔离和审计。
- M3 已完成预约核心完整首版：支持可用性检查、价格试算、预订单/正式下单契约、待支付锁、续费、换房、过期释放、mock 支付确认、取消、开始和完成状态流转。
- M4 已完成资金营销主闭环和生产化加固首版：支持支付单、支付事件、退款单、mock 微信预支付/回调、回调 HMAC 签名、退款创建幂等、支付关闭、退款回调、余额账户/流水、优惠券、团购码，以及团购码 -> 优惠券 -> 余额 -> mock 微信支付的抵扣与退款返还。
- M5 已完成设备控制首版：支持设备配置、设备命令、mock adapter、订单授权开店门/房门/门锁/电源、命令幂等和审计记录。
- M5/M6 衔接已完成：支持商家设备测试/开/关、设备命令失败重试和短时间去重；M6 保洁任务首版已启动，订单完成自动生成保洁任务，保洁可接单、开始、开门、完成、审核和结算。
- M6 完整化已完成：支持房间清洁状态、订单完成/已使用取消后标脏、人工触发保洁、清洁审核标净、脏房预约阻断/门店配置放行、保洁取消接单、任务取消、返工重新派单、投诉、结算金额、开门时间窗口和保洁摘要。
- M7 商家运营统计首版已完成：支持商家工作台统计、房间使用率、保洁统计、平台/商家异常列表和审计查询。
- M7 财务运营首版已完成：支持提现申请/审核/驳回/打款确认、后台人工调账、后台发券、会员消费画像和提现异常识别。
- M7 收尾已完成并启动 M8：支持后台订单改时、统一人工补偿入口，并新增 `web/` 商家运营工作台首版。
- M8 正式工程化首版已完成：`web/` 升级为 Vue 3 + Vite + TypeScript，具备商家后台路由、Pinia 登录态、权限守卫、类型化 API client、运营总览、订单改时、会员补偿、提现审核、异常审计和连接设置页面。
- 当前开发命令默认使用 conda 环境 `anti-spoofing_scc_175`，不自动创建或修改 Python 环境。
- 后续建议继续 M8 Web，完善顾客 H5、保洁移动网页、平台后台、前端自动化测试和试运营联调。

## M0 本地命令

Codex 会话建议通过项目隔离入口启动，避免不同项目会话混用：

```bash
./scripts/codex_project_session.sh
./scripts/codex_project_session.sh resume <session-id>
```

```bash
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
conda run -n anti-spoofing_scc_175 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

在没有可访问 PostgreSQL 服务时，可用本地 SQLite 先验证 Alembic 迁移脚本：

```bash
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic upgrade head
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
```

如果要直接用 SQLite 跑 FastAPI 开发服务，运行时需要异步驱动 `aiosqlite`，URL 使用 `sqlite+aiosqlite`：

```bash
QIPAISHI_DATABASE_URL=sqlite+aiosqlite:///./dev.db \
QIPAISHI_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://192.168.17.175:5173,http://10.99.10.175:5173 \
conda run -n anti-spoofing_scc_175 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

局域网分享测试时，前端和 API 都需要绑定 `0.0.0.0`，并把访问者实际打开的 Web Origin 加入 `QIPAISHI_CORS_ORIGINS`。前端默认会根据页面 hostname 自动把 API 地址推导为 `http://<host>:8000`，也可以在页面右上角手动修改 API 地址。

开发环境创建首个租户和管理员 token：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/dev-bootstrap \
  -H 'content-type: application/json' \
  -d '{"tenant_name":"示例棋牌室","client_type":"h5","app_id":"dev-h5"}'
```

## 总体技术取向

- 后端优先：FastAPI + PostgreSQL + Redis + SQLAlchemy + Alembic。
- Web 优先：顾客 H5、保洁移动网页、商家 Web 后台和平台 Web 后台使用统一 OpenAPI 契约，参考小程序仅作为业务对齐和兼容迁移来源。
- 强业务边界：订单库存锁、支付回调、设备控制、退款提现全部放在服务端裁决。
- 可运营：从第一阶段开始记录审计日志、幂等键、设备命令和异常事件。
