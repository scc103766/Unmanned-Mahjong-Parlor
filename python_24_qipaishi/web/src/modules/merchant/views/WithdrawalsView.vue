<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { ApiError, merchantApi } from "@/core/api/client";
import { demoWithdrawals } from "@/core/api/demo";
import type { Withdrawal } from "@/core/api/types";
import { formatDateTime, formatMoney, statusLabel, statusTone } from "@/shared/utils/format";

const session = useSessionStore();
const loading = ref(false);
const actioningId = ref("");
const error = ref("");
const notice = ref("");
const statusFilter = ref("");
const rows = ref<Withdrawal[]>(demoWithdrawals);

const totalPendingAmount = computed(() =>
  rows.value
    .filter((item) => item.status === "pending")
    .reduce((sum, item) => sum + Number(item.amount), 0),
);

async function load() {
  error.value = "";
  if (!session.isConnected) {
    rows.value = demoWithdrawals.filter((item) => !statusFilter.value || item.status === statusFilter.value);
    return;
  }
  loading.value = true;
  try {
    rows.value = await merchantApi.withdrawals(statusFilter.value ? { status: statusFilter.value } : undefined);
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "提现加载失败";
  } finally {
    loading.value = false;
  }
}

async function runAction(id: string, action: "approve" | "reject" | "paid") {
  notice.value = "";
  error.value = "";
  if (!session.isConnected) {
    notice.value = "当前为样例模式，连接后端后可处理提现";
    return;
  }
  actioningId.value = id;
  try {
    let updated: Withdrawal;
    if (action === "approve") {
      updated = await merchantApi.approveWithdrawal(id, "后台审核通过");
    } else if (action === "reject") {
      const reason = window.prompt("驳回原因", "资料不完整") ?? "";
      if (!reason.trim()) {
        return;
      }
      updated = await merchantApi.rejectWithdrawal(id, reason);
    } else {
      const payoutRef = window.prompt("打款流水号", `payout-${Date.now()}`) ?? "";
      if (!payoutRef.trim()) {
        return;
      }
      updated = await merchantApi.markWithdrawalPaid(id, payoutRef, "后台确认打款");
    }
    rows.value = rows.value.map((item) => (item.id === updated.id ? updated : item));
    notice.value = "提现状态已更新";
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "提现处理失败";
  } finally {
    actioningId.value = "";
  }
}

onMounted(() => {
  void load();
});
</script>

<template>
  <section class="page-stack">
    <div class="page-actions">
      <div class="inline-controls">
        <label>
          状态
          <select v-model="statusFilter" @change="load">
            <option value="">全部</option>
            <option value="pending">待处理</option>
            <option value="approved">已审核</option>
            <option value="rejected">已驳回</option>
            <option value="paid_out">已打款</option>
          </select>
        </label>
        <span class="muted">待处理合计 {{ formatMoney(totalPendingAmount) }}</span>
      </div>
      <button type="button" :disabled="loading" @click="load">{{ loading ? "刷新中" : "刷新" }}</button>
    </div>

    <p v-if="error" class="alert">{{ error }}</p>
    <p v-if="notice" class="notice-line">{{ notice }}</p>

    <article class="panel">
      <div class="panel-head">
        <h2>提现审核</h2>
        <span class="muted">{{ rows.length }} 条</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>申请人</th>
              <th>金额</th>
              <th>备注</th>
              <th>申请时间</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in rows" :key="item.id">
              <td>{{ item.user_id }}</td>
              <td>{{ formatMoney(item.amount) }}</td>
              <td>{{ item.remark || item.reject_reason || "-" }}</td>
              <td>{{ formatDateTime(item.requested_at) }}</td>
              <td><span class="badge" :class="statusTone(item.status)">{{ statusLabel(item.status) }}</span></td>
              <td>
                <div class="table-actions">
                  <button
                    type="button"
                    class="mini"
                    :disabled="actioningId === item.id || item.status !== 'pending'"
                    @click="runAction(item.id, 'approve')"
                  >
                    通过
                  </button>
                  <button
                    type="button"
                    class="mini ghost"
                    :disabled="actioningId === item.id || item.status !== 'pending'"
                    @click="runAction(item.id, 'reject')"
                  >
                    驳回
                  </button>
                  <button
                    type="button"
                    class="mini secondary"
                    :disabled="actioningId === item.id || item.status !== 'approved'"
                    @click="runAction(item.id, 'paid')"
                  >
                    打款
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>
