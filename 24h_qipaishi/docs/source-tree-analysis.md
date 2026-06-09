# 源码结构分析

```text
24h_qipaishi/
├── app.js                         # 小程序全局配置：baseUrl、tenantId、用户 token、设备信息
├── app.json                       # 页面路由、tabBar、Vant 组件、插件和权限声明
├── app.wxss                       # 全局样式
├── package.json                   # npm 依赖，主要为 @vant/weapp
├── utils/
│   ├── http.js                    # wx.request 封装，统一请求头、401 处理、loading
│   ├── lock.js                    # 蓝牙门锁插件控制封装
│   └── util.js                    # 时间格式化、手机号校验
├── lib/
│   └── moment.js                  # 本地 Moment 时间库
├── ec-canvas/                     # ECharts 小程序适配层
├── miniprogram_npm/@vant/weapp/   # Vant Weapp 构建产物
├── style/                         # 公共样式和 iconfont
├── pages/
│   ├── index/                     # 门店首页、房间时间轴、预约入口、充值/组局/客服
│   ├── doorList/                  # 门店选择列表
│   ├── booking/                   # 预约模式入口
│   ├── orderSubmit/               # 下单、价格计算、优惠券/团购码、微信支付/余额支付
│   ├── orderDetail/               # 订单详情、开门、续费、取消、换房、分享
│   ├── orderList/                 # 顾客订单列表
│   ├── recharge/                  # 余额充值和充值赠送规则
│   ├── coupon/                    # 顾客优惠券选择
│   ├── user/                      # 个人中心
│   ├── login/                     # 微信手机号授权登录
│   ├── setStore*/                 # 门店列表和门店资料配置
│   ├── setDoor*/                  # 房间列表、房间资料、开关门和设备控制
│   ├── SetOrder/                  # 管理员订单处理
│   ├── task*/                     # 保洁任务、任务详情、结算和统计
│   ├── statics/                   # 经营统计图表
│   ├── admin/                     # 管理员账号
│   ├── cleaner/                   # 保洁员账号
│   ├── setCoupon*/                # 优惠券配置与发放
│   ├── setDiscount/               # 充值赠送规则
│   ├── setVip/                    # 会员列表/发券
│   ├── scanQr/                    # 团购券码核销
│   └── static/                    # 图标和静态图片
└── docs/                          # BMAD 项目知识文档
```

## 入口与导航

- `app.json` 注册全部页面和 3 个 tab：首页、我的订单、个人中心。
- 用户首次进入首页时，如果未持有门店 ID，会跳转至门店选择。
- 首页缓存 `global_store_id`，用于保持当前门店上下文。
- 多数页面直接依赖 `app.globalData.userDatatoken.accessToken` 调 API。

## 网络与 API 组织

- 所有常规请求走 `utils/http.js`。
- 请求头包含：
  - `tenant-id`
  - `Content-Type: application/json`
  - `Authorization: Bearer <accessToken>`
- 后端返回 `401` 或业务 `code == 401` 时跳转登录页。
- 上传图片页面直接使用 `wx.uploadFile` 调 `/member/store/uploadImg`。

## 关键页面说明

| 页面 | 作用 | 主要依赖 |
| --- | --- | --- |
| `pages/index` | 门店首页、房间时间轴、预约入口 | `/member/index/getStoreInfo`, `/member/index/getRoomInfoList` |
| `pages/orderSubmit` | 下单与支付 | `/member/index/getRoomInfo`, `/member/order/preOrder`, `/member/order/lockWxOrder`, `/member/order/save` |
| `pages/orderDetail` | 订单履约与开门 | `/member/order/getOrderInfo`, `/member/order/openRoomDoor`, `/member/order/openRoomLock`, `/member/order/renew` |
| `pages/setStoreInfo` | 门店资料配置 | `/member/store/getDetail`, `/member/store/save`, `/member/store/uploadImg` |
| `pages/setDoorInfo` | 房间资料配置 | `/member/store/getRoomDetail`, `/member/store/saveRoomDetail` |
| `pages/setDoorList` / `pages/roomList` | 房间管理与开关门 | `/member/store/openRoomDoor`, `/member/store/openRoomLock`, `/member/store/closeRoomDoor` |
| `pages/task` / `pages/taskDetail` | 保洁任务流 | `/member/clear/getClearPage`, `/member/clear/jiedan`, `/member/clear/start`, `/member/clear/finish` |
| `pages/statics` | 经营统计 | `/member/chart/**` |

## 推荐重构方向

- 将“顾客端”“商家端”“保洁端”拆成明确模块或独立应用入口。
- 将 API 路径集中成契约文件，避免页面散落字符串。
- 将订单时间、价格、优惠券、通宵场计算移出页面层，形成可测试的领域服务。
- 将门锁/电源/云喇叭抽象为设备适配层，前端只接收操作结果和状态。
- 为用户 token、tenantId、baseUrl 建立环境配置与初始化流程。

