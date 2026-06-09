export type MoneyLike = string | number;

export interface ApiEnvelope<T> {
  code: number;
  message: string;
  data: T;
  request_id?: string | null;
}

export interface Principal {
  user_id: string;
  tenant_id?: string | null;
  phone?: string | null;
  nickname?: string | null;
  roles: string[];
  store_ids: string[];
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: Principal;
}

export interface DevBootstrapRequest {
  tenant_name: string;
  client_type: string;
  app_id: string;
  phone?: string;
  nickname?: string;
}

export interface QueryRange {
  tenant_id?: string;
  store_id?: string;
  start_at?: string;
  end_at?: string;
  limit?: number;
}

export interface MerchantDashboard {
  tenant_id: string;
  store_id?: string | null;
  start_at: string;
  end_at: string;
  order_count: number;
  paid_order_count: number;
  in_use_order_count: number;
  completed_order_count: number;
  cancelled_order_count: number;
  gross_revenue: MoneyLike;
  refund_amount: MoneyLike;
  net_revenue: MoneyLike;
  wallet_recharge_amount: MoneyLike;
  member_count: number;
  room_count: number;
  active_room_count: number;
  dirty_room_count: number;
  usage_hours: MoneyLike;
  room_utilization_rate: MoneyLike;
  cleaning_pending_count: number;
  cleaning_overdue_count: number;
  cleaning_completed_count: number;
  cleaning_complained_count: number;
  device_failure_count: number;
}

export interface RoomUsage {
  room_id: string;
  room_name: string;
  order_count: number;
  usage_hours: MoneyLike;
  utilization_rate: MoneyLike;
}

export interface RoomUsageList {
  tenant_id: string;
  store_id?: string | null;
  start_at: string;
  end_at: string;
  rooms: RoomUsage[];
}

export interface CleaningAnalytics {
  tenant_id: string;
  store_id?: string | null;
  start_at: string;
  end_at: string;
  pending_count: number;
  accepted_count: number;
  in_progress_count: number;
  pending_review_count: number;
  completed_count: number;
  rejected_count: number;
  canceled_count: number;
  complained_count: number;
  settled_count: number;
  overdue_count: number;
  settlement_amount: MoneyLike;
}

export interface OperationException {
  id: string;
  tenant_id?: string | null;
  store_id?: string | null;
  source: string;
  severity: string;
  entity_type: string;
  entity_id: string;
  status: string;
  message: string;
  occurred_at: string;
  payload: Record<string, unknown>;
}

export interface OperationExceptionList {
  exceptions: OperationException[];
}

export interface AuditLog {
  id: string;
  tenant_id?: string | null;
  actor_id?: string | null;
  action: string;
  target_type: string;
  target_id?: string | null;
  request_id?: string | null;
  ip_address?: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogList {
  logs: AuditLog[];
}

export interface Withdrawal {
  id: string;
  tenant_id: string;
  user_id: string;
  requested_by: string;
  amount: MoneyLike;
  status: string;
  remark?: string | null;
  review_note?: string | null;
  reject_reason?: string | null;
  payout_ref?: string | null;
  payout_payload: Record<string, unknown>;
  requested_at: string;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  paid_by?: string | null;
  paid_at?: string | null;
  rejected_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MemberSummary {
  user_id: string;
  tenant_id: string;
  phone?: string | null;
  nickname?: string | null;
  status: string;
  cash_balance: MoneyLike;
  gift_balance: MoneyLike;
  order_count: number;
  completed_order_count: number;
  total_spend: MoneyLike;
  coupon_count: number;
  available_coupon_count: number;
  created_at?: string | null;
}

export interface MemberList {
  members: MemberSummary[];
}

// Customer types

export interface StoreSummary {
  id: string;
  tenant_id: string;
  name: string;
  address?: string | null;
  longitude?: number | null;
  latitude?: number | null;
  notice?: string | null;
  contact_phone?: string | null;
  wifi_ssid?: string | null;
  wifi_password?: string | null;
  images: string[];
  business_settings: Record<string, unknown>;
  cleaning_settings: Record<string, unknown>;
  status: string;
  sort_order: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface RoomSummary {
  id: string;
  tenant_id: string;
  store_id: string;
  name: string;
  room_type?: string | null;
  capacity: number;
  tags: string[];
  images: string[];
  status: string;
  cleaning_status: string;
  sort_order: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface RoomDetail extends RoomSummary {
  price_rules: PriceRule[];
  blocked_slots: BlockedSlot[];
}

export interface PriceRule {
  id: string;
  tenant_id: string;
  room_id: string;
  name: string;
  base_price: MoneyLike;
  weekday_prices: Record<string, unknown>;
  night_price?: MoneyLike | null;
  min_hours: number;
  advance_booking_days: number;
  status: string;
}

export interface BlockedSlot {
  id: string;
  tenant_id: string;
  room_id: string;
  start_at: string;
  end_at: string;
  reason?: string | null;
  status: string;
}

export interface RoomAvailability {
  room_id: string;
  store_id: string;
  start_at: string;
  end_at: string;
  available: boolean;
  conflict_reasons: string[];
}

export interface PriceQuote {
  room_id: string;
  price_rule_id: string;
  currency: string;
  start_at: string;
  end_at: string;
  duration_hours: MoneyLike;
  billable_hours: MoneyLike;
  unit_price: MoneyLike;
  subtotal_amount: MoneyLike;
  total_amount: MoneyLike;
  details: Record<string, unknown>[];
}

export interface PreorderResult {
  order_id: string;
  payable_amount: MoneyLike;
  expires_at: string;
}

export interface PaymentResult {
  id: string;
  tenant_id: string;
  order_id: string;
  channel: string;
  amount: MoneyLike;
  status: string;
  transaction_id?: string | null;
  idempotency_key?: string | null;
  provider_payload: Record<string, unknown>;
  paid_at?: string | null;
  created_at?: string | null;
}

export interface WalletAccount {
  id: string;
  tenant_id: string;
  user_id: string;
  cash_balance: MoneyLike;
  gift_balance: MoneyLike;
  status: string;
}

export interface CouponInfo {
  id: string;
  tenant_id: string;
  user_id: string;
  template_id: string;
  status: string;
  name?: string | null;
  amount: MoneyLike;
  min_order_amount?: MoneyLike | null;
  expires_at?: string | null;
}

export interface OrderItem {
  id: string;
  order_id: string;
  item_type: string;
  description?: string | null;
  quantity: MoneyLike;
  unit_price: MoneyLike;
  amount: MoneyLike;
}

export interface OrderSummary {
  id: string;
  tenant_id: string;
  store_id: string;
  room_id: string;
  user_id: string;
  order_no: string;
  start_at: string;
  end_at: string;
  status: string;
  total_amount: MoneyLike;
  payable_amount: MoneyLike;
  pricing_snapshot: Record<string, unknown>;
  expires_at?: string | null;
  paid_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  cancelled_at?: string | null;
  cancel_reason?: string | null;
  items: OrderItem[];
}

export interface OrderRescheduleQuote {
  order_id: string;
  room_id: string;
  original_start_at: string;
  original_end_at: string;
  new_start_at: string;
  new_end_at: string;
  original_amount: MoneyLike;
  new_amount: MoneyLike;
  delta_amount: MoneyLike;
  pricing_quote: Record<string, unknown>;
}

export interface ManualCompensationRequest {
  tenant_id?: string | null;
  user_id: string;
  cash_amount: MoneyLike;
  gift_amount: MoneyLike;
  coupon_template_id?: string | null;
  reason: string;
}

export interface ManualCompensationResponse {
  user_id: string;
  cash_amount: MoneyLike;
  gift_amount: MoneyLike;
  coupon_id?: string | null;
  wallet_account_id?: string | null;
}

// Cleaner types

export interface CleaningTask {
  id: string;
  tenant_id: string;
  store_id: string;
  room_id: string;
  order_id: string;
  cleaner_id?: string | null;
  status: string;
  scheduled_start_at?: string | null;
  scheduled_end_at?: string | null;
  accepted_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  reviewed_at?: string | null;
  settled_at?: string | null;
  canceled_at?: string | null;
  review_note?: string | null;
  cancel_reason?: string | null;
  complaint_reason?: string | null;
  complained_at?: string | null;
  settlement_amount: MoneyLike;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CleaningProof {
  id: string;
  tenant_id: string;
  task_id: string;
  uploaded_by: string;
  image_urls: string[];
  remark?: string | null;
  created_at?: string | null;
}

export interface CleaningSummary {
  pending_count: number;
  overdue_count: number;
  in_progress_count: number;
  complained_count: number;
  overdue_task_ids: string[];
}

// Platform types

export interface TenantInfo {
  id: string;
  name: string;
  status: string;
  plan?: string | null;
  settings: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface TenantApp {
  id: string;
  tenant_id: string;
  client_type: string;
  app_id: string;
  mch_id?: string | null;
  secret_ref?: string | null;
  status: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface UserInfo {
  id: string;
  tenant_id?: string | null;
  phone?: string | null;
  nickname?: string | null;
  status: string;
  roles: string[];
  store_ids: string[];
  created_at?: string | null;
}

export interface RoleInfo {
  id: string;
  name: string;
  label: string;
  description?: string | null;
}

export interface DeviceInfo {
  id: string;
  tenant_id: string;
  store_id: string;
  room_id?: string | null;
  name: string;
  device_type: string;
  provider: string;
  external_id: string;
  status: string;
  capabilities: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface DeviceCommandInfo {
  id: string;
  tenant_id: string;
  device_id: string;
  actor_id?: string | null;
  command: string;
  biz_type: string;
  biz_id: string;
  status: string;
  idempotency_key?: string | null;
  request_payload: Record<string, unknown>;
  response_payload: Record<string, unknown>;
  failure_reason?: string | null;
  retry_count: number;
  executed_at?: string | null;
  created_at?: string | null;
}
