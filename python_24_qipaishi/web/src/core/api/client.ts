import axios, { AxiosError, type AxiosRequestConfig } from "axios";

import { useSessionStore } from "@/app/stores/session";
import type {
  ApiEnvelope,
  AuditLogList,
  CleaningAnalytics,
  DevBootstrapRequest,
  ManualCompensationRequest,
  ManualCompensationResponse,
  MemberList,
  MerchantDashboard,
  OperationExceptionList,
  OrderRescheduleQuote,
  OrderSummary,
  Principal,
  QueryRange,
  RoomUsageList,
  TokenResponse,
  Withdrawal,
} from "@/core/api/types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
    readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const http = axios.create({
  timeout: 12_000,
});

http.interceptors.request.use((config) => {
  const session = useSessionStore();
  config.baseURL = session.apiBase;
  if (session.token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${session.token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ message?: string; code?: string }>) => {
    const status = error.response?.status;
    const message = error.response?.data?.message ?? error.message;
    const code = error.response?.data?.code;
    return Promise.reject(new ApiError(message, status, code));
  },
);

function unwrap<T>(payload: ApiEnvelope<T>): T {
  if (payload.code !== 0) {
    throw new ApiError(payload.message, undefined, String(payload.code));
  }
  return payload.data;
}

export async function apiGet<T>(url: string, params?: object): Promise<T> {
  const response = await http.get<ApiEnvelope<T>>(url, { params });
  return unwrap(response.data);
}

export async function apiPost<T, B = unknown>(
  url: string,
  body?: B,
  config?: AxiosRequestConfig,
): Promise<T> {
  const response = await http.post<ApiEnvelope<T>>(url, body, config);
  return unwrap(response.data);
}

function withTenant(params: QueryRange = {}): QueryRange {
  const session = useSessionStore();
  return session.tenantId ? { tenant_id: session.tenantId, ...params } : params;
}

export const merchantApi = {
  devBootstrap(payload: DevBootstrapRequest) {
    return apiPost<TokenResponse, DevBootstrapRequest>("/api/v1/auth/dev-bootstrap", payload);
  },
  currentUser() {
    return apiGet<Principal>("/api/v1/auth/me");
  },
  dashboard(params?: QueryRange) {
    return apiGet<MerchantDashboard>("/api/v1/analytics/dashboard", withTenant(params));
  },
  roomUsage(params?: QueryRange) {
    return apiGet<RoomUsageList>("/api/v1/analytics/rooms/usage", withTenant(params));
  },
  cleaning(params?: QueryRange) {
    return apiGet<CleaningAnalytics>("/api/v1/analytics/cleaning", withTenant(params));
  },
  exceptions(params?: QueryRange & { source?: string }) {
    return apiGet<OperationExceptionList>("/api/v1/operations/exceptions", withTenant(params));
  },
  auditLogs(params?: QueryRange & { action?: string; target_type?: string }) {
    return apiGet<AuditLogList>("/api/v1/operations/audit-logs", withTenant(params));
  },
  withdrawals(params?: { status?: string; user_id?: string }) {
    return apiGet<Withdrawal[]>("/api/v1/withdrawals", params);
  },
  approveWithdrawal(id: string, note?: string) {
    return apiPost<Withdrawal, { note?: string }>(`/api/v1/withdrawals/${id}/approve`, { note });
  },
  rejectWithdrawal(id: string, reason: string) {
    return apiPost<Withdrawal, { reason: string }>(`/api/v1/withdrawals/${id}/reject`, { reason });
  },
  markWithdrawalPaid(id: string, payoutRef: string, note?: string) {
    return apiPost<Withdrawal, { payout_ref: string; note?: string }>(
      `/api/v1/withdrawals/${id}/mark-paid`,
      { payout_ref: payoutRef, note },
    );
  },
  members(limit = 100) {
    return apiGet<MemberList>("/api/v1/members", { limit });
  },
  compensate(payload: ManualCompensationRequest) {
    const session = useSessionStore();
    return apiPost<ManualCompensationResponse, ManualCompensationRequest>(
      "/api/v1/operations/compensations",
      {
        ...payload,
        tenant_id: payload.tenant_id || session.tenantId || null,
      },
    );
  },
  orders() {
    return apiGet<OrderSummary[]>("/api/v1/orders");
  },
  quoteReschedule(orderId: string, startAt: string, endAt: string) {
    return apiPost<OrderRescheduleQuote, { start_at: string; end_at: string }>(
      `/api/v1/orders/${orderId}/reschedule/quote`,
      { start_at: startAt, end_at: endAt },
    );
  },
  rescheduleOrder(orderId: string, startAt: string, endAt: string) {
    return apiPost<OrderSummary, { start_at: string; end_at: string }>(
      `/api/v1/orders/${orderId}/reschedule`,
      { start_at: startAt, end_at: endAt },
    );
  },
};
