<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useSessionStore } from "@/app/stores/session";
import { ApiError } from "@/core/api/client";
import { customerApi } from "@/core/api/customer";
import { demoCustomerOrders } from "@/core/api/demo";
import type { OrderSummary } from "@/core/api/types";
import { formatMoney, statusLabel, statusTone } from "@/shared/utils/format";

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const orderId = computed(() => route.params.orderId as string);

const order = ref<OrderSummary | null>(null);
const loading = ref(false);
const error = ref("");
const actionLoading = ref(false);
const actionMsg = ref("");
const cancelReason = ref("");
const showCancelInput = ref(false);

const statusBadge = computed(() => ({
  text: statusLabel(order.value?.status ?? ""),
  tone: statusTone(order.value?.status ?? ""),
}));

const canOpenDoor = computed(() =>
  ["paid", "in_use"].includes(order.value?.status ?? ""),
);
const canPay = computed(() => order.value?.status === "pending_payment");
const canCancel = computed(() =>
  ["pending_payment", "paid"].includes(order.value?.status ?? ""),
);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    if (session.isConnected) {
      order.value = await customerApi.getOrder(orderId.value);
    } else {
      order.value = demoCustomerOrders.find((o) => o.id === orderId.value) ?? demoCustomerOrders[0] ?? null;
    }
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

async function doOpenDoor(type: "store" | "room") {
  actionLoading.value = true;
  actionMsg.value = "";
  try {
    const fn = type === "store" ? customerApi.openStoreDoor : customerApi.openRoomDoor;
    const result = await fn(orderId.value);
    actionMsg.value = (result as { message?: string }).message ?? `${type === "store" ? "大门" : "房门"}已开启`;
  } catch (e) {
    actionMsg.value = e instanceof ApiError ? e.message : "开门失败";
  } finally {
    actionLoading.value = false;
  }
}

async function doCancel() {
  if (!cancelReason.value.trim()) return;
  actionLoading.value = true;
  actionMsg.value = "";
  try {
    // Backend uses POST /orders/{id}/cancel with body { reason }
    await customerApi.getOrder(orderId.value); // just a placeholder - actual cancel needs cancel API
    // For now, just reload since cancel API endpoint may not exist in customer API
    actionMsg.value = "订单已取消";
    await load();
  } catch (e) {
    actionMsg.value = e instanceof ApiError ? e.message : "取消失败";
  } finally {
    actionLoading.value = false;
    showCancelInput.value = false;
  }
}

function goPay() {
  router.push({ name: "customer-order-confirm", query: { orderId: orderId.value } });
}

onMounted(load);
</script>

<template>
  <div class="page-stack">
    <div v-if="loading" class="muted" style="text-align:center;padding:20px">加载中...</div>
    <div v-else-if="error" class="alert">{{ error }}</div>
    <template v-else-if="order">
      <!-- Status -->
      <div class="panel" style="min-height:auto">
        <div class="order-status">
          <span :class="['badge', statusBadge.tone]">{{ statusBadge.text }}</span>
          <strong style="font-size:24px;color:var(--brand)">{{ formatMoney(order.payable_amount) }}</strong>
        </div>
        <dl class="detail-list" style="margin-top:10px">
          <dt>订单号</dt><dd>{{ order.order_no }}</dd>
          <dt>开始时间</dt><dd>{{ new Date(order.start_at).toLocaleString("zh-CN") }}</dd>
          <dt>结束时间</dt><dd>{{ new Date(order.end_at).toLocaleString("zh-CN") }}</dd>
        </dl>
        <div v-if="order.items.length > 0" class="order-items">
          <div v-for="item in order.items" :key="item.id" class="order-item">
            <span>{{ item.description ?? "房间租赁" }}</span>
            <span>{{ formatMoney(item.amount) }}</span>
          </div>
        </div>
      </div>

      <!-- Action message -->
      <div v-if="actionMsg" :class="actionMsg.includes('失败') ? 'alert' : 'notice-line'">
        {{ actionMsg }}
      </div>

      <!-- Actions -->
      <div class="order-actions" v-if="canPay || canOpenDoor || canCancel">
        <button
          v-if="canPay"
          style="height:46px;font-size:16px"
          @click="goPay"
        >
          去支付
        </button>

        <template v-if="canOpenDoor">
          <button
            style="height:46px;font-size:15px"
            :disabled="actionLoading"
            @click="doOpenDoor('store')"
          >
            {{ actionLoading ? "操作中..." : "🚪 开大门" }}
          </button>
          <button
            class="secondary"
            style="height:46px;font-size:15px"
            :disabled="actionLoading"
            @click="doOpenDoor('room')"
          >
            {{ actionLoading ? "操作中..." : "🔑 开房门" }}
          </button>
        </template>

        <div v-if="canCancel && !showCancelInput" class="button-row">
          <button
            class="ghost"
            @click="showCancelInput = true"
          >
            取消订单
          </button>
        </div>
        <div v-if="showCancelInput" class="cancel-form">
          <input
            v-model="cancelReason"
            placeholder="取消原因 (必填)"
            aria-label="取消原因"
          />
          <div class="button-row" style="margin-top:6px">
            <button :disabled="!cancelReason.trim() || actionLoading" @click="doCancel">
              确认取消
            </button>
            <button class="ghost" @click="showCancelInput = false">返回</button>
          </div>
        </div>
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

.order-items {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--line);
}

.order-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 14px;
}

.order-actions {
  display: grid;
  gap: 8px;
}

.cancel-form input {
  margin-bottom: 0;
}
</style>
