import { apiGet, apiPost } from "@/core/api/client";
import { useSessionStore } from "@/app/stores/session";
import type { CleaningTask, CleaningSummary } from "@/core/api/types";

function withTenant(params: Record<string, unknown> = {}): Record<string, unknown> {
  const session = useSessionStore();
  return session.tenantId ? { tenant_id: session.tenantId, ...params } : params;
}

export const cleanerApi = {
  listTasks(params?: { status?: string }) {
    return apiGet<CleaningTask[]>("/api/v1/cleaning/tasks", {
      ...withTenant(),
      ...params,
    });
  },

  getSummary() {
    return apiGet<CleaningSummary>("/api/v1/cleaning/summary", withTenant());
  },

  acceptTask(taskId: string) {
    return apiPost<CleaningTask>(`/api/v1/cleaning/tasks/${taskId}/accept`);
  },

  unacceptTask(taskId: string) {
    return apiPost<CleaningTask>(`/api/v1/cleaning/tasks/${taskId}/unaccept`);
  },

  startTask(taskId: string) {
    return apiPost<CleaningTask>(`/api/v1/cleaning/tasks/${taskId}/start`);
  },

  openTaskDoor(taskId: string) {
    return apiPost<{ status: string; message: string }>(
      `/api/v1/cleaning/tasks/${taskId}/open-door`,
    );
  },

  completeTask(taskId: string, imageUrls: string[], remark?: string) {
    return apiPost<CleaningTask>(`/api/v1/cleaning/tasks/${taskId}/complete`, {
      image_urls: imageUrls,
      remark: remark ?? "",
    });
  },
};
