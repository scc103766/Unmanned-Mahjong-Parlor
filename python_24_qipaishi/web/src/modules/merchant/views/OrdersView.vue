<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { ApiError, merchantApi } from "@/core/api/client";
import { demoOrders } from "@/core/api/demo";
import type { OrderRescheduleQuote, OrderSummary } from "@/core/api/types";
import {
  addHours,
  formatDateTime,
  formatMoney,
  statusLabel,
  statusTone,
  toDateTimeInputValue,
} from "@/shared/utils/format";

const session = useSessionStore();
const loading = ref(false);
const actioning = ref(false);
const error = ref("");
const notice = ref("");
const orders = ref<OrderSummary[]>(demoOrders);
const selectedOrderId = ref(demoOrders[0]?.id ?? "");
const newStartAt = ref(toDateTimeInputValue(addHours(new Date(), 2)));
const newEndAt = ref(toDateTimeInputValue(addHours(new Date(), 5)));
const quote = ref<OrderRescheduleQuote | null>(null);

const selectedOrder = computed(() => orders.value.find((order) => order.id === selectedOrderId.value));

async function load() {
  error.value = "";
  if (!session.isConnected) {
    orders.value = demoOrders;
    selectedOrderId.value ||= demoOrders[0]?.id ?? "";
    return;
  }
  loading.value = true;
  try {
    orders.value = await merchantApi.orders();
    selectedOrderId.value ||= orders.value[0]?.id ?? "";
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "订单加载失败";
  } finally {
    loading.value = false;
  }
}

function requireConnection(): boolean {
  if (!session.isConnected) {
    notice.value = "当前为样例模式，连接后端后可执行订单改时";
    return false;
  }
  return true;
}

async function quoteReschedule() {
  if (!selectedOrderId.value || !requireConnection()) {
    return;
  }
  actioning.value = true;
  error.value = "";
  notice.value = "";
  try {
    quote.value = await merchantApi.quoteReschedule(
      selectedOrderId.value,
      new Date(newStartAt.value).toISOString(),
      new Date(newEndAt.value).toISOString(),
    );
    notice.value = "改时试算已生成";
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "改时试算失败";
  } finally {
    actioning.value = false;
  }
}

async function submitReschedule() {
  if (!selectedOrderId.value || !requireConnection()) {
    return;
  }
  actioning.value = true;
  error.value = "";
  notice.value = "";
  try {
    const updated = await merchantApi.rescheduleOrder(
      selectedOrderId.value,
      new Date(newStartAt.value).toISOString(),
      new Date(newEndAt.value).toISOString(),
    );
    orders.value = orders.value.map((order) => (order.id === updated.id ? updated : order));
    quote.value = null;
    notice.value = "订单改时已完成";
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "订单改时失败";
  } finally {
    actioning.value = false;
  }
}

onMounted(() => {
  void load();
});
</script>

<template>
  <section class="page-stack">
    <div class="page-actions">
      <span class="muted">{{ orders.length }} 笔订单</span>
      <button type="button" :disabled="loading" @click="load">{{ loading ? "刷新中" : "刷新" }}</button>
    </div>

    <p v-if="error" class="alert">{{ error }}</p>
    <p v-if="notice" class="notice-line">{{ notice }}</p>

    <section class="content-grid two-columns">
      <article class="panel span-2">
        <div class="panel-head">
          <h2>订单列表</h2>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>订单号</th>
                <th>房间</th>
                <th>用户</th>
                <th>时间</th>
                <th>金额</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="order in orders"
                :key="order.id"
                :class="{ selected: order.id === selectedOrderId }"
                @click="selectedOrderId = order.id"
              >
                <td>{{ order.order_no }}</td>
                <td>{{ order.room_id }}</td>
                <td>{{ order.user_id }}</td>
                <td>{{ formatDateTime(order.start_at) }} - {{ formatDateTime(order.end_at) }}</td>
                <td>{{ formatMoney(order.payable_amount) }}</td>
                <td><span class="badge" :class="statusTone(order.status)">{{ statusLabel(order.status) }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="panel">
        <div class="panel-head">
          <h2>后台改时</h2>
        </div>
        <div class="form-stack">
          <label>
            订单
            <select v-model="selectedOrderId">
              <option v-for="order in orders" :key="order.id" :value="order.id">
                {{ order.order_no }} / {{ order.room_id }}
              </option>
            </select>
          </label>
          <label>
            新开始时间
            <input v-model="newStartAt" type="datetime-local" />
          </label>
          <label>
            新结束时间
            <input v-model="newEndAt" type="datetime-local" />
          </label>
          <div v-if="selectedOrder" class="summary-box">
            <span>原时间</span>
            <strong>{{ formatDateTime(selectedOrder.start_at) }} - {{ formatDateTime(selectedOrder.end_at) }}</strong>
          </div>
          <div v-if="quote" class="summary-box">
            <span>差额</span>
            <strong>{{ formatMoney(quote.delta_amount) }}</strong>
            <small>{{ formatMoney(quote.original_amount) }} -> {{ formatMoney(quote.new_amount) }}</small>
          </div>
          <div class="button-row">
            <button type="button" :disabled="actioning" @click="quoteReschedule">试算</button>
            <button type="button" class="secondary" :disabled="actioning" @click="submitReschedule">
              确认改时
            </button>
          </div>
        </div>
      </article>
    </section>
  </section>
</template>
