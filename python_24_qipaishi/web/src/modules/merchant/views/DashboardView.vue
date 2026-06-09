<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { ApiError, merchantApi } from "@/core/api/client";
import { demoDashboard, demoExceptions, demoRooms, demoWithdrawals } from "@/core/api/demo";
import type { MerchantDashboard, OperationException, RoomUsage, Withdrawal } from "@/core/api/types";
import { useSessionStore } from "@/app/stores/session";
import {
  formatDateTime,
  formatMoney,
  formatNumber,
  formatPercent,
  severityLabel,
  sourceLabel,
  statusLabel,
  statusTone,
} from "@/shared/utils/format";

const session = useSessionStore();
const loading = ref(false);
const error = ref("");
const dashboard = ref<MerchantDashboard>(demoDashboard);
const rooms = ref<RoomUsage[]>(demoRooms);
const exceptions = ref<OperationException[]>(demoExceptions);
const withdrawals = ref<Withdrawal[]>(demoWithdrawals);

const metricCards = computed(() => [
  { label: "净收入", value: formatMoney(dashboard.value.net_revenue), hint: `退款 ${formatMoney(dashboard.value.refund_amount)}` },
  { label: "订单数", value: dashboard.value.order_count, hint: `${dashboard.value.in_use_order_count} 间使用中` },
  { label: "会员数", value: dashboard.value.member_count, hint: `充值 ${formatMoney(dashboard.value.wallet_recharge_amount)}` },
  { label: "房间利用率", value: formatPercent(dashboard.value.room_utilization_rate), hint: `${formatNumber(dashboard.value.usage_hours)} 小时` },
]);

async function load() {
  error.value = "";
  if (!session.isConnected) {
    dashboard.value = demoDashboard;
    rooms.value = demoRooms;
    exceptions.value = demoExceptions;
    withdrawals.value = demoWithdrawals;
    return;
  }

  loading.value = true;
  try {
    const [dashboardData, roomUsage, exceptionList, withdrawalRows] = await Promise.all([
      merchantApi.dashboard(),
      merchantApi.roomUsage(),
      merchantApi.exceptions(),
      merchantApi.withdrawals({ status: "pending" }),
    ]);
    dashboard.value = dashboardData;
    rooms.value = roomUsage.rooms;
    exceptions.value = exceptionList.exceptions;
    withdrawals.value = withdrawalRows;
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "数据加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void load();
});
</script>

<template>
  <section class="page-stack">
    <div class="page-actions">
      <span class="muted">
        {{ formatDateTime(dashboard.start_at) }} - {{ formatDateTime(dashboard.end_at) }}
      </span>
      <button type="button" :disabled="loading" @click="load">
        {{ loading ? "刷新中" : "刷新" }}
      </button>
    </div>

    <p v-if="error" class="alert">{{ error }}</p>

    <section class="metrics-grid">
      <article v-for="item in metricCards" :key="item.label" class="metric">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </section>

    <section class="content-grid">
      <article class="panel span-2">
        <div class="panel-head">
          <h2>房间使用率</h2>
          <span class="muted">{{ dashboard.active_room_count }}/{{ dashboard.room_count }} 间可用</span>
        </div>
        <div class="usage-list">
          <div v-for="room in rooms" :key="room.room_id" class="usage-row">
            <div>
              <strong>{{ room.room_name }}</strong>
              <small>{{ room.order_count }} 单 / {{ formatNumber(room.usage_hours) }} 小时</small>
            </div>
            <meter min="0" max="1" :value="Number(room.utilization_rate)"></meter>
            <span>{{ formatPercent(room.utilization_rate) }}</span>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="panel-head">
          <h2>保洁与设备</h2>
        </div>
        <div class="compact-stats">
          <div><span>待保洁</span><strong>{{ dashboard.cleaning_pending_count }}</strong></div>
          <div><span>超时</span><strong>{{ dashboard.cleaning_overdue_count }}</strong></div>
          <div><span>已完成</span><strong>{{ dashboard.cleaning_completed_count }}</strong></div>
          <div><span>设备失败</span><strong>{{ dashboard.device_failure_count }}</strong></div>
        </div>
      </article>

      <article class="panel span-2">
        <div class="panel-head">
          <h2>运营异常</h2>
          <RouterLink :to="{ name: 'exceptions' }" class="text-link">查看全部</RouterLink>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>来源</th>
                <th>级别</th>
                <th>消息</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in exceptions.slice(0, 5)" :key="item.id">
                <td>{{ sourceLabel(item.source) }}</td>
                <td><span class="badge" :class="statusTone(item.status)">{{ severityLabel(item.severity) }}</span></td>
                <td>{{ item.message }}</td>
                <td>{{ formatDateTime(item.occurred_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="panel">
        <div class="panel-head">
          <h2>待审核提现</h2>
          <RouterLink :to="{ name: 'withdrawals' }" class="text-link">处理</RouterLink>
        </div>
        <div class="timeline">
          <div v-for="item in withdrawals.slice(0, 4)" :key="item.id" class="timeline-item">
            <strong>{{ formatMoney(item.amount) }}</strong>
            <span>{{ item.user_id }}</span>
            <small>{{ statusLabel(item.status) }} / {{ formatDateTime(item.requested_at) }}</small>
          </div>
        </div>
      </article>
    </section>
  </section>
</template>
