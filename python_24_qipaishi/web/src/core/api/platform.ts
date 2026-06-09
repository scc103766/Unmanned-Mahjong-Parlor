import { apiGet, apiPost, ApiError } from "@/core/api/client";
import type {
  TenantInfo,
  TenantApp,
  UserInfo,
  RoleInfo,
  DeviceInfo,
  OperationException,
  OperationExceptionList,
  AuditLog,
  AuditLogList,
} from "@/core/api/types";

export { ApiError } from "@/core/api/client";

export const platformApi = {
  // Tenants
  listTenants() {
    return apiGet<TenantInfo[]>("/api/v1/tenants");
  },
  createTenant(name: string, plan?: string) {
    return apiPost<TenantInfo, { name: string; plan?: string }>("/api/v1/tenants", {
      name,
      plan: plan ?? "standard",
    });
  },
  getTenant(id: string) {
    return apiGet<TenantInfo>(`/api/v1/tenants/${id}`);
  },
  listTenantApps(tenantId: string) {
    return apiGet<TenantApp[]>(`/api/v1/tenants/${tenantId}/apps`);
  },
  createTenantApp(tenantId: string, clientType: string, appId: string) {
    return apiPost<TenantApp, { client_type: string; app_id: string }>(
      `/api/v1/tenants/${tenantId}/apps`,
      { client_type: clientType, app_id: appId },
    );
  },

  // Users & Roles
  listUsers() {
    return apiGet<UserInfo[]>("/api/v1/users");
  },
  listRoles() {
    return apiGet<RoleInfo[]>("/api/v1/roles");
  },
  assignRoles(userId: string, roleNames: string[]) {
    return apiPost<UserInfo, { role_names: string[] }>(`/api/v1/users/${userId}/roles`, {
      role_names: roleNames,
    });
  },
  assignStoreScopes(userId: string, storeIds: string[]) {
    return apiPost<UserInfo, { store_ids: string[] }>(
      `/api/v1/users/${userId}/store-scopes`,
      { store_ids: storeIds },
    );
  },

  // Devices
  listDevices() {
    return apiGet<DeviceInfo[]>("/api/v1/devices");
  },
  createDevice(body: Record<string, unknown>) {
    return apiPost<DeviceInfo>("/api/v1/devices", body);
  },
  testDevice(deviceId: string) {
    return apiPost<{ status: string; message: string }>(
      `/api/v1/devices/${deviceId}/test`,
    );
  },

  // Exceptions & Audit (cross-tenant)
  listExceptions(params?: Record<string, unknown>) {
    return apiGet<OperationExceptionList>("/api/v1/operations/exceptions", params);
  },
  listAuditLogs(params?: Record<string, unknown>) {
    return apiGet<AuditLogList>("/api/v1/operations/audit-logs", params);
  },
};
