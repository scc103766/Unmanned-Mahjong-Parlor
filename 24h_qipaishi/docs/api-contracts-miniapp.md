# 小程序 API 契约盘点

> 本文来自现有小程序源码静态扫描，实际字段和错误码需要以后端为准。

## 请求约定

- Base URL：`https://wq.scyanzu.com/app-api`
- Header：
  - `tenant-id: <tenantId>`
  - `Authorization: Bearer <accessToken>`
  - `Content-Type: application/json`
- 返回约定：页面普遍判断 `info.code == 0` 为成功，`code == 401` 或 HTTP 401 跳转登录。

## 用户与登录

| 能力 | API |
| --- | --- |
| 微信手机号一键登录 | `POST /member/auth/weixin-mini-app-login` |
| 退出登录 | `/member/auth/logout` |
| 获取用户信息 | `GET /member/user/get` |
| 修改昵称 | `/member/user/updateNickname?nickname=` |
| 修改手机号 | `/member/user/update-mobile` |
| 修改头像 | `/member/user/updateAvatar?avatarUrl=` |

## 门店与房间展示

| 能力 | API |
| --- | --- |
| 城市列表 | `/member/index/getCityList` |
| 门店列表 | `/member/index/getStoreList`, `/member/index/getStoreList?cityName=` |
| 门店详情 | `/member/index/getStoreInfo/{storeId}` |
| 房间列表 | `/member/index/getRoomInfoList/{storeId}` |
| 房间详情 | `/member/index/getRoomInfo/{roomId}` |
| Banner | `/member/index/getBannerList` |

## 订单与支付

| 能力 | API |
| --- | --- |
| 预下单/续费预支付 | `POST /member/order/preOrder` |
| 锁定微信订单 | `POST /member/order/lockWxOrder` |
| 保存订单 | `POST /member/order/save` |
| 订单详情 | `GET /member/order/getOrderInfo` |
| 订单列表 | `POST /member/order/getOrderPage` |
| 取消订单 | `POST /member/order/cancelOrder/{orderId}` |
| 开始订单 | `POST /member/order/startOrder/{orderId}` |
| 续费 | `POST /member/order/renew` |
| 换房 | `POST /member/order/changeRoom/{orderId}/{roomId}` |
| 房间图片 | `GET /member/order/getRoomImgs/{roomId}` |
| 订单授权开大门 | `POST /member/order/openStoreDoor?orderKey=` |
| 订单授权开房间门 | `POST /member/order/openRoomDoor?orderKey=` |
| 订单授权开智能锁 | `POST /member/order/openRoomLock` |

## 余额、优惠、团购

| 能力 | API |
| --- | --- |
| 门店余额 | `/member/user/getStoreBalance/{storeId}` |
| 赠送余额流水 | `/member/user/getGiftBalanceList` |
| 资金流水 | `/member/user/getMoneyBillPage` |
| 优惠券列表 | `/member/user/getCouponPage` |
| 充值预支付 | `/member/user/preRechargeBalance` |
| 充值确认 | `/member/user/rechargeBalance` |
| 充值规则 | `/member/order/getDiscountRules/{storeId}` |
| 团购码核销 | `/member/manager/useGroupNo` |

## 商家管理

| 能力 | API |
| --- | --- |
| 管理端门店列表 | `/member/store/getStoreList` |
| 门店分页 | `/member/store/getPageList` |
| 门店详情 | `/member/store/getDetail/{storeId}` |
| 保存门店 | `/member/store/save` |
| 上传图片 | `/member/store/uploadImg` |
| 房间列表 | `/member/store/getRoomInfoList/{storeId}` |
| 房间详情 | `/member/store/getRoomDetail/{roomId}` |
| 保存房间 | `/member/store/saveRoomDetail` |
| 开/关房间门 | `/member/store/openRoomDoor/{roomId}`, `/member/store/closeRoomDoor/{roomId}` |
| 开智能锁 | `/member/store/openRoomLock/{roomId}` |
| 开门店大门 | `/member/store/openStoreDoor/{storeId}` |
| 停用房间 | `/member/store/disableRoom/{roomId}` |
| 结束房间订单 | `/member/store/finishRoomOrder/{roomId}` |
| 清洁并结束 | `/member/store/clearAndFinish/{roomId}` |
| 测试云喇叭 | `/member/store/testYunlaba/{roomId}` |

## 保洁

| 能力 | API |
| --- | --- |
| 保洁任务列表 | `/member/clear/getClearPage` |
| 保洁管理任务列表 | `/member/manager/getClearManagerPage` |
| 任务详情 | `/member/clear/getDetail/{id}` |
| 接单 | `/member/clear/jiedan/{id}` |
| 取消接单 | `/member/clear/cancel/{id}` |
| 开始任务 | `/member/clear/start/{id}` |
| 完成任务 | `/member/clear/finish/{id}` |
| 保洁开大门 | `/member/clear/openStoreDoor/{id}` |
| 保洁开房间门 | `/member/clear/openRoomDoor/{id}` |
| 投诉保洁 | `/member/manager/complaintClearInfo` |
| 结算保洁 | `/member/manager/settlementClearUser` |
| 保洁统计 | `/member/clear/getChartData`, `/member/clear/getClearBillPage` |

## 运营统计

| 能力 | API |
| --- | --- |
| 营收概览 | `/member/chart/getRevenueChart` |
| 业务统计 | `/member/chart/getBusinessStatistics` |
| 收益统计 | `/member/chart/getIncomeStatistics` |
| 订单统计 | `/member/chart/getOrderStatistics` |
| 会员统计 | `/member/chart/getMemberStatistics` |
| 充值统计 | `/member/chart/getRechargeStatistics` |
| 房间使用率 | `/member/chart/getRoomUseStatistics` |
| 房间使用时长 | `/member/chart/getRoomUseHourStatistics` |
| 收入/提现申请 | `/member/manager/applyWithdrawal`, `/member/manager/getWithdrawalPage` |

