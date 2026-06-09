<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { useSessionStore } from "@/app/stores/session";
import { platformApi, ApiError } from "@/core/api/platform";
import { demoTenants, demoTenantApps } from "@/core/api/demo";
import type { TenantInfo, TenantApp } from "@/core/api/types";

const route = useRoute();
const session = useSessionStore();
const tenantId = computed(() => route.params.tenantId as string);

const tenant = ref<TenantInfo | null>(null);
const apps = ref<TenantApp[]>(demoTenantApps);
const loading = ref(false);
const error = ref("");
const showCreateApp = ref(false);
const newClientType = ref("h5");
const newAppId = ref("");
const creatingApp = ref(false);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    if (session.isConnected) {
      const [t, a] = await Promise.all([
        platformApi.getTenant(tenantId.value),
        platformApi.listTenantApps(tenantId.value),
      ]);
      tenant.value = t;
      if (a.length > 0) apps.value = a;
    } else {
      tenant.value = demoTenants.find((t) => t.id === tenantId.value) ?? demoTenants[0];
    }
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

async function doCreateApp() {
  if (!newAppId.value.trim()) return;
  creatingApp.value = true;
  error.value = "";
  try {
    await platformApi.createTenantApp(tenantId.value, newClientType.value, newAppId.value.trim());
    showCreateApp.value = false;
    newAppId.value = "";
    await load();
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "创建失败";
  } finally {
    creatingApp.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="page-stack">
    <div v-if="loading" class="muted" style="text-align:center;padding:20px">加载中...</div>
    <div v-else-if="error" class="alert">{{ error }}</div>
    <template v-else-if="tenant">
      <div class="panel" style="min-height:auto">
        <h3 style="margin-bottom:10px">{{ tenant.name }}</h3>
        <dl class="detail-list" style="grid-template-columns:100px minmax(0,1fr)">
          <dt>状态</dt><dd><span :class="['badge', tenant.status==='active'?'good':'neutral']">{{ tenant.status }}</span></dd>
          <dt>套餐</dt><dd>{{ tenant.plan ?? '—' }}</dd>
          <dt>创建时间</dt><dd><small>{{ tenant.created_at ? new Date(tenant.created_at).toLocaleString("zh-CN") : '—' }}</small></dd>
        </dl>
      </div>

      <div class="page-actions">
        <h2>应用列表 ({{ apps.length }})</h2>
        <button @click="showCreateApp = !showCreateApp">
          {{ showCreateApp ? "取消" : "添加应用" }}
        </button>
      </div>

      <div v-if="showCreateApp" class="panel" style="min-height:auto">
        <label>客户端类型
          <select v-model="newClientType">
            <option value="h5">H5 网页</option>
            <option value="miniapp">微信小程序</option>
            <option value="app">App</option>
          </select>
        </label>
        <label style="margin-top:8px">App ID
          <input v-model="newAppId" placeholder="wx... 或 dev-..." />
        </label>
        <button style="margin-top:10px" :disabled="creatingApp || !newAppId.trim()" @click="doCreateApp">
          {{ creatingApp ? "创建中..." : "确认添加" }}
        </button>
      </div>

      <table v-if="apps.length > 0">
        <thead>
          <tr>
            <th>类型</th><th>App ID</th><th>状态</th><th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in apps" :key="a.id">
            <td><span class="chip">{{ a.client_type }}</span></td>
            <td>{{ a.app_id }}</td>
            <td><span :class="['badge', a.status==='active'?'good':'neutral']">{{ a.status }}</span></td>
            <td><small>{{ a.created_at ? new Date(a.created_at).toLocaleString("zh-CN") : '—' }}</small></td>
          </tr>
        </tbody>
      </table>
    </template>
  </div>
</template>
