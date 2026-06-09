<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { ApiError } from "@/core/api/client";
import { cleanerApi } from "@/core/api/cleaner";
import { demoCleaningTasks } from "@/core/api/demo";
import type { CleaningTask } from "@/core/api/types";
import { formatMoney, statusLabel, statusTone } from "@/shared/utils/format";

const session = useSessionStore();
const tasks = ref<CleaningTask[]>(demoCleaningTasks);
const loading = ref(false);
const error = ref("");
const activeFilter = ref("all");

const filters = [
  { key: "all", label: "全部" },
  { key: "pending", label: "待接单" },
  { key: "accepted", label: "已接单" },
  { key: "in_progress", label: "进行中" },
  { key: "completed", label: "已完成" },
];

const filteredTasks = computed(() => {
  if (activeFilter.value === "all") return tasks.value;
  return tasks.value.filter((t) => t.status === activeFilter.value);
});

function roomLabel(task: CleaningTask): string {
  return `房间 ${task.room_id?.slice(0, 8) ?? "—"}`;
}

async function load() {
  if (!session.isConnected) return;
  loading.value = true;
  error.value = "";
  try {
    const data = await cleanerApi.listTasks();
    if (data.length > 0) tasks.value = data;
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
    <!-- Filter tabs -->
    <div class="filter-tabs">
      <button
        v-for="f in filters"
        :key="f.key"
        :class="['mini', activeFilter === f.key ? '' : 'ghost']"
        @click="activeFilter = f.key"
      >
        {{ f.label }}
      </button>
    </div>

    <div v-if="loading" class="muted" style="text-align:center;padding:20px">加载中...</div>
    <div v-else-if="error" class="alert">{{ error }}</div>
    <div v-else-if="filteredTasks.length === 0" class="muted" style="text-align:center;padding:30px">
      暂无任务
    </div>

    <RouterLink
      v-for="task in filteredTasks"
      :key="task.id"
      :to="{ name: 'cleaner-task-detail', params: { taskId: task.id } }"
      class="order-card"
    >
      <div class="order-card-head">
        <strong>{{ roomLabel(task) }}</strong>
        <span :class="['badge', statusTone(task.status)]">{{ statusLabel(task.status) }}</span>
      </div>
      <small v-if="task.scheduled_start_at" class="muted">
        ⏰ {{ new Date(task.scheduled_start_at).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }) }}
      </small>
      <div class="order-card-foot">
        <strong style="color:var(--good)">¥{{ task.settlement_amount }}</strong>
        <small class="muted">门店 {{ task.store_id?.slice(0, 8) ?? "—" }}</small>
      </div>
    </RouterLink>
  </div>
</template>

<style scoped>
.filter-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.filter-tabs button {
  flex-shrink: 0;
}

.order-card {
  display: grid;
  gap: 4px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 14px;
  text-decoration: none;
  color: inherit;
}

.order-card:active {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.order-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.order-card-head strong {
  font-size: 15px;
}

.order-card-head .badge {
  font-size: 11px;
  flex-shrink: 0;
}

.order-card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 2px;
}
</style>
