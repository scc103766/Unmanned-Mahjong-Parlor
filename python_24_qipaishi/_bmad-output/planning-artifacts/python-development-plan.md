---
title: "Python Development Plan: 24H 无人棋牌室管理系统"
project: "python_24_qipaishi"
status: "draft"
created: "2026-05-12"
sourceProject: "../24h_qipaishi"
sourceArtifacts:
  - "../24h_qipaishi/docs/index.md"
  - "../24h_qipaishi/docs/architecture.md"
  - "../24h_qipaishi/docs/api-contracts-miniapp.md"
  - "../24h_qipaishi/_bmad-output/planning-artifacts/product-brief.md"
  - "../24h_qipaishi/_bmad-output/planning-artifacts/prd.md"
---

# Python Development Plan

## 目标

开发一个 Python 后端 + 网页端的 24H 无人棋牌室管理系统，功能对齐参考小程序项目，并补齐服务端工程能力：多租户、RBAC、订单库存锁、支付幂等、设备命令审计、保洁闭环、运营统计和可观测性。App 作为后续深化移植阶段。

## 建议技术路线

- FastAPI + Pydantic v2 提供 API。
- Vue/Vite/TypeScript 用于开发顾客 H5、保洁移动网页、商家 Web 后台和平台 Web 后台。
- SQLAlchemy 2 + Alembic 管理 PostgreSQL。
- Redis 用于缓存、限流、幂等和短期锁。
- Celery/Worker 处理支付补偿、设备状态回写、清洁任务和统计聚合。
- OpenAPI 作为网页端、后续 App 和可选兼容层的接口契约。

## 里程碑

1. M0 项目基础：脚手架、配置、数据库、测试、OpenAPI。
2. M1 租户权限：租户、用户、角色、门店作用域、审计。
3. M2 门店房间：门店、房间、价格、禁用时段、设备绑定草案。
4. M3 交易核心：可用性、价格试算、预订单、订单状态机。
5. M4 支付资金：微信支付、余额、优惠券、团购码、退款。
6. M5 设备控制：设备命令、适配器、开门开电、审计重试。
7. M6 保洁闭环：任务生成、接单、开门、凭证、审核结算。
8. M7 运营统计：订单处理、会员、提现、经营数据。
9. M8 网页端：顾客 H5、保洁移动网页、商家 Web 后台、平台 Web 后台 MVP。
10. M9 联调上线：Web 发布、兼容迁移、安全检查、监控告警、试运营。

## 关键交付文档

详细计划见：

- `docs/01-development-plan.md`
- `docs/02-python-architecture-plan.md`
- `docs/03-domain-model-plan.md`
- `docs/04-api-implementation-plan.md`
- `docs/05-epics-and-backlog.md`
- `docs/06-next-development-roadmap.md`
- `docs/07-web-client-plan.md`
- `docs/07-app-client-plan.md`

## 首个可执行任务

进入 M0，创建 Python 项目脚手架：

- 依赖管理文件。
- FastAPI `app/main.py`。
- 配置、日志、错误处理。
- 数据库连接和迁移。
- 健康检查接口。
- pytest 基础测试。

后续执行节奏和验收门槛以 `docs/06-next-development-roadmap.md` 为准。
网页端客户端规划以 `docs/07-web-client-plan.md` 为准；App 迁移储备以 `docs/07-app-client-plan.md` 为参考。
