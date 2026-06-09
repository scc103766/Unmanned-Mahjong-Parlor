# Python 架构方案

## 推荐技术栈

| 层次 | 建议 |
| --- | --- |
| Web 框架 | FastAPI |
| Web 前端 | Vue 3 + Vite + TypeScript，后台可用 Element Plus，移动网页可用 Vant/NutUI |
| 后续 App | Flutter 作为后续移植储备，非近期主线 |
| 数据校验 | Pydantic v2 |
| ORM | SQLAlchemy 2.x |
| 数据库迁移 | Alembic |
| 主数据库 | PostgreSQL |
| 缓存与锁 | Redis |
| 异步任务 | Celery 或 Arq，MVP 可先用 Celery |
| 测试 | pytest、httpx、factory-boy |
| 代码质量 | ruff、mypy、pre-commit |
| API 文档 | OpenAPI 自动生成，补充契约说明 |
| 对象存储 | S3 兼容接口，开发期可用 MinIO |
| 部署 | Docker Compose 起步，后续可迁移 Kubernetes |

## 运行拓扑

```text
Customer H5 / Cleaner H5 / Merchant Web / Platform Web / optional Mini Program compatibility
  -> API Service (FastAPI)
  -> PostgreSQL
  -> Redis
  -> Worker Service
  -> External Providers
       WeChat Pay
       Lock Gateway
       Power Controller
       Cloud Speaker
       Object Storage
       Map Service
```

## 目录建议

```text
python_24_qipaishi/
  web/
    src/
      app/
      core/
      layouts/
      modules/
      shared/
    tests/
  clients/
    qipaishi_app/  # reserved for later App migration
  app/
    main.py
    api/
      v1/
        routers/
        schemas/
        dependencies.py
      compat/
        member_routes.py
    core/
      config.py
      security.py
      logging.py
      errors.py
      idempotency.py
    db/
      base.py
      session.py
      migrations/
    modules/
      tenancy/
      auth/
      users/
      stores/
      rooms/
      availability/
      pricing/
      orders/
      payments/
      wallet/
      coupons/
      devices/
      cleaning/
      notifications/
      analytics/
      audit/
    providers/
      wechat/
      device_gateway/
      storage/
      map/
    workers/
      celery_app.py
      tasks/
  tests/
    unit/
    api/
    integration/
  docs/
```

## 客户端策略

- 顾客 H5 面向预约、支付、订单详情、开门、续费和取消等移动现场流程。
- 保洁移动网页面向任务、接单、开门、凭证和结算记录。
- 商家 Web 后台面向门店、房间、价格、设备、订单、保洁、财务和统计。
- 平台 Web 后台面向租户、权限、设备供应商、异常、审计和人工补偿。
- 参考小程序只作为业务流程来源和可选兼容对象。
- Flutter App 目录保留为后续移植储备，近期主线不以 App 打包为验收标准。
- 所有客户端都通过 `/api/v1/**` 访问后端，不直接连接数据库、支付网关或硬件供应商。

## 模块边界

| 模块 | 职责 |
| --- | --- |
| tenancy | 租户、应用绑定、门店作用域、数据隔离 |
| auth | 微信登录、JWT、RBAC、权限依赖 |
| stores | 门店资料、公告、客服、Wi-Fi、坐标、营业参数 |
| rooms | 房间资料、分类、图片、标签、设备绑定 |
| availability | 可预约时间、禁用时段、订单占用、清洁占用 |
| pricing | 普通价、工作日价、通宵价、最小时长、优惠前金额 |
| orders | 预订单、正式订单、续费、取消、换房、状态机 |
| payments | 微信支付、支付回调、查单、退款、支付流水 |
| wallet | 余额、赠送余额、充值规则、余额流水 |
| coupons | 优惠券定义、领取、锁定、使用、退回 |
| devices | 设备、供应商适配器、命令表、开门开电权限 |
| cleaning | 清洁任务、接单、凭证、审核、结算 |
| analytics | 订单、收入、退款、房间使用率、会员统计 |
| audit | 高风险操作、后台操作、设备命令、资金操作审计 |

## 数据访问策略

- 所有业务表包含 `tenant_id`，平台级表除外。
- 常用查询字段建立索引：`tenant_id`、`store_id`、`room_id`、`status`、`start_at`、`end_at`。
- 房间库存锁使用事务和排他约束，避免并发超卖。
- 支付回调、设备命令、退款和提现使用幂等键。
- 统计优先基于事实表查询，流量上来后再增加日聚合表。

## 安全策略

- 登录态中保存用户、租户、角色和门店作用域。
- 前端 `tenant-id` 只能作为路由提示，不能作为最终可信凭据。
- 开门、退款、提现、结算、后台改价必须写审计日志。
- 订单分享 `order_key` 必须有过期时间、能力范围和限频。
- 设备命令需要防重放，同一订单短时间重复命令要合并或限流。
- 手机号、支付标识、定位信息按最小必要展示。

## 事务与异步

| 场景 | 策略 |
| --- | --- |
| 下单锁房 | 数据库事务内检查时段重叠并创建锁定记录 |
| 支付回调 | 幂等记录回调事件，事务内更新支付单和订单 |
| 退款 | 退款单状态机，回调确认后更新订单和资金流水 |
| 开门开电 | 同步返回命令受理结果，异步补写供应商状态 |
| 订单结束 | 发布领域事件，生成清洁任务和房态变化 |
| 统计 | 异步刷新聚合，实时接口可查事实表 |

## 观测与运维

- 日志采用结构化 JSON，包含 `request_id`、`tenant_id`、`user_id`、`order_id`。
- 关键指标：API P95、支付回调成功率、设备命令成功率、订单超时率、库存冲突数。
- 告警场景：支付成功但订单未确认、设备连续失败、退款异常、提现异常、任务积压。
- Web 运营后台需要异常列表和人工补偿入口。

## MVP 部署

开发和试运营阶段可使用：

```text
docker compose
  api
  worker
  postgres
  redis
  minio
```

生产阶段至少拆分：

- API 多实例。
- Worker 独立扩容。
- PostgreSQL 托管或主从高可用。
- Redis 持久化和备份策略。
- 对象存储使用云服务或独立 MinIO 集群。
