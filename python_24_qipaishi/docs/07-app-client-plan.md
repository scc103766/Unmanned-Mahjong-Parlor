# PC 与手机端 App 计划

> 状态：后续迁移储备。
>
> 当前项目主线已调整为 Web-first：先完成顾客 H5、保洁移动网页、商家 Web 后台和平台 Web 后台。本文仅作为业务稳定后迁移到可下载 App 的参考计划，不作为近期 M8/M9 验收依据。

## 目标调整

后续迁移阶段可开发一套可下载、可安装的无人棋牌室系统 App，包含：

- 手机端 App：面向顾客、保洁员、商家移动管理，覆盖预约、支付、开门、保洁、移动运营处理。
- PC 端 App：面向商家、店长、平台运营和客服，覆盖门店配置、房间配置、订单处理、设备管理、保洁审核、提现和统计。
- Python 后端：作为统一业务中台，负责租户、权限、订单、支付、设备、保洁、资金、统计和审计。

参考小程序和网页端继续作为业务流程和接口语义来源。`/compat/member/**` 兼容层只用于迁移和联调，不作为长期主接口。

## 客户端技术路线

推荐采用 Flutter 作为 PC 与手机端的统一客户端技术栈：

- Flutter 官方支持 Android、iOS、Windows、macOS、Linux 等部署平台。
- Flutter 桌面支持可编译为原生 Windows、macOS、Linux 桌面应用。
- Flutter 官方部署文档覆盖 Android、iOS、Windows、macOS、Linux 的发布流程。

技术依据：

- [Flutter supported deployment platforms](https://docs.flutter.dev/reference/supported-platforms)
- [Flutter desktop support](https://docs.flutter.dev/platform-integration/desktop)
- [Flutter deployment](https://docs.flutter.dev/deployment)

## 推荐产品形态

| 客户端 | 主要用户 | 发布形态 | 核心能力 |
| --- | --- | --- | --- |
| 手机端 App | 顾客 | Android APK/应用商店、iOS App Store/TestFlight | 选店、选房、预约、支付、开门、续费、取消、余额、优惠券、客服 |
| 手机端 App | 保洁员 | 同上 | 任务列表、接单、开始、开门、拍照凭证、完成、结算记录 |
| 手机端 App | 商家/店员 | 同上 | 移动看店、订单处理、异常开门、房态查看、保洁审核 |
| PC 端 App | 商家/店长 | Windows 安装包，macOS DMG/PKG，Linux 可选 | 门店房间配置、价格、设备、订单、会员、营销、提现、统计 |
| PC 端 App | 平台运营/客服 | 同上 | 租户管理、权限、异常处理、审计、设备供应商、人工补偿 |

## 客户端架构

建议采用一个 Flutter 工程，多端共享领域模型、API client、状态管理和基础组件，再按端拆分页面布局。

```text
clients/
  qipaishi_app/
    lib/
      main.dart
      app/
        router/
        theme/
        env/
      core/
        api/
        auth/
        storage/
        errors/
        telemetry/
      features/
        auth/
        stores/
        rooms/
        booking/
        orders/
        payments/
        devices/
        cleaning/
        merchant/
        analytics/
        audit/
      layouts/
        mobile/
        desktop/
      shared/
        widgets/
        models/
        utils/
    test/
    integration_test/
```

设计原则：

- 同一业务能力共享 API client 和状态模型。
- 手机端优先保证到店、开门、支付、保洁等高频现场流程。
- PC 端优先保证数据密度、表格筛选、批量操作和异常处理效率。
- 支付、开门、退款、提现等高风险动作只调用后端 API，不在客户端做最终裁决。
- 本地只保存短期 token、用户偏好和必要缓存，不保存支付密钥、硬件 token 或租户密钥。

## 手机端功能范围

### 顾客

- 登录、手机号绑定、个人资料。
- 城市/定位选店、门店详情、导航、客服、公告。
- 房间列表、图片、标签、价格、可预约时间轴。
- 下单、价格明细、优惠券、团购码、余额、微信支付。
- 订单列表、订单详情、开店门、开房门、开智能锁、开电。
- 续费、取消、换房、分享订单、帮助中心。

### 保洁员

- 任务列表、任务筛选、任务详情。
- 接单、取消接单、开始任务、到店开门、房间开门。
- 上传清洁凭证、完成任务、查看驳回原因。
- 结算记录、任务统计。

### 商家移动端

- 今日房态、今日订单、待处理异常。
- 订单取消、退款、改时、续费、换房。
- 远程开门、设备测试、房间停用。
- 保洁审核、投诉、结算确认。
- 简版营收和订单统计。

## PC 端功能范围

PC 端不是手机端的放大版，而是经营后台软件：

- 工作台：实时订单、房态、设备状态、待支付超时、待保洁、异常开门、退款待处理。
- 门店管理：门店资料、公告、Wi-Fi、客服、地址、坐标、图片。
- 房间管理：房间资料、标签、图片、价格、工作日价、通宵价、禁用时段、清洁参数。
- 设备管理：店门、房间门、智能锁、电源、云喇叭、设备命令记录、失败重试。
- 订单中心：列表、详情、取消、退款、改时、续费、换房、人工完成、审计记录。
- 会员营销：会员、余额、充值规则、优惠券、团购码核销。
- 保洁管理：任务派发、审核、投诉、驳回、结算。
- 财务：支付、退款、余额流水、提现、对账导出。
- 统计：收入、订单、退款、充值、房间使用率、保洁效率、设备成功率。
- 平台运营：租户、角色、应用绑定、设备供应商、异常补偿、审计查询。

## 与后端的关系

PC 和手机端都只依赖 `/api/v1/**` 新接口：

```text
PC App / Mobile App
  -> API Service (FastAPI)
  -> PostgreSQL / Redis / Worker
  -> WeChat Pay / Device Gateway / Object Storage / Map Service
```

客户端需要的能力由后端统一保证：

- 登录、租户、角色和门店作用域。
- 订单库存锁和价格试算。
- 支付预下单、回调确认和退款。
- 设备命令、开门授权和审计。
- 保洁任务生成、房态联动和结算。
- 统计口径、异常列表和人工补偿。

## 开发里程碑补充

| 阶段 | 客户端目标 | 后端配合 |
| --- | --- | --- |
| C0 客户端底座 | Flutter 工程、路由、主题、登录态、API client、环境配置 | M0-M1 API、OpenAPI |
| C1 手机顾客 MVP | 选店、选房、下单、支付 mock、订单详情、开门 mock | M2-M5 |
| C2 手机保洁/商家 MVP | 保洁任务、移动订单处理、移动开门、房态查看 | M5-M6 |
| C3 PC 运营 MVP | 工作台、门店房间、订单中心、设备管理、保洁审核 | M2-M7 |
| C4 资金营销统计 | 余额、优惠券、团购码、提现、统计图表 | M4-M7 |
| C5 打包发布 | Android/iOS/Windows/macOS 打包、签名、自动更新策略、灰度 | M8-M9 |

## 发布与分发

### 手机端

- Android：先支持测试 APK，再准备应用商店包和签名。
- iOS：先使用 TestFlight，再提交 App Store。
- 国内分发需要额外准备应用备案、隐私政策、权限说明和各安卓应用市场资料。

### PC 端

- Windows：优先提供安装包，后续可评估 Microsoft Store。
- macOS：提供 DMG/PKG，正式发布需要签名和公证。
- Linux：按客户环境决定是否提供 AppImage、deb 或 Snap。
- PC 端需要设计版本检查和更新策略，避免门店现场长期运行旧版本。

## App 验收标准

- 手机端顾客可以完成选店、选房、下单、支付、开门、续费、取消。
- 手机端保洁可以接单、开门、上传凭证、完成任务。
- 手机端商家可以查看房态、处理订单和保洁异常。
- PC 端商家可以完成门店、房间、价格、设备、订单、保洁、财务和统计管理。
- 平台 PC 端可以管理租户、权限、设备供应商、异常和审计。
- 手机和 PC 使用同一套后端权限，不出现客户端绕过业务规则。
- Android、iOS、Windows、macOS 至少各有一个可安装测试包。
