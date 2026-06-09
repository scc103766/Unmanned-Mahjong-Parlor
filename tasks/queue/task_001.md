# 任务单 #1

**任务名称**：M8 顾客 H5 移动端开发 — 核心业务闭环
**优先级**：P0
**依赖**：无（后端 API 已完成）

---

## 任务描述

在 `web/` 工程中新增顾客 H5 移动端页面，实现完整的顾客业务闭环：选店 → 选房 → 试算价格 → 下单 → 支付 → 订单详情 → 开门。

---

## 技术背景

### 工程结构
- 项目根目录：`/supercloud/llm-code/scc/scc/project_robot/python_24_qipaishi/web/`
- 框架：Vue 3 + Vite + TypeScript + Pinia + Vue Router
- 现有：商家后台路由 (`/` → `MerchantLayout`)，已完整运行
- 代码风格：自研轻量 CSS（无 Element Plus），移动端 first

### 关键参考文件（请先阅读）
| 文件 | 用途 |
|------|------|
| `src/app/router/index.ts` | 路由配置（需新增 customer 路由） |
| `src/app/stores/session.ts` | Pinia 登录态（可直接复用） |
| `src/core/api/client.ts` | Axios API client + `merchantApi` 模式 |
| `src/core/api/types.ts` | TypeScript 类型定义（需补充顾客类型） |
| `src/shared/utils/format.ts` | 格式化工具（金额/时间/百分比） |
| `src/layouts/merchant/MerchantLayout.vue` | 商家后台布局参考 |
| `src/modules/merchant/views/DashboardView.vue` | 页面对接 API 的参考模式 |
| `src/App.vue` | 根组件 |
| `src/main.ts` | 入口 |
| `vite.config.ts` | Vite 配置 |
| `tsconfig.json` | TS 配置 |

### 后端 API（已可用）

运行后端服务命令：
```bash
cd /supercloud/llm-code/scc/scc/project_robot/python_24_qipaishi
QIPAISHI_DATABASE_URL=sqlite+aiosqlite:///./dev.db \
QIPAISHI_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173 \
conda run -n anti-spoofing_scc_175 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

获取登录 token（顾客身份）：
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/dev-bootstrap \
  -H 'content-type: application/json' \
  -d '{"tenant_name":"示例棋牌室","client_type":"h5","app_id":"dev-h5"}'
```

---

## 输出要求

### 1. 新增文件

#### 1.1 `src/core/api/customer.ts` — 顾客端 API 封装

参考 `client.ts` 中 `merchantApi` 的模式（使用 `apiGet`/`apiPost`），封装以下顾客端 API：

```
- listStores(params?)           → GET /api/v1/stores
- getStore(id)                  → GET /api/v1/stores/{id}
- listRooms(params?)            → GET /api/v1/rooms
- getRoomAvailability(params)   → GET /api/v1/availability/rooms
- quotePrice(body)              → POST /api/v1/pricing/quote
- createPreorder(body)          → POST /api/v1/orders/preorder
- createOrder(body)             → POST /api/v1/orders
- getOrder(id)                  → GET /api/v1/orders/{id}
- listMyOrders()                → GET /api/v1/orders
- wechatPrepay(body)            → POST /api/v1/payments/wechat/prepay
- mockPayCallback(body)         → POST /api/v1/payments/wechat/callback
- openStoreDoor(orderId)        → POST /api/v1/orders/{orderId}/open-store-door
- openRoomDoor(orderId)         → POST /api/v1/orders/{orderId}/open-room-door
- getMyWallet()                 → GET /api/v1/wallets/me
- getMyCoupons()                → GET /api/v1/coupons
```

#### 1.2 `src/layouts/customer/CustomerLayout.vue` — 顾客移动布局

- 移动优先设计：`max-width: 480px; margin: 0 auto;` 居中，模拟手机视口
- 底部 Tab 导航栏（固定于底部）：
  - 🏠 首页（门店列表）
  - 📋 订单
  - 👤 我的
- 顶部标题栏（显示当前页面标题）
- 使用 `<router-view>` 渲染子页面

#### 1.3 `src/modules/customer/views/StoresView.vue` — 门店列表页

- 页面加载时调用 `customerApi.listStores()` 获取门店列表
- 每个门店卡片显示：封面图（占位）、名称、地址、距离（如有）、营业状态
- 点击卡片跳转到 `StoreDetailView`
- 顶部搜索框（可选，先做静态）
- 遵循 `merchantApi` 页面的模式：`loading`/`error`/数据状态管理

#### 1.4 `src/modules/customer/views/StoreDetailView.vue` — 门店详情+房间列表

- 页面顶部：门店头图（占位）、名称、地址、公告、Wi-Fi信息
- 下方房间列表：每个房间卡片显示图片（占位）、名称、标签、价格区间、可约状态
- 点击房间跳转到 `BookingView`，传递 `store_id` 和 `room_id`（通过路由 params 或 query）
- 从 API 获取：`getStore(id)` + `listRooms({store_id})`

#### 1.5 `src/modules/customer/views/BookingView.vue` — 预约下单页

- 展示选中房间的基本信息
- 选择日期（简单日期选择器，至少支持今天和明天）
- 选择开始时间（小时选择器，如 09:00-23:00）
- 选择消费时长（预设按钮：2小时/4小时/6小时/通宵）
- 点击"试算价格"调用 `customerApi.quotePrice()`
- 展示价格明细：原价、优惠抵扣、应付金额
- 底部"立即预订"按钮 → 调用 `createPreorder()` → 跳转 `OrderConfirmView`
- 状态管理：`loading`/`error`

#### 1.6 `src/modules/customer/views/OrderConfirmView.vue` — 确认订单+支付

- 接收路由参数：`order_id`（从预订单获取）
- 展示订单摘要：门店、房间、时间、时长、金额
- 支付方式选择：微信支付 / 余额支付（简单 radio 切换）
- 可用优惠券列表（调用 `getMyCoupons()`）
- 点击"去支付"：
  - 若选微信支付 → 调用 `wechatPrepay()` → 模拟跳转 → 调用 `mockPayCallback()` → 跳转订单详情
  - 若选余额 → 调用 `createOrder()` 直接完成 → 跳转订单详情
- 支付过程的 loading 和错误处理

#### 1.7 `src/modules/customer/views/OrderDetailView.vue` — 订单详情

- 展示订单完整信息：门店、房间、时间段、金额、状态
- 状态标签（待支付/已支付/进行中/已完成/已取消）
- 根据状态显示操作按钮：
  - 待支付 → "去支付"按钮
  - 已支付/进行中 → "开门" / "开锁" / "续费" 按钮
  - 进行中 → "取消订单"（确认弹窗）
- 开门操作调用 `openStoreDoor()`/`openRoomDoor()`，展示结果 toast
- 续费跳转到续费页（可以简化：弹窗选择追加时长，调用续费API）

#### 1.8 `src/modules/customer/views/OrdersView.vue` — 我的订单列表

- 调用 `customerApi.listMyOrders()` 获取订单列表
- 每个订单卡片：门店名、房间名、时间段、金额、状态标签
- 点击跳转到 `OrderDetailView`
- 按状态筛选 tabs：全部/待支付/进行中/已完成

### 2. 修改文件

#### 2.1 `src/app/router/index.ts`

新增顾客路由：

```typescript
{
  path: "/customer",
  component: CustomerLayout,
  redirect: { name: "customer-stores" },
  children: [
    {
      path: "stores",
      name: "customer-stores",
      component: () => import("@/modules/customer/views/StoresView.vue"),
      meta: { title: "门店", roles: [] },  // 公开访问
    },
    {
      path: "stores/:storeId",
      name: "customer-store-detail",
      component: () => import("@/modules/customer/views/StoreDetailView.vue"),
      meta: { title: "门店详情", roles: [] },
    },
    {
      path: "booking",
      name: "customer-booking",
      component: () => import("@/modules/customer/views/BookingView.vue"),
      meta: { title: "预约", roles: ["customer"] },
    },
    {
      path: "order-confirm",
      name: "customer-order-confirm",
      component: () => import("@/modules/customer/views/OrderConfirmView.vue"),
      meta: { title: "确认订单", roles: ["customer"] },
    },
    {
      path: "orders/:orderId",
      name: "customer-order-detail",
      component: () => import("@/modules/customer/views/OrderDetailView.vue"),
      meta: { title: "订单详情", roles: ["customer"] },
    },
    {
      path: "orders",
      name: "customer-orders",
      component: () => import("@/modules/customer/views/OrdersView.vue"),
      meta: { title: "我的订单", roles: ["customer"] },
    },
  ],
},
```

**注意**：`CustomerLayout` 使用 `() => import("@/layouts/customer/CustomerLayout.vue")` 懒加载。

#### 2.2 `src/core/api/types.ts`

补充顾客端需要的类型（根据后端 API 响应结构，可参考已有类型扩展）：

```typescript
// 已有类型可复用：Store, Room, Order, Payment 等来自 backend
// 需要补充或确认的类型：
export interface StoreSummary { id: string; name: string; address: string; cover_image?: string; is_open: boolean; }
export interface RoomSummary { id: string; name: string; category: string; price_range: string; image?: string; }
export interface RoomAvailability { room_id: string; date: string; available_slots: TimeSlot[]; }
export interface TimeSlot { start: string; end: string; available: boolean; }
export interface PriceQuote { original_amount: string; discount_amount: string; payable_amount: string; breakdown: PriceBreakdown[]; }
export interface PriceBreakdown { item: string; amount: string; }
export interface PreorderResult { order_id: string; payable_amount: string; expires_at: string; }
export interface WalletAccount { balance: string; gift_balance: string; }
export interface CouponInfo { id: string; name: string; amount: string; min_order: string; expires_at: string; }
```

### 3. `src/core/api/demo.ts` 补充

为顾客端页面补充 demo 数据，确保**无 Token 时也能预览页面结构**（与商家后台模式一致）。至少覆盖门店列表和房间列表的 demo 数据。

---

## 🧠 开发思路（为什么这样做）

1. **复用现有架构**：`customerApi` 沿用 `merchantApi` 的 `apiGet`/`apiPost` 封装模式；顾客页面复用 `session store` 判断登录态
2. **移动优先**：顾客 H5 的核心用户场景在手机上，`max-width: 480px` + 底部 Tab 是标准移动 H5 模式
3. **渐进增强**：先从静态页面骨架开始，能展示 demo 数据；再接入真实 API；确保无后端时也能预览
4. **状态管理简单化**：每个页面独立管理 `loading/error/data`，不使用全局 store（顾客场景简单，页面间通过路由传参即可）
5. **权限灵活**：门店/房间浏览设为公开访问（`roles: []`），下单/支付需要 customer 角色

---

## 验收标准

1. ✅ `npm run build` 构建通过，无新增 TypeScript 错误
2. ✅ 无 Token 时，顾客页面展示 demo 数据，布局正常
3. ✅ 有 Token 时（通过商家后台 Settings 页签获取），能完成以下完整闭环：
   - 浏览门店列表 → 进入门店查看房间 → 选择房间和时间 → 试算价格 → 提交预订单 → 确认支付（mock） → 查看订单详情 → 模拟开门
4. ✅ 顾客路由 `/customer/stores` 可独立访问
5. ✅ 顾客端与商家后台 `/` 可在同一工程中并存，不互相干扰
6. ✅ 移动布局在 375–480px 宽度下正常显示
7. ✅ 错误状态有友好提示（网络错误、token 过期等）

---

## 文件变更清单

| 操作 | 文件路径 | 说明 |
|------|---------|------|
| 新增 | `web/src/core/api/customer.ts` | 顾客端 API 封装 |
| 新增 | `web/src/layouts/customer/CustomerLayout.vue` | 顾客移动布局 |
| 新增 | `web/src/modules/customer/views/StoresView.vue` | 门店列表 |
| 新增 | `web/src/modules/customer/views/StoreDetailView.vue` | 门店详情+房间 |
| 新增 | `web/src/modules/customer/views/BookingView.vue` | 预约下单 |
| 新增 | `web/src/modules/customer/views/OrderConfirmView.vue` | 确认支付 |
| 新增 | `web/src/modules/customer/views/OrderDetailView.vue` | 订单详情 |
| 新增 | `web/src/modules/customer/views/OrdersView.vue` | 我的订单 |
| 修改 | `web/src/app/router/index.ts` | 新增顾客路由 |
| 修改 | `web/src/core/api/types.ts` | 补充顾客类型 |
| 修改 | `web/src/core/api/demo.ts` | 补充顾客 demo 数据 |

---

## 📚 参考来源

- 现有商家后台代码：`web/src/modules/merchant/views/*.vue`
- 后端 API 代码：`app/api/v1/routers/stores.py`, `rooms.py`, `orders.py`, `payments.py`, `pricing.py`, `availability.py`
- BMAD PRD：`../24h_qipaishi/_bmad-output/planning-artifacts/prd.md`
- 架构文档：`docs/02-python-architecture-plan.md`
