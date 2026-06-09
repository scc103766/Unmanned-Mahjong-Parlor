import { addHours } from "@/shared/utils/format";
import type {
  AuditLog,
  MerchantDashboard,
  OperationException,
  OrderSummary,
  RoomUsage,
  Withdrawal,
  MemberSummary,
  StoreSummary,
  RoomSummary,
  RoomDetail,
  RoomAvailability,
  PriceQuote,
  PreorderResult,
  PaymentResult,
  WalletAccount,
  CouponInfo,
  OrderItem,
} from "@/core/api/types";

const now = new Date();
const iso = (date: Date) => date.toISOString();

export const demoDashboard: MerchantDashboard = {
  tenant_id: "tenant_demo",
  store_id: null,
  start_at: iso(addHours(now, -24)),
  end_at: iso(now),
  order_count: 42,
  paid_order_count: 7,
  in_use_order_count: 5,
  completed_order_count: 28,
  cancelled_order_count: 2,
  gross_revenue: "9860.00",
  refund_amount: "220.00",
  net_revenue: "9640.00",
  wallet_recharge_amount: "3600.00",
  member_count: 318,
  room_count: 12,
  active_room_count: 10,
  dirty_room_count: 2,
  usage_hours: "136.50",
  room_utilization_rate: "0.72",
  cleaning_pending_count: 3,
  cleaning_overdue_count: 1,
  cleaning_completed_count: 18,
  cleaning_complained_count: 1,
  device_failure_count: 2,
};

export const demoRooms: RoomUsage[] = [
  { room_id: "room_a", room_name: "A01 国标麻将", order_count: 8, usage_hours: "28.5", utilization_rate: "0.81" },
  { room_id: "room_b", room_name: "B03 商务棋牌", order_count: 6, usage_hours: "21", utilization_rate: "0.66" },
  { room_id: "room_c", room_name: "C02 掼蛋包厢", order_count: 5, usage_hours: "17.5", utilization_rate: "0.52" },
];

export const demoExceptions: OperationException[] = [
  {
    id: "ex_device_1",
    tenant_id: "tenant_demo",
    store_id: "store_1",
    source: "device",
    severity: "high",
    entity_type: "device_command",
    entity_id: "cmd_1024",
    status: "open",
    message: "B03 门锁连续两次开门失败",
    occurred_at: iso(addHours(now, -1)),
    payload: { command: "unlock_room", retry_count: 2 },
  },
  {
    id: "ex_withdrawal_1",
    tenant_id: "tenant_demo",
    store_id: null,
    source: "withdrawal",
    severity: "medium",
    entity_type: "withdrawal",
    entity_id: "wd_7788",
    status: "open",
    message: "提现已审核但超过 24 小时未打款",
    occurred_at: iso(addHours(now, -4)),
    payload: { amount: "880.00" },
  },
];

export const demoWithdrawals: Withdrawal[] = [
  {
    id: "wd_1001",
    tenant_id: "tenant_demo",
    user_id: "user_1001",
    requested_by: "user_1001",
    amount: "880.00",
    status: "pending",
    remark: "本周收入提现",
    payout_payload: {},
    requested_at: iso(addHours(now, -2)),
  },
  {
    id: "wd_1002",
    tenant_id: "tenant_demo",
    user_id: "cleaner_1",
    requested_by: "cleaner_1",
    amount: "126.00",
    status: "approved",
    remark: "保洁结算",
    payout_payload: {},
    requested_at: iso(addHours(now, -27)),
    reviewed_at: iso(addHours(now, -25)),
  },
];

export const demoMembers: MemberSummary[] = [
  {
    user_id: "user_1001",
    tenant_id: "tenant_demo",
    phone: "13800000000",
    nickname: "张先生",
    status: "active",
    cash_balance: "128.00",
    gift_balance: "30.00",
    order_count: 16,
    completed_order_count: 15,
    total_spend: "2890.00",
    coupon_count: 3,
    available_coupon_count: 2,
    created_at: iso(addHours(now, -2400)),
  },
  {
    user_id: "user_1002",
    tenant_id: "tenant_demo",
    phone: "13900000000",
    nickname: "李女士",
    status: "active",
    cash_balance: "80.00",
    gift_balance: "0.00",
    order_count: 7,
    completed_order_count: 6,
    total_spend: "980.00",
    coupon_count: 1,
    available_coupon_count: 1,
    created_at: iso(addHours(now, -900)),
  },
];

export const demoOrders: OrderSummary[] = [
  {
    id: "order_1001",
    tenant_id: "tenant_demo",
    store_id: "store_1",
    room_id: "room_a",
    user_id: "user_1001",
    order_no: "QP202605150001",
    start_at: iso(addHours(now, 1)),
    end_at: iso(addHours(now, 4)),
    status: "paid",
    total_amount: "198.00",
    payable_amount: "178.00",
    pricing_snapshot: {},
    items: [],
  },
  {
    id: "order_1002",
    tenant_id: "tenant_demo",
    store_id: "store_1",
    room_id: "room_b",
    user_id: "user_1002",
    order_no: "QP202605150002",
    start_at: iso(addHours(now, -2)),
    end_at: iso(addHours(now, 2)),
    status: "in_use",
    total_amount: "288.00",
    payable_amount: "288.00",
    pricing_snapshot: {},
    items: [],
  },
];

export const demoAuditLogs: AuditLog[] = [
  {
    id: "audit_1",
    tenant_id: "tenant_demo",
    actor_id: "admin_1",
    action: "withdrawal.approve",
    target_type: "withdrawal",
    target_id: "wd_1002",
    request_id: "req_demo_1",
    ip_address: "127.0.0.1",
    payload: { note: "审核通过" },
    created_at: iso(addHours(now, -24)),
  },
  {
    id: "audit_2",
    tenant_id: "tenant_demo",
    actor_id: "admin_1",
    action: "operations.compensate",
    target_type: "user",
    target_id: "user_1001",
    request_id: "req_demo_2",
    ip_address: "127.0.0.1",
    payload: { cash_amount: "20.00", reason: "设备异常补偿" },
    created_at: iso(addHours(now, -3)),
  },
];

// Customer demo data

export const demoStores: StoreSummary[] = [
  {
    id: "store_demo_1",
    tenant_id: "tenant_demo",
    name: "24H 自助棋牌 · 朝阳店",
    address: "北京市朝阳区建国路88号SOHO现代城B座3层",
    longitude: 116.46,
    latitude: 39.91,
    notice: "本店全自助营业，请在小程序内完成预约和支付后自助开门。客服微信：qipaishi001",
    contact_phone: "18800001111",
    wifi_ssid: "Qipaishi-Chaoyang",
    wifi_password: "qp888888",
    images: [],
    business_settings: { night_start: "22:00", night_duration_hours: 8 },
    cleaning_settings: { allow_booking_dirty: false },
    status: "active",
    sort_order: 0,
  },
  {
    id: "store_demo_2",
    tenant_id: "tenant_demo",
    name: "24H 自助棋牌 · 海淀店",
    address: "北京市海淀区中关村大街27号中关村广场2层",
    longitude: 116.31,
    latitude: 39.98,
    notice: "地铁4号线中关村站A口步行3分钟即达。",
    contact_phone: "18800002222",
    wifi_ssid: "Qipaishi-Haidian",
    wifi_password: "qp666666",
    images: [],
    business_settings: {},
    cleaning_settings: {},
    status: "active",
    sort_order: 0,
  },
];

export const demoCustomerRooms: RoomSummary[] = [
  {
    id: "room_demo_1",
    tenant_id: "tenant_demo",
    store_id: "store_demo_1",
    name: "A01 国标麻将包厢",
    room_type: "mahjong",
    capacity: 4,
    tags: ["自动麻将桌", "独立空调", "空气净化器"],
    images: [],
    status: "active",
    cleaning_status: "clean",
    sort_order: 0,
  },
  {
    id: "room_demo_2",
    tenant_id: "tenant_demo",
    store_id: "store_demo_1",
    name: "B03 商务棋牌室",
    room_type: "mahjong",
    capacity: 6,
    tags: ["商务茶桌", "投影仪", "独立卫生间"],
    images: [],
    status: "active",
    cleaning_status: "clean",
    sort_order: 1,
  },
  {
    id: "room_demo_3",
    tenant_id: "tenant_demo",
    store_id: "store_demo_1",
    name: "C02 掼蛋包厢",
    room_type: "card",
    capacity: 4,
    tags: ["圆桌", "舒适沙发"],
    images: [],
    status: "active",
    cleaning_status: "dirty",
    sort_order: 2,
  },
];

export const demoPriceQuote: PriceQuote = {
  room_id: "room_demo_1",
  price_rule_id: "rule_1",
  currency: "CNY",
  start_at: iso(addHours(now, 1)),
  end_at: iso(addHours(now, 4)),
  duration_hours: "3.0",
  billable_hours: "3.0",
  unit_price: "66.00",
  subtotal_amount: "198.00",
  total_amount: "198.00",
  details: [{ item: "基础房价", hours: "3.0", unit: "66.00", amount: "198.00" }],
};

export const demoPreorder: PreorderResult = {
  order_id: "order_demo_1",
  payable_amount: "198.00",
  expires_at: iso(addHours(now, 1)),
};

export const demoPayment: PaymentResult = {
  id: "pay_demo_1",
  tenant_id: "tenant_demo",
  order_id: "order_demo_1",
  channel: "wechat",
  amount: "198.00",
  status: "succeeded",
  transaction_id: "wx_txn_demo_001",
  provider_payload: {},
  paid_at: iso(now),
};

export const demoWallet: WalletAccount = {
  id: "wallet_demo",
  tenant_id: "tenant_demo",
  user_id: "user_customer",
  cash_balance: "200.00",
  gift_balance: "30.00",
  status: "active",
};

export const demoCoupons: CouponInfo[] = [
  {
    id: "coupon_demo_1",
    tenant_id: "tenant_demo",
    user_id: "user_customer",
    template_id: "tmpl_1",
    status: "available",
    name: "新客专享券",
    amount: "20.00",
    min_order_amount: "100.00",
    expires_at: iso(addHours(now, 720)),
  },
  {
    id: "coupon_demo_2",
    tenant_id: "tenant_demo",
    user_id: "user_customer",
    template_id: "tmpl_2",
    status: "available",
    name: "周末特惠券",
    amount: "10.00",
    min_order_amount: "50.00",
    expires_at: iso(addHours(now, 240)),
  },
];

export const demoCustomerOrders: OrderSummary[] = [
  {
    id: "order_demo_1",
    tenant_id: "tenant_demo",
    store_id: "store_demo_1",
    room_id: "room_demo_1",
    user_id: "user_customer",
    order_no: "QP20260608001",
    start_at: iso(addHours(now, 2)),
    end_at: iso(addHours(now, 5)),
    status: "paid",
    total_amount: "198.00",
    payable_amount: "178.00",
    pricing_snapshot: {},
    expires_at: null,
    paid_at: iso(addHours(now, -1)),
    items: [
      {
        id: "item_demo_1",
        order_id: "order_demo_1",
        item_type: "room_rental",
        description: "A01 国标麻将包厢 3小时",
        quantity: "3.0",
        unit_price: "66.00",
        amount: "198.00",
      },
    ],
  },
];

// Cleaner demo data

export const demoCleaningTasks: import("@/core/api/types").CleaningTask[] = [
  {
    id: "ct_demo_1",
    tenant_id: "tenant_demo",
    store_id: "store_demo_1",
    room_id: "room_demo_1",
    order_id: "order_demo_1",
    cleaner_id: null,
    status: "pending",
    scheduled_start_at: iso(addHours(now, 1)),
    scheduled_end_at: iso(addHours(now, 2)),
    settlement_amount: "30.00",
    created_at: iso(addHours(now, -0.5)),
  },
  {
    id: "ct_demo_2",
    tenant_id: "tenant_demo",
    store_id: "store_demo_1",
    room_id: "room_demo_2",
    order_id: "order_demo_2",
    cleaner_id: "cleaner_user",
    status: "in_progress",
    scheduled_start_at: iso(addHours(now, -0.5)),
    scheduled_end_at: iso(addHours(now, 0.5)),
    accepted_at: iso(addHours(now, -1)),
    started_at: iso(addHours(now, -0.5)),
    settlement_amount: "25.00",
    created_at: iso(addHours(now, -2)),
  },
  {
    id: "ct_demo_3",
    tenant_id: "tenant_demo",
    store_id: "store_demo_1",
    room_id: "room_demo_3",
    order_id: "order_demo_3",
    cleaner_id: "cleaner_user",
    status: "completed",
    scheduled_start_at: iso(addHours(now, -4)),
    scheduled_end_at: iso(addHours(now, -3)),
    accepted_at: iso(addHours(now, -5)),
    started_at: iso(addHours(now, -4)),
    completed_at: iso(addHours(now, -3)),
    settlement_amount: "28.00",
    created_at: iso(addHours(now, -6)),
  },
  {
    id: "ct_demo_4",
    tenant_id: "tenant_demo",
    store_id: "store_demo_2",
    room_id: "room_demo_5",
    order_id: "order_demo_4",
    cleaner_id: "cleaner_user",
    status: "accepted",
    scheduled_start_at: iso(addHours(now, 0.5)),
    scheduled_end_at: iso(addHours(now, 1.5)),
    accepted_at: iso(addHours(now, -0.2)),
    settlement_amount: "22.00",
    created_at: iso(addHours(now, -1)),
  },
];

export const demoCleaningSummary: import("@/core/api/types").CleaningSummary = {
  pending_count: 2,
  overdue_count: 1,
  in_progress_count: 1,
  complained_count: 0,
  overdue_task_ids: ["ct_demo_3"],
};

// Platform demo data

export const demoTenants: import("@/core/api/types").TenantInfo[] = [
  {
    id: "tenant_demo",
    name: "示例棋牌室",
    status: "active",
    plan: "standard",
    settings: { max_stores: 10, max_rooms: 50 },
    created_at: iso(addHours(now, -720)),
  },
  {
    id: "tenant_demo_2",
    name: "朝阳共享茶室",
    status: "active",
    plan: "basic",
    settings: { max_stores: 3, max_rooms: 15 },
    created_at: iso(addHours(now, -480)),
  },
];

export const demoTenantApps: import("@/core/api/types").TenantApp[] = [
  { id: "app_1", tenant_id: "tenant_demo", client_type: "h5", app_id: "dev-h5", status: "active", created_at: iso(addHours(now, -700)) },
  { id: "app_2", tenant_id: "tenant_demo", client_type: "miniapp", app_id: "wx1234567890", status: "active", created_at: iso(addHours(now, -600)) },
];

export const demoUsers: import("@/core/api/types").UserInfo[] = [
  { id: "user_admin", tenant_id: "tenant_demo", phone: "18800000000", nickname: "开发管理员", status: "active", roles: ["merchant_admin"], store_ids: [], created_at: iso(addHours(now, -700)) },
  { id: "user_customer", tenant_id: "tenant_demo", phone: "18800001111", nickname: "顾客_小明", status: "active", roles: ["customer"], store_ids: [], created_at: iso(addHours(now, -500)) },
  { id: "user_cleaner", tenant_id: "tenant_demo", phone: "18800003333", nickname: "保洁员_李姐", status: "active", roles: ["cleaner"], store_ids: [], created_at: iso(addHours(now, -300)) },
];

export const demoRoles: import("@/core/api/types").RoleInfo[] = [
  { id: "role_1", name: "platform_admin", label: "平台管理员", description: "最高权限" },
  { id: "role_2", name: "merchant_admin", label: "商家管理员", description: "门店管理" },
  { id: "role_3", name: "clerk", label: "店员", description: "日常运营" },
  { id: "role_4", name: "cleaner", label: "保洁员", description: "保洁任务" },
  { id: "role_5", name: "customer", label: "顾客", description: "预约消费" },
];

export const demoDevices: import("@/core/api/types").DeviceInfo[] = [
  { id: "dev_1", tenant_id: "tenant_demo", store_id: "store_demo_1", room_id: "room_demo_1", name: "A01 智能门锁", device_type: "room_lock", provider: "mock", external_id: "lock_a01", status: "active", capabilities: { open: true, close: true }, created_at: iso(addHours(now, -400)) },
  { id: "dev_2", tenant_id: "tenant_demo", store_id: "store_demo_1", room_id: null, name: "朝阳店大门", device_type: "store_door", provider: "mock", external_id: "door_store_1", status: "active", capabilities: { open: true }, created_at: iso(addHours(now, -400)) },
  { id: "dev_3", tenant_id: "tenant_demo_2", store_id: "store_demo_2", room_id: null, name: "海淀店大门", device_type: "store_door", provider: "mock", external_id: "door_store_2", status: "active", capabilities: { open: true }, created_at: iso(addHours(now, -300)) },
];
