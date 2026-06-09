<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { useSessionStore } from "@/app/stores/session";
import { ApiError } from "@/core/api/client";
import { customerApi } from "@/core/api/customer";
import { demoCustomerRooms, demoStores } from "@/core/api/demo";
import type { RoomSummary, StoreSummary } from "@/core/api/types";

const route = useRoute();
const session = useSessionStore();
const storeId = computed(() => route.params.storeId as string);

const store = ref<StoreSummary | null>(null);
const rooms = ref<RoomSummary[]>(demoCustomerRooms);
const loading = ref(false);
const error = ref("");

const storeName = computed(() => store.value?.name ?? "门店详情");
const filteredRooms = computed(() =>
  rooms.value.filter((r) => r.store_id === storeId.value),
);

function getRoomPriceLabel(room: RoomSummary): string {
  if (room.tags.includes("商务茶桌")) return "¥66/时";
  if (room.tags.includes("舒适沙发")) return "¥48/时";
  return "¥66/时";
}

function getRoomStatusLabel(room: RoomSummary): { text: string; cls: string } {
  if (room.cleaning_status === "dirty") return { text: "清洁中", cls: "badge warn" };
  if (room.status !== "active") return { text: "维护中", cls: "badge neutral" };
  return { text: "可预约", cls: "badge good" };
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    if (session.isConnected) {
      const [storeData, roomData] = await Promise.all([
        customerApi.getStore(storeId.value),
        customerApi.listRooms(storeId.value),
      ]);
      store.value = storeData;
      if (roomData.length > 0) rooms.value = roomData;
    } else {
      store.value = demoStores.find((s) => s.id === storeId.value) ?? null;
    }
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
    <div v-if="loading" class="muted" style="text-align:center;padding:20px">加载中...</div>
    <div v-else-if="error" class="alert">{{ error }}</div>
    <template v-else>
      <!-- Store header -->
      <div class="store-header">
        <div class="store-header-img">
          <span class="store-placeholder">🏠</span>
        </div>
        <div>
          <h1>{{ storeName }}</h1>
          <small>{{ store?.address ?? "" }}</small>
          <div class="store-header-meta" v-if="store">
            <span v-if="store.wifi_ssid" class="notice">WiFi: {{ store.wifi_ssid }}</span>
            <span v-if="store.contact_phone" class="muted">📞 {{ store.contact_phone }}</span>
          </div>
        </div>
      </div>

      <div v-if="store?.notice" class="notice-line">{{ store.notice }}</div>

      <!-- Room list -->
      <h3 style="margin:4px 0">可选房间 ({{ filteredRooms.length }})</h3>

      <div v-if="filteredRooms.length === 0" class="muted" style="text-align:center;padding:16px">
        暂无可用房间
      </div>

      <RouterLink
        v-for="room in filteredRooms"
        :key="room.id"
        :to="{ name: 'customer-booking', query: { storeId: storeId, roomId: room.id } }"
        class="room-card"
      >
        <div class="room-card-img">
          <span class="store-placeholder" style="font-size:28px">🎲</span>
        </div>
        <div class="room-card-body">
          <div class="room-card-head">
            <strong>{{ room.name }}</strong>
            <span :class="getRoomStatusLabel(room).cls">{{ getRoomStatusLabel(room).text }}</span>
          </div>
          <small>{{ room.tags.join(" · ") }}</small>
          <div class="room-card-foot">
            <span class="room-price">{{ getRoomPriceLabel(room) }}</span>
            <small>可容 {{ room.capacity }} 人</small>
          </div>
        </div>
      </RouterLink>
    </template>
  </div>
</template>

<style scoped>
.store-header {
  display: flex;
  gap: 12px;
  background: #fff;
  border-radius: 10px;
  padding: 16px;
  border: 1px solid var(--line);
}

.store-header-img {
  width: 80px;
  height: 80px;
  border-radius: 10px;
  background: #e8f0ee;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.store-placeholder {
  font-size: 36px;
  opacity: 0.6;
}

.store-header div {
  min-width: 0;
}

.store-header h1 {
  font-size: 18px;
  margin-bottom: 4px;
}

.store-header small {
  display: block;
  line-height: 1.4;
}

.store-header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}

.store-header-meta .notice {
  font-size: 11px;
}

.room-card {
  display: flex;
  gap: 12px;
  background: #fff;
  border-radius: 10px;
  padding: 14px;
  border: 1px solid var(--line);
  text-decoration: none;
  color: inherit;
  transition: box-shadow 120ms;
}

.room-card:active {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.room-card-img {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  background: #e8f0ee;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.room-card-body {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 4px;
}

.room-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.room-card-head strong {
  font-size: 15px;
}

.room-card-head .badge {
  font-size: 11px;
  flex-shrink: 0;
}

.room-card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 2px;
}

.room-price {
  font-size: 16px;
  font-weight: 800;
  color: var(--brand);
}
</style>
