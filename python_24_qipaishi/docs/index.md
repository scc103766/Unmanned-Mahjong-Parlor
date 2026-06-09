# Python 版开发计划索引

## 目标

基于参考项目 `24h_qipaishi` 的 BMAD 梳理结果，先开发一个 Python 后端 + 网页端的 24H 无人棋牌室管理系统。系统需要覆盖顾客预约支付开门、商家门店和房间管理、保洁履约、设备控制、营销、结算和运营统计，并在可靠性、安全性、可维护性和多租户能力上优于参考项目。App 作为后续深化移植阶段。

## 规划产物

| 文档 | 用途 |
| --- | --- |
| [00-bmad-input-summary.md](00-bmad-input-summary.md) | 记录来自参考项目 BMAD 文档的输入与关键判断 |
| [01-development-plan.md](01-development-plan.md) | 项目阶段、里程碑、验收标准和风险 |
| [02-python-architecture-plan.md](02-python-architecture-plan.md) | Python 后端架构、目录、基础设施和安全策略 |
| [03-domain-model-plan.md](03-domain-model-plan.md) | 租户、门店、房间、订单、支付、设备、保洁等领域模型 |
| [04-api-implementation-plan.md](04-api-implementation-plan.md) | API 设计、兼容参考小程序的接口迁移策略 |
| [05-epics-and-backlog.md](05-epics-and-backlog.md) | 可执行 Epic、Story、首轮 Sprint 建议 |
| [06-next-development-roadmap.md](06-next-development-roadmap.md) | 后续落地路线图、Sprint 拆解、验收和上线检查 |
| [07-web-client-plan.md](07-web-client-plan.md) | 当前网页端开发计划和后续 App 迁移策略 |
| [07-app-client-plan.md](07-app-client-plan.md) | 后续 PC 与手机端 App 迁移储备计划 |
| [08-environment-download-checklist.md](08-environment-download-checklist.md) | M0 环境下载、依赖补全和验证命令清单 |
| [09-m0-verification-report.md](09-m0-verification-report.md) | M0 后端、迁移和 Flutter 储备验证结果 |
| [10-hermes-agent-usage-plan.md](10-hermes-agent-usage-plan.md) | Hermes Agent 在研发、运维、运营和后续智能助手中的使用边界 |
| [11-m1-identity-verification-report.md](11-m1-identity-verification-report.md) | M1 租户、身份、角色、门店作用域和审计底座验证结果 |
| [12-m2-store-room-verification-report.md](12-m2-store-room-verification-report.md) | M2 门店、房间、价格规则和不可预约时段验证结果 |
| [13-m3-booking-core-verification-report.md](13-m3-booking-core-verification-report.md) | M3 可用性、价格试算、预订单、库存锁和订单状态机验证结果 |
| [14-m4-payment-core-verification-report.md](14-m4-payment-core-verification-report.md) | M4 支付单、支付事件、退款单和 mock 微信支付核心验证结果 |
| [15-m4-funds-marketing-verification-report.md](15-m4-funds-marketing-verification-report.md) | M4 余额、优惠券、团购码、支付抵扣、退款返还和生产化加固验证结果 |
| [16-m5-device-control-verification-report.md](16-m5-device-control-verification-report.md) | M5 设备、设备命令、mock adapter 和订单授权开门开电验证结果 |
| [17-m5-m6-bridge-verification-report.md](17-m5-m6-bridge-verification-report.md) | M5/M6 设备重试去重、商家直控设备和保洁任务首版验证结果 |
| [18-m6-cleaning-completion-verification-report.md](18-m6-cleaning-completion-verification-report.md) | M6 房态清洁联动、人工触发、脏房预约策略、保洁取消/返工、投诉、结算和摘要验证结果 |
| [19-m7-merchant-operations-verification-report.md](19-m7-merchant-operations-verification-report.md) | M7 商家工作台统计、房间使用率、保洁统计、异常列表和审计查询验证结果 |
| [20-m7-financial-operations-verification-report.md](20-m7-financial-operations-verification-report.md) | M7 提现、人工调账、后台发券、会员消费画像和提现异常验证结果 |
| [21-m7-closeout-and-m8-web-start-report.md](21-m7-closeout-and-m8-web-start-report.md) | M7 后台订单改时、统一人工补偿和 M8 Web 首版工作台启动验证结果 |
| [22-m8-web-engineering-verification-report.md](22-m8-web-engineering-verification-report.md) | M8 Vue/Vite/TypeScript 正式前端工程、路由、登录态、API client 和商家运营页面验证结果 |
| [23-environment-readiness-check.md](23-environment-readiness-check.md) | `anti-spoofing_scc_175` 环境依赖、aiosqlite、前后端构建和本地联调体检 |
| [24-codex-project-session-isolation.md](24-codex-project-session-isolation.md) | Codex 按项目隔离会话、同项目共享上下文、跨项目显式指定的启动方案 |

## 推荐执行顺序

1. 确认技术栈和部署环境。
2. 按 [06-next-development-roadmap.md](06-next-development-roadmap.md) 进入 M0，创建 FastAPI 项目脚手架、数据库迁移和基础测试框架。
3. 先实现租户、用户、门店、房间和价格模型。
4. 实现订单库存锁和支付幂等闭环。
5. 接入设备命令表和至少一种门禁/门锁适配器。
6. 完成保洁任务和房态清洁联动。
7. M7 已完成收尾，后台订单改时和统一人工补偿入口已完成。
8. M8 已进入正式工程化，商家 Web 后台首版已升级到 Vue/Vite/TypeScript；继续完善顾客 H5、保洁移动网页和平台 Web 后台。

## 关键原则

- 前端只负责交互，不作为权限、库存、订单或设备控制的最终可信来源。
- 所有会造成资金、门锁、房间占用变化的操作必须幂等并写审计。
- 多租户隔离以服务端登录态、应用绑定、门店授权和数据作用域为准，不能只相信前端 `tenant-id`。
- 订单、支付、设备、保洁必须形成闭环：下单锁库存，支付定订单，开门有审计，结束触发清洁。
