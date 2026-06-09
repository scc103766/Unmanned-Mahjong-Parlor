<script setup lang="ts">
import { onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { platformApi, ApiError } from "@/core/api/platform";
import { demoDevices } from "@/core/api/demo";
import type { DeviceInfo } from "@/core/api/types";

const session = useSessionStore();
const devices = ref<DeviceInfo[]>(demoDevices);
const loading = ref(false);
const error = ref("");
const actionMsg = ref("");
const testingId = ref<string | null>(null);

const deviceTypeLabels: Record<string, string> = {
  store_door: "大门",
  room_door: "房门",
  room_lock: "智能锁",
  power: "电源",
  speaker: "云喇叭",
};

async function load() {
  if (!session.isConnected) return;
  loading.value = true;
  error.value = "";
  try {
    const data = await platformApi.listDevices();
    if (data.length > 0) devices.value = data;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

async function doTest(device: DeviceInfo) {
  testingId.value = device.id;
  actionMsg.value = "";
  try {
    const result = await platformApi.testDevice(device.id);
    actionMsg.value = (result as { message?: string }).message ?? "测试完成";
  } catch (e) {
    actionMsg.value = e instanceof ApiError ? e.message : "测试失败";
  } finally {
    testingId.value = null;
  }
}

onMounted(load);
</script>

<template>
  <div class="page-stack">
    <div class="page-actions">
      <h2>设备列表 ({{ devices.length }})</h2>
    </div>

    <div v-if="loading" class="muted" style="text-align:center;padding:20px">加载中...</div>
    <div v-else-if="error" class="alert">{{ error }}</div>
    <div v-if="actionMsg" :class="actionMsg.includes('失败') ? 'alert' : 'notice-line'">
      {{ actionMsg }}
    </div>

    <table v-if="devices.length > 0">
      <thead>
        <tr>
          <th>名称</th><th>类型</th><th>供应商</th><th>租户</th><th>状态</th><th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="d in devices" :key="d.id">
          <td>
            <strong>{{ d.name }}</strong>
            <small>{{ d.external_id }}</small>
          </td>
          <td><span class="chip">{{ deviceTypeLabels[d.device_type] ?? d.device_type }}</span></td>
          <td>{{ d.provider }}</td>
          <td><small>{{ d.tenant_id?.slice(0, 8) ?? '—' }}</small></td>
          <td><span :class="['badge', d.status==='active'?'good':'neutral']">{{ d.status }}</span></td>
          <td>
            <button
              class="mini secondary"
              :disabled="testingId === d.id"
              @click="doTest(d)"
            >
              {{ testingId === d.id ? "测试中" : "测试" }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
