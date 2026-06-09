<script setup lang="ts">
import { onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { platformApi, ApiError } from "@/core/api/platform";
import { demoTenants } from "@/core/api/demo";
import type { TenantInfo } from "@/core/api/types";

const session = useSessionStore();
const tenants = ref<TenantInfo[]>(demoTenants);
const loading = ref(false);
const error = ref("");
const showCreate = ref(false);
const newName = ref("");
const newPlan = ref("standard");
const creating = ref(false);

async function load() {
  if (!session.isConnected) return;
  loading.value = true;
  error.value = "";
  try {
    const data = await platformApi.listTenants();
    if (data.length > 0) tenants.value = data;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

async function doCreate() {
  if (!newName.value.trim()) return;
  creating.value = true;
  error.value = "";
  try {
    await platformApi.createTenant(newName.value.trim(), newPlan.value);
    showCreate.value = false;
    newName.value = "";
    await load();
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "创建失败";
  } finally {
    creating.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="page-stack">
    <div class="page-actions">
      <h2>租户列表 ({{ tenants.length }})</h2>
      <button @click="showCreate = !showCreate">
        {{ showCreate ? "取消" : "创建租户" }}
      </button>
    </div>

    <div v-if="showCreate" class="panel" style="min-height:auto">
      <label>
        租户名称
        <input v-model="newName" placeholder="输入租户名称..." />
      </label>
      <label style="margin-top:8px">
        套餐
        <select v-model="newPlan">
          <option value="basic">基础版</option>
          <option value="standard">标准版</option>
          <option value="premium">高级版</option>
        </select>
      </label>
      <button style="margin-top:10px" :disabled="creating || !newName.trim()" @click="doCreate">
        {{ creating ? "创建中..." : "确认创建" }}
      </button>
    </div>

    <div v-if="loading" class="muted" style="text-align:center;padding:20px">加载中...</div>
    <div v-else-if="error" class="alert">{{ error }}</div>

    <div v-for="t in tenants" :key="t.id" class="panel" style="min-height:auto">
      <div class="detail-list" style="grid-template-columns:120px minmax(0,1fr)">
        <dt>名称</dt><dd><strong>{{ t.name }}</strong></dd>
        <dt>状态</dt><dd><span :class="['badge', t.status==='active'?'good':'neutral']">{{ t.status === 'active' ? '运营中' : t.status }}</span></dd>
        <dt>套餐</dt><dd>{{ t.plan ?? '—' }}</dd>
        <dt>ID</dt><dd><small>{{ t.id }}</small></dd>
      </div>
      <div style="margin-top:8px">
        <RouterLink
          :to="{ name: 'platform-tenant-detail', params: { tenantId: t.id } }"
          class="text-link"
        >
          查看应用 →
        </RouterLink>
      </div>
    </div>
  </div>
</template>
