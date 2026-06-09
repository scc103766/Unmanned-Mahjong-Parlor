# 架构说明：参考小程序端

## 当前架构

现有项目是“前端小程序 + 远程后端 API + 硬件控制服务”的前端部分。小程序负责展示、交互、微信登录、微信支付发起、图片上传和部分蓝牙门锁控制；后端负责订单、价格、支付单、权限、设备控制、保洁任务、统计和结算。

```text
微信用户
  -> 微信小程序 pages/**
  -> utils/http.js
  -> 后端 REST API /member/**
  -> 业务服务：用户、门店、房间、订单、支付、优惠、保洁、统计
  -> 硬件/第三方：微信支付、门锁网关、蓝牙锁、云喇叭、地图、文件存储
```

## 客户端层

- 页面层以 `pages/<name>/<name>.js|wxml|wxss|json` 组织。
- 页面直接持有业务状态，例如订单时长、价格、优惠券、门店 ID、房间 ID。
- UI 使用 Vant Weapp 组件，统计图使用 ECharts。
- 登录态存储在 `app.globalData` 和 `wx.setStorageSync("userDatatoken")`。

## API 层

`utils/http.js` 是唯一的常规请求封装。它做了：

- 拼接 `app.globalData.baseUrl`。
- 添加 `tenant-id`。
- 添加 Bearer token。
- 显示/隐藏 loading。
- 处理 401 跳转登录。

当前不足：

- 没有请求超时、重试、错误码统一映射。
- `urltype` 参数未实际影响请求逻辑。
- 登录函数 `getLogin` 的参数顺序与 `request` 定义存在明显错位风险，应在后续重构中验证。
- API 路径散落在页面文件中，不利于契约管理。

## 业务层现状

当前没有独立业务 service 层，业务规则主要散落在页面中：

- `orderSubmit` 负责预约时间、通宵价、工作日价、优惠券、团购码、支付方式计算。
- `orderDetail` 负责订单开始、续费、取消、换房、开门、蓝牙锁兜底。
- `setDoorInfo` 负责房间价格、标签、图片、禁用时段和云喇叭文案配置。
- `task` 负责保洁任务状态流转和开门能力。

这对快速开发友好，但会让关键交易逻辑难以测试。后续完整系统应把价格、库存、订单状态机、设备权限校验放在服务端领域层。

## 设备控制架构

现有小程序体现了三类设备控制路径：

1. 订单授权开门：订单详情页通过 `orderKey` 调用 `/member/order/openStoreDoor`、`/member/order/openRoomDoor`、`/member/order/openRoomLock`。
2. 管理/保洁开门：商家或保洁通过 `/member/store/**`、`/member/clear/**` 接口开门。
3. 蓝牙锁兜底：`utils/lock.js` 调用微信插件本地控制蓝牙锁。

完整系统需要确保：

- 每次开门都绑定操作者、角色、订单/任务、门店、房间、设备、时间和结果。
- 开门操作需要防重放、防越权、防越时段。
- 后端需要统一封装设备供应商差异，前端不直接理解硬件协议。

## 安全边界

- 前端不能作为权限判断可信来源。
- 开门、开电、退款、提现、结算必须以后端鉴权和审计为准。
- `tenant-id` 不应只依赖前端传递，服务端需从小程序 appId、域名、登录态或租户绑定关系校验。
- 订单分享的 `orderKey` 应有时效、权限范围和最小可操作能力。

## 目标架构建议

```text
顾客小程序 / 商家管理端 / 保洁端
  -> API Gateway / BFF
  -> Auth & Tenant Service
  -> Store Service
  -> Room & Inventory Service
  -> Order Service
  -> Payment Service
  -> Coupon & Balance Service
  -> Device Control Service
  -> Cleaning Task Service
  -> Notification Service
  -> Analytics Service
  -> Audit Log
  -> Database / Cache / Queue
  -> WeChat Pay / Lock Gateway / Power Controller / Cloud Speaker / Map / Object Storage
```

## 后续架构关注点

- 订单状态机和房间库存锁必须服务端强一致或准强一致。
- 微信支付回调必须幂等，不能依赖前端支付成功回调创建最终订单。
- 设备控制建议使用命令表 + 异步状态回写，避免接口成功但硬件失败无法追踪。
- 保洁任务应由订单结束/取消/超时触发，并支持人工补单。
- 统计服务应基于订单、支付、退款、充值、提现、房间使用时长等事实表生成。

