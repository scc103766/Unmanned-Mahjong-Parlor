<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { useSessionStore } from "@/app/stores/session";
import { ApiError } from "@/core/api/client";
import { cleanerApi } from "@/core/api/cleaner";
import { demoCleaningTasks } from "@/core/api/demo";
import type { CleaningTask } from "@/core/api/types";
import { formatMoney, statusLabel, statusTone } from "@/shared/utils/format";

const route = useRoute();
const session = useSessionStore();
const taskId = computed(() => route.params.taskId as string);

const task = ref<CleaningTask | null>(null);
const loading = ref(false);
const error = ref("");
const actionLoading = ref(false);
const actionMsg = ref("");

const imageUrlInput = ref("");
const remarkInput = ref("");
const showCompleteForm = ref(false);

const statusBadge = computed(() => ({
  text: statusLabel(task.value?.status ?? ""),
  tone: statusTone(task.value?.status ?? ""),
}));

const canAccept = computed(() => task.value?.status === "pending");
const canUnaccept = computed(() => task.value?.status === "accepted");
const canStart = computed(() => task.value?.status === "accepted");
const canOpenDoor = computed(() => task.value?.status === "in_progress");
const canComplete = computed(() => task.value?.status === "in_progress");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    if (session.isConnected) {
      const tasks = await cleanerApi.listTasks();
      task.value = tasks.find((t) => t.id === taskId.value) ?? null;
    } else {
      task.value = demoCleaningTasks.find((t) => t.id === taskId.value) ?? demoCleaningTasks[0] ?? null;
    }
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

async function doAction(action: string) {
  actionLoading.value = true;
  actionMsg.value = "";
  try {
    switch (action) {
      case "accept":
        task.value = await cleanerApi.acceptTask(taskId.value);
        actionMsg.value = "已接单";
        break;
      case "unaccept":
        task.value = await cleanerApi.unacceptTask(taskId.value);
        actionMsg.value = "已取消接单";
        break;
      case "start":
        task.value = await cleanerApi.startTask(taskId.value);
        actionMsg.value = "任务已开始";
        break;
      case "open-door": {
        const result = await cleanerApi.openTaskDoor(taskId.value);
        actionMsg.value = (result as { message?: string }).message ?? "门已开启";
        break;
      }
      case "complete": {
        const urls = imageUrlInput.value
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
        if (urls.length === 0) {
          actionMsg.value = "请至少输入一张图片URL";
          actionLoading.value = false;
          return;
        }
        task.value = await cleanerApi.completeTask(taskId.value, urls, remarkInput.value);
        actionMsg.value = "任务已完成";
        showCompleteForm.value = false;
        break;
      }
    }
    if (action !== "complete") await load();
  } catch (e) {
    actionMsg.value = e instanceof ApiError ? e.message : "操作失败";
  } finally {
    actionLoading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="page-stack">
    <div v-if="loading" class="muted" style="text-align:center;padding:20px">加载中...</div>
    <div v-else-if="error" class="alert">{{ error }}</div>
    <template v-else-if="task">
      <!-- Status & amount -->
      <div class="panel" style="min-height:auto">
        <div class="order-status">
          <span :class="['badge', statusBadge.tone]">{{ statusBadge.text }}</span>
          <strong style="font-size:22px;color:var(--good)">{{ formatMoney(task.settlement_amount) }}</strong>
        </div>
        <dl class="detail-list" style="margin-top:10px">
          <dt>房间ID</dt><dd>{{ task.room_id }}</dd>
          <dt>门店ID</dt><dd>{{ task.store_id }}</dd>
          <dt>订单ID</dt><dd>{{ task.order_id }}</dd>
          <dt v-if="task.scheduled_start_at">计划时间</dt>
          <dd v-if="task.scheduled_start_at">
            {{ new Date(task.scheduled_start_at).toLocaleString("zh-CN") }}
            <span v-if="task.scheduled_end_at">
              — {{ new Date(task.scheduled_end_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }) }}
            </span>
          </dd>
        </dl>
        <!-- Timeline -->
        <div class="timeline" style="margin-top:10px">
          <div v-if="task.accepted_at" class="timeline-item">
            <small class="muted">接单</small>
            <span>{{ new Date(task.accepted_at).toLocaleString("zh-CN") }}</span>
          </div>
          <div v-if="task.started_at" class="timeline-item">
            <small class="muted">开始</small>
            <span>{{ new Date(task.started_at).toLocaleString("zh-CN") }}</span>
          </div>
          <div v-if="task.completed_at" class="timeline-item" style="border-left-color:var(--good)">
            <small class="muted">完成</small>
            <span>{{ new Date(task.completed_at).toLocaleString("zh-CN") }}</span>
          </div>
        </div>
      </div>

      <!-- Action feedback -->
      <div v-if="actionMsg" :class="actionMsg.includes('失败') || actionMsg.includes('请') ? 'alert' : 'notice-line'">
        {{ actionMsg }}
      </div>

      <!-- Complete form -->
      <div v-if="showCompleteForm" class="panel" style="min-height:auto">
        <h3 style="margin-bottom:8px">上传清洁凭证</h3>
        <label>
          图片URL（多个用逗号分隔）
          <input v-model="imageUrlInput" placeholder="https://img.example.com/1.jpg, https://..." />
        </label>
        <label style="margin-top:8px">
          备注
          <input v-model="remarkInput" placeholder="清洁完成情况..." />
        </label>
        <div class="button-row" style="margin-top:10px">
          <button :disabled="actionLoading" @click="doAction('complete')">
            {{ actionLoading ? "提交中..." : "提交完成" }}
          </button>
          <button class="ghost" @click="showCompleteForm = false">取消</button>
        </div>
      </div>

      <!-- Actions -->
      <div class="order-actions">
        <button
          v-if="canAccept"
          style="height:46px;font-size:15px"
          :disabled="actionLoading"
          @click="doAction('accept')"
        >
          🙋 接单
        </button>
        <button
          v-if="canUnaccept"
          class="ghost"
          style="height:46px;font-size:15px"
          :disabled="actionLoading"
          @click="doAction('unaccept')"
        >
          取消接单
        </button>
        <button
          v-if="canStart"
          style="height:46px;font-size:15px"
          :disabled="actionLoading"
          @click="doAction('start')"
        >
          ▶️ 开始任务
        </button>
        <button
          v-if="canOpenDoor"
          class="secondary"
          style="height:46px;font-size:15px"
          :disabled="actionLoading"
          @click="doAction('open-door')"
        >
          🔑 保洁开门
        </button>
        <button
          v-if="canComplete && !showCompleteForm"
          style="height:46px;font-size:15px"
          :disabled="actionLoading"
          @click="showCompleteForm = true"
        >
          ✅ 完成任务
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.order-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
}

.order-actions {
  display: grid;
  gap: 8px;
}

.timeline {
  display: grid;
  gap: 6px;
}

.timeline-item {
  display: grid;
  gap: 1px;
  border-left: 3px solid var(--brand);
  padding-left: 10px;
}

.timeline-item span {
  font-size: 14px;
}
</style>
