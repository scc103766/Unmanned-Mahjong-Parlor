# 领域模型计划

## 核心实体

| 实体 | 说明 | 关键字段 |
| --- | --- | --- |
| Tenant | 租户/商户主体 | id、name、status、plan、settings |
| TenantApp | 网页端、小程序、App 或第三方应用绑定 | tenant_id、app_id、client_type、mch_id、secret_ref |
| User | 系统用户 | phone、openid、unionid、nickname、status |
| Role | 角色 | platform_admin、merchant_admin、clerk、cleaner、customer、support |
| Store | 门店 | tenant_id、name、address、lng、lat、notice、wifi、cleaning_settings |
| Room | 房间 | store_id、name、type、capacity、tags、status、sort |
| RoomPriceRule | 价格规则 | room_id、base_price、weekday_price、night_price、min_hours |
| RoomBlockedSlot | 不可预约时段 | room_id、start_at、end_at、reason |
| RoomTimeLock | 时段锁定 | room_id、order_id、start_at、end_at、status |
| Order | 订单 | order_no、user_id、room_id、start_at、end_at、amount、status |
| OrderItem | 订单明细 | order_id、item_type、quantity、unit_price、amount |
| Payment | 支付单 | order_id、channel、amount、status、transaction_id |
| Refund | 退款单 | payment_id、amount、reason、status |
| WalletAccount | 余额账户 | user_id、cash_balance、gift_balance |
| WalletLedger | 余额流水 | account_id、direction、amount、biz_type、biz_id |
| CouponTemplate | 优惠券模板 | tenant_id、name、type、value、threshold |
| Coupon | 用户优惠券 | user_id、template_id、status、locked_order_id |
| GroupBuyCode | 团购码 | code、store_id、status、verified_order_id |
| Device | 设备 | store_id、room_id、type、provider、external_id、status |
| DeviceCommand | 设备命令 | device_id、actor_id、biz_type、biz_id、command、status |
| CleaningTask | 保洁任务 | store_id、room_id、order_id、cleaner_id、status |
| CleaningProof | 清洁凭证 | task_id、image_url、remark |
| Withdrawal | 提现申请 | tenant_id、amount、status、audit_user_id |
| AuditLog | 审计日志 | actor_id、action、target_type、target_id、metadata |

## 订单状态机

```text
created
  -> pending_payment
  -> paid
  -> in_use
  -> completed

pending_payment -> cancelled
paid -> cancelled_refunding -> refunded
paid -> in_use
in_use -> completed
in_use -> renewal_pending -> in_use
paid/in_use -> room_change_pending -> paid/in_use
completed -> cleaning_pending
```

## 支付状态机

```text
created
  -> paying
  -> paid
  -> refunding
  -> partially_refunded
  -> refunded

created/paying -> closed
```

关键规则：

- 支付成功回调可以重复进入，但只能产生一次订单确认。
- 退款可以多次部分退款，但总额不能超过可退金额。
- 前端支付成功回跳只作为提示，最终以服务端支付单为准。

## 房间库存规则

- 房间可预约时间由门店营业参数、房间禁用时段、订单占用、清洁占用共同计算。
- 同一房间有效订单时段不能重叠。
- 待支付订单锁定时段需要过期释放。
- 续费时只检查当前订单结束后的延长时段。
- 换房时需要同时释放旧房锁定并创建新房锁定，必须在同一事务内完成。
- 门店可配置是否允许未清洁房间继续被预约。

## 价格规则

- 基础价格：按小时计算。
- 工作日价格：按星期或日期覆盖基础价格。
- 通宵价格：按门店通宵开始时间和固定时长计算。
- 最小时长：下单时长不得低于房间配置。
- 优惠顺序建议：团购码/套餐抵扣、优惠券、余额、微信支付。
- 服务端返回价格明细，便于前端展示和客服解释。

## 设备权限规则

| 场景 | 校验 |
| --- | --- |
| 顾客开店门 | 存在已支付或进行中订单，当前时间在允许开门窗口内 |
| 顾客开房门 | 订单房间匹配，订单未取消未退款，当前时间有效 |
| 顾客开电 | 同房门规则，可按房间设备配置限制 |
| 商家开门 | 拥有门店管理权限，操作写审计 |
| 保洁开门 | 存在已接或进行中清洁任务，任务房间匹配 |
| 客服补救 | 需要客服权限、原因备注和审计 |

## 保洁任务规则

- 订单完成、提前结束、取消且已使用、人工补单可以触发保洁任务。
- 一个订单默认只生成一个有效保洁任务。
- 保洁任务状态：待接单、已接单、进行中、待审核、已完成、已驳回、已取消、已结算。
- 保洁员开门能力只在任务授权时间内有效。
- 完成任务需要凭证，是否必须上传图片由租户或门店配置。

## 审计范围

必须写审计的动作：

- 后台创建或修改门店、房间、价格和设备。
- 订单取消、改时、换房、续费、人工完成。
- 支付退款、余额调整、优惠券人工发放、团购码核销。
- 开门、开锁、开电、关电。
- 保洁审核、结算、投诉。
- 提现申请、审核和打款确认。
