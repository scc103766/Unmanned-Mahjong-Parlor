<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { ApiError, merchantApi } from "@/core/api/client";
import { demoAuditLogs, demoExceptions } from "@/core/api/demo";
import type { AuditLog, OperationException } from "@/core/api/types";
import {
  formatDateTime,
  severityLabel,
  sourceLabel,
  statusLabel,
  statusTone,
} from "@/shared/utils/format";

const session = useSessionStore();
const loading = ref(false);
const error = ref("");
const sourceFilter = ref("");
const exceptions = ref<OperationException[]>(demoExceptions);
const auditLogs = ref<AuditLog[]>(demoAuditLogs);

const filteredDemoExceptions = computed(() =>
  demoExceptions.filter((item) => !sourceFilter.value || item.source === sourceFilter.value),
);

async function load() {
  error.value = "";
  if (!session.isConnected) {
    exceptions.value = filteredDemoExceptions.value;
    auditLogs.value = demoAuditLogs;
    return;
  }
  loading.value = true;
  try {
    const [exceptionList, auditList] = await Promise.all([
      merchantApi.exceptions(sourceFilter.value ? { source: sourceFilter.value } : undefined),
      merchantApi.auditLogs({ limit: 100 }),
    ]);
    exceptions.value = exceptionList.exceptions;
    auditLogs.value = auditList.logs;
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "异常审计加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void load();
});
</script>

<template>
  <section class="page-stack">
    <div class="page-actions">
      <label>
        来源
        <select v-model="sourceFilter" @change="load">
          <option value="">全部</option>
          <option value="payment">支付</option>
          <option value="refund">退款</option>
          <option value="withdrawal">提现</option>
          <option value="device">设备</option>
          <option value="cleaning">保洁</option>
        </select>
      </label>
      <button type="button" :disabled="loading" @click="load">{{ loading ? "刷新中" : "刷新" }}</button>
    </div>

    <p v-if="error" class="alert">{{ error }}</p>

    <section class="content-grid two-columns">
      <article class="panel span-2">
        <div class="panel-head">
          <h2>异常列表</h2>
          <span class="muted">{{ exceptions.length }} 条</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>来源</th>
                <th>级别</th>
                <th>对象</th>
                <th>消息</th>
                <th>状态</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in exceptions" :key="item.id">
                <td>{{ sourceLabel(item.source) }}</td>
                <td>{{ severityLabel(item.severity) }}</td>
                <td>{{ item.entity_type }} / {{ item.entity_id }}</td>
                <td>{{ item.message }}</td>
                <td><span class="badge" :class="statusTone(item.status)">{{ statusLabel(item.status) }}</span></td>
                <td>{{ formatDateTime(item.occurred_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="panel">
        <div class="panel-head">
          <h2>审计日志</h2>
          <span class="muted">{{ auditLogs.length }} 条</span>
        </div>
        <div class="audit-list">
          <div v-for="item in auditLogs" :key="item.id" class="audit-item">
            <strong>{{ item.action }}</strong>
            <span>{{ item.target_type }} / {{ item.target_id || "-" }}</span>
            <small>{{ item.actor_id || "-" }} / {{ formatDateTime(item.created_at) }}</small>
          </div>
        </div>
      </article>
    </section>
  </section>
</template>
