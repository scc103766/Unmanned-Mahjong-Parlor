<script setup lang="ts">
import { onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { platformApi, ApiError } from "@/core/api/platform";
import { demoAuditLogs } from "@/core/api/demo";
import type { AuditLog } from "@/core/api/types";

const session = useSessionStore();
const logs = ref<AuditLog[]>(demoAuditLogs);
const loading = ref(false);
const error = ref("");

async function load() {
  if (!session.isConnected) return;
  loading.value = true;
  error.value = "";
  try {
    const result = await platformApi.listAuditLogs();
    if (result.logs.length > 0) logs.value = result.logs;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="page-stack">
    <div class="page-actions">
      <h2>审计日志 ({{ logs.length }})</h2>
    </div>

    <div v-if="loading" class="muted" style="text-align:center;padding:20px">加载中...</div>
    <div v-else-if="error" class="alert">{{ error }}</div>

    <table v-if="logs.length > 0">
      <thead>
        <tr>
          <th>操作</th><th>目标</th><th>操作者</th><th>时间</th><th>租户</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id">
          <td><span class="chip">{{ log.action }}</span></td>
          <td>
            {{ log.target_type }}
            <small v-if="log.target_id">{{ log.target_id?.slice(0, 8) }}...</small>
          </td>
          <td><small>{{ log.actor_id?.slice(0, 8) ?? '—' }}</small></td>
          <td><small>{{ new Date(log.created_at).toLocaleString("zh-CN") }}</small></td>
          <td><small>{{ log.tenant_id?.slice(0, 8) ?? '—' }}</small></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
