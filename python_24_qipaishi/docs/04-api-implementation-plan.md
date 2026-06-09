# API 实施计划

## API 策略

Python 版建议采用 Web-first 的内部清晰路由，并保留可选外部兼容层：

- `/api/v1/**`：新的领域化 API，供顾客 H5、保洁移动网页、商家 Web 后台、平台 Web 后台和后续 App 使用。
- `/compat/member/**`：参考项目小程序接口兼容层，仅用于迁移、联调或临时复用旧页面。
- 内部服务只依赖领域模块，不在业务层传播旧接口命名。

## API 分组

| 分组 | 路由前缀 | 说明 |
| --- | --- | --- |
| 健康检查 | `/health` | 服务、数据库、Redis 健康状态 |
| 认证 | `/api/v1/auth` | 微信登录、手机号绑定、token 刷新 |
| 租户 | `/api/v1/tenants` | 平台租户、应用绑定、租户配置 |
| 用户权限 | `/api/v1/users` `/api/v1/roles` | 用户、角色、门店作用域 |
| 门店 | `/api/v1/stores` | 门店资料、图片、公告、Wi-Fi、客服 |
| 房间 | `/api/v1/rooms` | 房间、标签、价格、禁用时段、设备绑定 |
| 可用性 | `/api/v1/availability` | 可预约时间轴、时段锁定检查 |
| 订单 | `/api/v1/orders` | 预订单、下单、详情、取消、续费、换房 |
| 支付 | `/api/v1/payments` | 微信支付、回调、查单、退款 |
| 余额 | `/api/v1/wallets` | 充值、余额、赠送余额、流水 |
| 优惠 | `/api/v1/coupons` `/api/v1/group-buy` | 优惠券、团购码 |
| 设备 | `/api/v1/devices` | 设备、命令、开门开电 |
| 保洁 | `/api/v1/cleaning` | 任务、接单、开门、凭证、审核、结算 |
| 统计 | `/api/v1/analytics` | 收入、订单、房间使用率、会员、保洁 |
| 审计 | `/api/v1/audit-logs` | 高风险操作记录 |

## 首批接口

### M0

- `GET /health`
- `GET /api/v1/meta/version`
- `GET /api/v1/meta/openapi-tags`

### M1

- `POST /api/v1/auth/wechat-login`
- `GET /api/v1/me`
- `GET /api/v1/stores`
- `POST /api/v1/stores`
- `GET /api/v1/stores/{store_id}`
- `PATCH /api/v1/stores/{store_id}`
- `GET /api/v1/rooms`
- `POST /api/v1/rooms`
- `PATCH /api/v1/rooms/{room_id}`
- `POST /api/v1/rooms/{room_id}/blocked-slots`

### M2

- `GET /api/v1/availability/rooms`
- `POST /api/v1/pricing/quote`
- `POST /api/v1/orders/preorder`
- `POST /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `POST /api/v1/orders/{order_id}/cancel`
- `POST /api/v1/orders/{order_id}/renew/quote`
- `POST /api/v1/orders/{order_id}/renew`
- `POST /api/v1/orders/{order_id}/change-room/quote`
- `POST /api/v1/orders/{order_id}/change-room`

### M3

- `POST /api/v1/payments/wechat/prepay`
- `POST /api/v1/payments/wechat/callback`
- `POST /api/v1/payments/{payment_id}/refund`
- `GET /api/v1/wallets/me`
- `POST /api/v1/wallets/recharge`
- `GET /api/v1/coupons/me`
- `POST /api/v1/group-buy/verify`

### M4

- `POST /api/v1/orders/{order_id}/open-store-door`
- `POST /api/v1/orders/{order_id}/open-room-door`
- `POST /api/v1/orders/{order_id}/open-room-lock`
- `POST /api/v1/orders/{order_id}/power-on`
- `GET /api/v1/devices`
- `POST /api/v1/devices`
- `GET /api/v1/device-commands`

### M5

- `GET /api/v1/cleaning/tasks`
- `POST /api/v1/cleaning/tasks/{task_id}/accept`
- `POST /api/v1/cleaning/tasks/{task_id}/start`
- `POST /api/v1/cleaning/tasks/{task_id}/open-door`
- `POST /api/v1/cleaning/tasks/{task_id}/complete`
- `POST /api/v1/cleaning/tasks/{task_id}/review`
- `POST /api/v1/cleaning/tasks/{task_id}/settle`

## 参考项目兼容映射

| 参考接口语义 | Python 新接口 |
| --- | --- |
| `/member/store/**` 门店详情、图片、开门 | `/api/v1/stores/**`、`/api/v1/devices/commands` |
| `/member/room/**` 房间列表、价格、禁用时段 | `/api/v1/rooms/**`、`/api/v1/availability/**` |
| `/member/order/preOrder` | `/api/v1/orders/preorder` |
| `/member/order/save` | `/api/v1/orders` |
| `/member/order/lockWxOrder` | `/api/v1/payments/wechat/prepay` |
| `/member/order/openStoreDoor` | `/api/v1/orders/{order_id}/open-store-door` |
| `/member/order/openRoomDoor` | `/api/v1/orders/{order_id}/open-room-door` |
| `/member/order/renew` | `/api/v1/orders/{order_id}/renew` |
| `/member/order/changeRoom` | `/api/v1/orders/{order_id}/change-room` |
| `/member/clear/**` 保洁任务 | `/api/v1/cleaning/**` |
| `/member/statistics/**` 统计 | `/api/v1/analytics/**` |

## 响应格式

统一响应建议：

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "request_id": "req_xxx"
}
```

错误响应建议：

```json
{
  "code": "ORDER_TIME_CONFLICT",
  "message": "该时间段已被预约",
  "details": {
    "room_id": "room_xxx",
    "start_at": "2026-05-12T10:00:00+08:00",
    "end_at": "2026-05-12T12:00:00+08:00"
  },
  "request_id": "req_xxx"
}
```

## 幂等约定

- 创建订单、支付预下单、支付回调、退款、设备命令、余额充值使用 `Idempotency-Key`。
- 微信回调以供应商交易号和事件 ID 去重。
- 设备命令以 `actor + device + biz + command + short_window` 去重或限流。
- 接口返回幂等命中结果时，需要带上原始业务对象状态。

## 鉴权约定

- 顾客接口要求 customer token。
- 商家接口要求 tenant role 和 store scope。
- 保洁接口要求 cleaner role 和任务授权。
- 平台接口要求 platform role。
- 兼容层也必须走同一套鉴权依赖，不能绕过领域权限。
- 网页端、后续 App 和兼容层只影响交互形态，不影响后端权限边界。
