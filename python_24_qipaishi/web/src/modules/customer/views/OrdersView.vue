<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { ApiError } from "@/core/api/client";
import { customerApi } from "@/core/api/customer";
import { demoCustomerOrders } from "@/core/api/demo";
import type { OrderSummary } from "@/core/api/types";
import { formatMoney, statusLabel, statusTone } from "@/shared/utils/format";

const session = useSessionStore();
const orders = ref<OrderSummary[]>(demoCustomerOrders);
const loading = ref(false);
const error = ref("");
const activeFilter = ref("all");

const filters = [
  { key: "all", label: "全部" },
  { key: "pending_payment", label: "待支付" },
  { key: "paid", label: "已支付" },
  { key: "in_use", label: "使用中" },
  { key: "completed", label: "已完成" },
];

const filteredOrders = computed(() => {
  if (activeFilter.value === "all") return orders.value;
  return orders.value.filter((o) => o.status === activeFilter.value);
});

async function load() {
  if (!session.isConnected) return;
  loading.value = true;
  error.value = "";
  try {
    const data = await customerApi.listMyOrders();
    if (data.length > 0) orders.value = data;
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
    <div v-else-if="filteredOrders.length === 0" class="muted" style="text-align:center;padding:30px">
      暂无订单
    </div>

    <RouterLink
      v-for="o in filteredOrders"
      :key="o.id"
      :to="{ name: 'customer-order-detail', params: { orderId: o.id } }"
      class="order-card"
    >
      <div class="order-card-head">
        <strong>{{ o.order_no }}</strong>
        <span :class="['badge', statusTone(o.status)]">{{ statusLabel(o.status) }}</span>
      </div>
      <small>{{ new Date(o.start_at).toLocaleString("zh-CN") }} — {{ new Date(o.end_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }) }}</small>
      <div class="order-card-foot">
        <strong style="color:var(--brand)">{{ formatMoney(o.payable_amount) }}</strong>
        <small class="muted">房间 {{ o.room_id?.slice(0, 8) ?? "" }}...</small>
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
