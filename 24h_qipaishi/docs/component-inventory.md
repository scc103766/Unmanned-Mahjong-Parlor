# 页面与组件清单

## 页面分组

### 顾客端

- `index`：门店首页、房间时间轴、预约入口、充值、团购、客服、地图。
- `doorList` / `location`：门店与城市选择。
- `booking` / `roomList`：预约和房间选择。
- `orderSubmit`：预约下单、价格计算、优惠券、团购码、微信支付/余额支付。
- `orderDetail`：订单详情、确认到店、续费、取消、换房、分享、开门。
- `orderList`：我的订单。
- `coupon`：优惠券选择。
- `recharge` / `myBalance` / `getBalance`：充值、余额和流水。
- `user` / `login` / `setUserInfo` / `setUserName` / `setUserPhone`：用户资料和登录。
- `help` / `doorDetail` / `tencentMap` / `tuangou` / `join`：帮助、门店详情、地图、团购、加盟。

### 商家/管理员

- `setStore` / `setStoreInfo`：门店列表和门店配置。
- `setDoorList` / `setDoorInfo`：房间列表和房间配置。
- `SetOrder`：订单管理，支持取消、退款、改时、续费等。
- `admin`：管理员账号管理。
- `setVip`：会员管理与赠券。
- `setCoupon` / `setCouponInfo`：优惠券配置和发放。
- `setDiscount`：充值赠送规则。
- `scanQr`：团购券码核销。
- `statics`：经营统计图表。
- `cashOut`：提现记录。

### 保洁端

- `cleaner`：保洁人员管理。
- `task`：保洁员任务列表。
- `taskManager`：管理端任务列表。
- `taskDetail`：任务详情、开门、上传图片、完成任务。
- `taskSettle`：保洁结算。
- `taskStatics`：保洁统计。

## 共享组件与能力

- Vant Weapp：按钮、弹窗、表单、日历、时间选择、上传、标签、下拉菜单、单元格、Tabs、Popup。
- ECharts：统计页折线图、饼图、柱状图。
- 微信能力：手机号授权、微信支付、定位、地图、扫码、图片预览、文件上传。
- 蓝牙门锁插件：`utils/lock.js` 调用 `myPlugin.controlLock`。

## 可复用模块建议

当前页面内逻辑重复明显，后续建议抽取：

- `services/authService`：登录、token、用户资料。
- `services/storeService`：门店、城市、地图、门店配置。
- `services/roomService`：房间列表、房间详情、价格参数、设备状态。
- `services/orderService`：预下单、保存、续费、取消、换房、订单详情。
- `services/paymentService`：微信支付、余额支付、团购码、充值。
- `services/deviceService`：开门、开锁、开电、云喇叭。
- `services/cleaningService`：保洁任务、结算、投诉。
- `domain/pricing`：工作日价、通宵价、最小时长、优惠券抵扣。

