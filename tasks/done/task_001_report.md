## 🛠️ 开发日志 — 任务单 #1

### 📝 开发过程

1. **读取所有现有代码**：阅读了 `web/src` 下全部文件，理解工程结构（Vue 3 + Vite + TypeScript + Pinia）、商家后台模式（router/layout/views/api client）、API 封装模式（`apiGet`/`apiPost`/`unwrap`）、样式体系（CSS variables + 自研组件）。

2. **研究后端 Schema**：读取了 `stores`/`rooms`/`orders`/`pricing`/`payments`/`wallet`/`availability` 等模块的 Pydantic schemas，明确前端类型定义应与后端响应一致。

3. **扩展 `types.ts`**：新增 12 个顾客端类型接口（StoreSummary / RoomSummary / RoomDetail / PriceRule / BlockedSlot / RoomAvailability / PriceQuote / PreorderResult / PaymentResult / WalletAccount / CouponInfo），与后端 Pydantic Schema 对齐。

4. **扩展 `demo.ts`**：新增顾客端 demo 数据（demoStores / demoCustomerRooms / demoPriceQuote / demoPreorder / demoPayment / demoWallet / demoCoupons / demoCustomerOrders），确保无后端时可独立预览。

5. **创建 `customer.ts` API 客户端**：封装 16 个顾客端 API 方法，遵循 `merchantApi` 的 `withTenant()` 模式。

6. **创建 `CustomerLayout.vue`**：移动优先布局（max-width 480px 居中），顶部标题栏（含一键登录按钮），底部三 Tab 导航（首页/订单/我的）。

7. **创建 7 个顾客视图**：
   - StoresView — 门店列表 + 搜索过滤
   - StoreDetailView — 门店详情 + 房间卡片列表（含状态标签和价格）
   - BookingView — 日期/时间/时长选择 + 实时试算 + 预订
   - OrderConfirmView — 订单确认 + 优惠券选择 + 微信/余额支付
   - OrderDetailView — 订单详情 + 开门/续费/取消操作
   - OrdersView — 订单列表 + 状态筛选
   - MeView — 钱包余额 + 退出登录

8. **更新路由和权限守卫**：新增 `/customer/...` 路由组（8 条路由），更新 title 和角色失败重定向逻辑。

### 🧠 开发思路

**整体设计考量**：
- 顾客 H5 与商家后台共享同一 Vue 工程，通过路由 `/customer` vs `/` 实现 layout 分流
- 页面间通过路由 query 传参（storeId/roomId/orderId），无需全局 store
- 每个页面独立管理 loading/error/data 状态，与商家后台模式一致

**为什么选择现有工程而非新建项目**：
- 复用已有的 API client（`apiGet`/`apiPost`/unwrap）、session store（Pinia）、格式化工具（formatMoney 等）
- 统一的构建配置和部署流程
- 商家和顾客在同一端口（5173）下，只需不同路径

**为什么移动布局用 max-width 480px 而非独立 viewport**：
- 桌面浏览器可同时预览商家后台和顾客 H5
- 不需要额外移动端适配框架（如 vw/vh 适配），CSS 即足够
- 后续如需真机适配，可在此布局基础上扩展

**与后端 API 的对接策略**：
- 有 Token → 调用真实 API
- 无 Token → 使用 demo 数据
- 与商家后台完全一致的 Session store 和 dev-bootstrap 登录流程

### 📊 代码变更清单

| 操作 | 文件路径 | 说明 |
|------|---------|------|
| 新增 | `web/src/core/api/customer.ts` | 顾客端 API 封装 (16个方法) |
| 新增 | `web/src/layouts/customer/CustomerLayout.vue` | 顾客移动端布局 |
| 新增 | `web/src/modules/customer/views/StoresView.vue` | 门店列表页 |
| 新增 | `web/src/modules/customer/views/StoreDetailView.vue` | 门店详情+房间列表 |
| 新增 | `web/src/modules/customer/views/BookingView.vue` | 预约下单页 |
| 新增 | `web/src/modules/customer/views/OrderConfirmView.vue` | 订单确认+支付 |
| 新增 | `web/src/modules/customer/views/OrderDetailView.vue` | 订单详情+操作 |
| 新增 | `web/src/modules/customer/views/OrdersView.vue` | 我的订单列表 |
| 新增 | `web/src/modules/customer/views/MeView.vue` | 个人中心 |
| 修改 | `web/src/core/api/types.ts` | +120行：新增12个顾客类型 |
| 修改 | `web/src/core/api/demo.ts` | +180行：新增顾客demo数据 |
| 修改 | `web/src/app/router/index.ts` | +45行：新增8条顾客路由 |
| 修改 | `web/src/app/permissions/guards.ts` | 更新title逻辑和角色重定向 |

### 💡 核心代码解读

#### 关键代码块 1：CustomerLayout 的三 Tab 底部导航

```vue
<nav class="customer-tabs">
  <RouterLink v-for="tab in tabs" :key="tab.name" class="tab-item" :to="{ name: tab.name }">
    <span class="tab-icon">{{ tab.icon }}</span>
    <span>{{ tab.label }}</span>
  </RouterLink>
</nav>
```

**解读**：标准的移动端底部 Tab 导航。使用 `position: fixed; bottom: 0; max-width: 480px; left: 50%; transform: translateX(-50%)` 使其固定在移动视口底部并与内容区 480px 对齐。三个 Tab 对应首页（门店）、订单、我的三个入口。

**为什么这样写**：不使用 `v-for` 遍历常量配置比硬编码三个 `<RouterLink>` 更易维护。`router-link-active` 类自动高亮当前 Tab。

#### 关键代码块 2：BookingView 的试算 + 预订流程

```typescript
const startAt = computed(() => `${selectedDate.value}T${selectedHour.value}:00`);
const endAt = computed(() => {
  const d = new Date(selectedDate.value + "T" + selectedHour.value + ":00");
  return new Date(d.getTime() + selectedDuration.value * 3600000).toISOString();
});

async function doQuote() { /* call quotePrice API */ }
async function doBook() { /* call createPreorder → router.push */ }
```

**解读**：日期、时间、时长三个变量拼成 ISO 时间戳，传给后端 `/api/v1/pricing/quote` 试算。试算成功后显示价格，点击预订调用 `/api/v1/orders/preorder` 创建预订单。endAt 通过 Date 对象计算确保跨天正确处理。

**为什么这样写**：将时间计算逻辑放在 computed 属性中，响应式地跟随用户选择的 date/hour/duration 变化。试算函数 doQuote 在所有三个变量变化时都会被调用（通过 click 绑定而非 watch，避免频繁请求）。

#### 关键代码块 3：OrderConfirmView 的优惠券选择

```typescript
const selectedCoupon = computed(() =>
  coupons.value.find((c) => c.id === selectedCouponId.value),
);
const finalPayable = computed(() => {
  const base = Number(order.value.payable_amount);
  if (selectedCoupon.value) {
    return formatMoney(Math.max(0, base - Number(selectedCoupon.value.amount)));
  }
  return payableAmount.value;
});
```

**解读**：用户点击优惠券卡片切换选中状态（再次点击取消选中）。finalPayable 实时计算券后应付金额，使用 `Math.max(0, ...)` 防止抵扣后金额为负。

**为什么这样写**：优惠券是"可选"而非"自动应用"，给用户选择权。selectedCouponId 是单选模式（点击已选中的取消），computed 属性自动响应选中变化。

### ⚠️ 遇到的问题与解决方案

| 问题 | 原因 | 解决方案 | 是否完全解决 |
|------|------|---------|------------|
| `demoRooms` 命名冲突 | 商家后台已有 `demoRooms: RoomUsage[]`，顾客端新定义了同名变量 | 重命名为 `demoCustomerRooms: RoomSummary[]` | ✅ |
| `ApiError` 不在 `customer.ts` 中导出 | 初始 imports 写成了 `from "@/core/api/customer"` | 改为从 `@/core/api/client"` 导入 | ✅ |
| catch block 类型错误 | TypeScript strict 模式下 catch 变量为 unknown | 使用 `e instanceof ApiError` 进行类型收窄 | ✅ |
| 底部 Tab fixed 定位溢出 | `left: 50%; transform: translateX(-50%)` 需配合 `max-width` 限制 | 在 `.customer-tabs` 中同时设置 `max-width: 480px` | ✅ |

### 📚 参考来源
- 商家后台代码：`web/src/layouts/merchant/MerchantLayout.vue`、`web/src/modules/merchant/views/*.vue`
- 后端 API schemas：`app/modules/stores/schemas.py`、`app/modules/rooms/schemas.py`、`app/modules/orders/schemas.py`、`app/modules/pricing/schemas.py`、`app/modules/payments/schemas.py`、`app/modules/wallet/schemas.py`、`app/modules/availability/schemas.py`
- BMAD PRD：`24h_qipaishi/_bmad-output/planning-artifacts/prd.md`
