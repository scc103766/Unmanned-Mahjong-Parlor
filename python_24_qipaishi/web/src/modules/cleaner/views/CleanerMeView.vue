<script setup lang="ts">
import { onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { ApiError } from "@/core/api/client";
import { cleanerApi } from "@/core/api/cleaner";
import { demoCleaningSummary } from "@/core/api/demo";
import type { CleaningSummary } from "@/core/api/types";

const session = useSessionStore();
const summary = ref<CleaningSummary>(demoCleaningSummary);
const loading = ref(false);

const statCards = computed(() => [
  { label: "待接单", value: summary.value.pending_count, tone: "warn" },
  { label: "进行中", value: summary.value.in_progress_count, tone: "good" },
  { label: "已逾期", value: summary.value.overdue_count, tone: "bad" },
  { label: "被投诉", value: summary.value.complained_count, tone: "bad" },
]);

async function load() {
  if (!session.isConnected) return;
  loading.value = true;
  try {
    summary.value = await cleanerApi.getSummary();
  } catch (e) {
    if (e instanceof ApiError) {
      // keep demo data
    }
  } finally {
    loading.value = false;
  }
}

function handleLogout() {
  session.clearToken();
  summary.value = demoCleaningSummary;
}

import { computed } from "vue";

onMounted(load);
</script>

<template>
  <div class="page-stack">
    <div class="panel" style="min-height:auto">
      <div v-if="session.isConnected">
        <h3 style="margin-bottom:6px">{{ session.displayName }}</h3>
        <small class="muted">已登录 · 保洁员</small>
      </div>
      <div v-else>
        <h3 style="margin-bottom:6px;color:var(--muted)">未登录</h3>
        <small class="muted">点击顶部"一键登录"按钮连接服务</small>
      </div>
    </div>

    <div class="panel" style="min-height:auto">
      <h3 style="margin-bottom:10px">任务统计</h3>
      <div class="compact-stats">
        <div v-for="card in statCards" :key="card.label">
          <span>{{ card.label }}</span>
          <strong :style="{ color: card.tone === 'bad' ? 'var(--bad)' : card.tone === 'warn' ? 'var(--warn)' : 'var(--good)' }">
            {{ card.value }}
          </strong>
        </div>
      </div>
    </div>

    <div v-if="session.isConnected" class="button-row">
      <button class="ghost" style="width:100%;height:44px" @click="handleLogout">
        退出登录
      </button>
    </div>
  </div>
</template>

<style scoped>
.compact-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.compact-stats div {
  display: grid;
  gap: 4px;
  min-height: 72px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
  background: var(--panel-soft);
}

.compact-stats span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.compact-stats strong {
  font-size: 24px;
}
</style>
