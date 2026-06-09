<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { ApiError } from "@/core/api/client";
import { customerApi } from "@/core/api/customer";
import { demoStores } from "@/core/api/demo";
import type { StoreSummary } from "@/core/api/types";

const session = useSessionStore();
const stores = ref<StoreSummary[]>(demoStores);
const loading = ref(false);
const error = ref("");
const searchText = ref("");

const filteredStores = computed(() => {
  if (!searchText.value.trim()) return stores.value;
  const q = searchText.value.trim().toLowerCase();
  return stores.value.filter(
    (s) =>
      s.name.toLowerCase().includes(q) ||
      (s.address ?? "").toLowerCase().includes(q),
  );
});

async function load() {
  if (!session.isConnected) return;
  loading.value = true;
  error.value = "";
  try {
    const data = await customerApi.listStores();
    if (data.length > 0) stores.value = data;
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
    <div class="customer-search">
      <input
        v-model="searchText"
        placeholder="搜索门店名称或地址..."
        aria-label="搜索门店"
      />
    </div>

    <div v-if="loading" class="muted" style="text-align:center;padding:20px">
      加载中...
    </div>
    <div v-else-if="error" class="alert">{{ error }}</div>
    <div v-else-if="filteredStores.length === 0" class="muted" style="text-align:center;padding:20px">
      暂无门店
    </div>

    <RouterLink
      v-for="store in filteredStores"
      :key="store.id"
      :to="{ name: 'customer-store-detail', params: { storeId: store.id } }"
      class="store-card"
    >
      <div class="store-card-img">
        <span class="store-placeholder">🏠</span>
      </div>
      <div class="store-card-body">
        <strong>{{ store.name }}</strong>
        <small>{{ store.address ?? "" }}</small>
        <div class="store-card-meta">
          <span v-if="store.status === 'active'" class="badge good">营业中</span>
          <span v-else class="badge neutral">休息中</span>
          <small v-if="store.notice" class="muted">{{ store.notice.slice(0, 30) }}{{ store.notice.length > 30 ? '...' : '' }}</small>
        </div>
      </div>
    </RouterLink>
  </div>
</template>

<style scoped>
.customer-search {
  margin-bottom: 8px;
}

.customer-search input {
  border-radius: 10px;
  background: #fff;
  padding: 10px 14px;
  border: 1px solid var(--line);
}

.store-card {
  display: flex;
  gap: 12px;
  background: #fff;
  border-radius: 10px;
  padding: 14px;
  text-decoration: none;
  color: inherit;
  border: 1px solid var(--line);
  transition: box-shadow 120ms;
}

.store-card:active {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.store-card-img {
  width: 70px;
  height: 70px;
  border-radius: 8px;
  background: #e8f0ee;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.store-placeholder {
  font-size: 32px;
  opacity: 0.6;
}

.store-card-body {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 4px;
  align-content: start;
}

.store-card-body strong {
  font-size: 16px;
  line-height: 1.3;
}

.store-card-body small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.store-card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
}

.store-card-meta .badge {
  font-size: 11px;
}
</style>
