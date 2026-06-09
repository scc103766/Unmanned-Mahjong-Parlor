<script setup lang="ts">
import { onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { platformApi, ApiError } from "@/core/api/platform";
import { demoExceptions } from "@/core/api/demo";
import type { OperationException } from "@/core/api/types";
import { severityLabel, sourceLabel } from "@/shared/utils/format";

const session = useSessionStore();
const exceptions = ref<OperationException[]>(demoExceptions);
const loading = ref(false);
const error = ref("");
const sourceFilter = ref("");

async function load() {
  if (!session.isConnected) return;
  loading.value = true;
  error.value = "";
  try {
    const params: Record<string, unknown> = {};
    if (sourceFilter.value) params.source = sourceFilter.value;
    const result = await platformApi.listExceptions(params);
    if (result.exceptions.length > 0) exceptions.value = result.exceptions;
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
      <h2>异常列表 ({{ exceptions.length }})</h2>
      <div class="inline-controls">
        <select v-model="sourceFilter" @change="load()">
          <option value="">全部来源</option>
          <option value="payment">支付</option>
          <option value="refund">退款</option>
          <option value="withdrawal">提现</option>
          <option value="device">设备</option>
          <option value="cleaning">保洁</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="muted" style="text-align:center;padding:20px">加载中...</div>
    <div v-else-if="error" class="alert">{{ error }}</div>

    <table v-if="exceptions.length > 0">
      <thead>
        <tr>
          <th>级别</th><th>来源</th><th>消息</th><th>时间</th><th>租户</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ex in exceptions" :key="ex.id">
          <td><span :class="['badge', ex.severity==='high'||ex.severity==='critical'?'bad':'warn']">{{ severityLabel(ex.severity) }}</span></td>
          <td><span class="chip">{{ sourceLabel(ex.source) }}</span></td>
          <td style="max-width:300px;white-space:normal">{{ ex.message }}</td>
          <td><small>{{ new Date(ex.occurred_at).toLocaleString("zh-CN") }}</small></td>
          <td><small>{{ ex.tenant_id?.slice(0, 8) ?? '—' }}</small></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
