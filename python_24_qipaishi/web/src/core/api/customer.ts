import { apiGet, apiPost } from "@/core/api/client";
import { useSessionStore } from "@/app/stores/session";
import type {
  StoreSummary,
  RoomSummary,
  RoomDetail,
  RoomAvailability,
  PriceQuote,
  PreorderResult,
  OrderSummary,
  PaymentResult,
  WalletAccount,
  CouponInfo,
} from "@/core/api/types";

function withTenant(params: Record<string, unknown> = {}): Record<string, unknown> {
  const session = useSessionStore();
  return session.tenantId ? { tenant_id: session.tenantId, ...params } : params;
}

export const customerApi = {
  // Stores
  listStores() {
    return apiGet<StoreSummary[]>("/api/v1/stores", withTenant());
  },
  getStore(id: string) {
    return apiGet<StoreSummary>(`/api/v1/stores/${id}`);
  },

  // Rooms
  listRooms(storeId: string) {
    return apiGet<RoomSummary[]>("/api/v1/rooms", withTenant({ store_id: storeId }));
  },
  getRoomDetail(id: string) {
    return apiGet<RoomDetail>(`/api/v1/rooms/${id}`);
  },

  // Availability
  getRoomAvailability(roomId: string, startAt: string, endAt: string) {
    return apiGet<RoomAvailability[]>("/api/v1/availability/rooms", {
      ...withTenant(),
      room_id: roomId,
      start_at: startAt,
      end_at: endAt,
    });
  },

  // Pricing
  quotePrice(roomId: string, startAt: string, endAt: string) {
    return apiPost<PriceQuote>("/api/v1/pricing/quote", {
      room_id: roomId,
      start_at: startAt,
      end_at: endAt,
    });
  },

  // Orders
  createPreorder(roomId: string, startAt: string, endAt: string) {
    return apiPost<PreorderResult>("/api/v1/orders/preorder", {
      room_id: roomId,
      start_at: startAt,
      end_at: endAt,
    });
  },
  createOrder(roomId: string, startAt: string, endAt: string) {
    return apiPost<OrderSummary>("/api/v1/orders", {
      room_id: roomId,
      start_at: startAt,
      end_at: endAt,
    });
  },
  getOrder(id: string) {
    return apiGet<OrderSummary>(`/api/v1/orders/${id}`);
  },
  listMyOrders() {
    return apiGet<OrderSummary[]>("/api/v1/orders", withTenant());
  },

  // Payments
  wechatPrepay(orderId: string) {
    return apiPost<PaymentResult>("/api/v1/payments/wechat/prepay", {
      order_id: orderId,
    });
  },
  mockPayCallback(paymentId: string) {
    return apiPost<PaymentResult>("/api/v1/payments/wechat/callback", {
      payment_id: paymentId,
      transaction_id: `txn_${Date.now()}`,
      provider_event_id: `evt_${Date.now()}`,
    });
  },

  // Device / door control
  openStoreDoor(orderId: string) {
    return apiPost<{ status: string; message: string }>(
      `/api/v1/orders/${orderId}/open-store-door`,
    );
  },
  openRoomDoor(orderId: string) {
    return apiPost<{ status: string; message: string }>(
      `/api/v1/orders/${orderId}/open-room-door`,
    );
  },

  // Wallet
  getMyWallet() {
    return apiGet<WalletAccount>("/api/v1/wallets/me", withTenant());
  },

  // Coupons
  getMyCoupons() {
    return apiGet<CouponInfo[]>("/api/v1/coupons", withTenant());
  },
};
