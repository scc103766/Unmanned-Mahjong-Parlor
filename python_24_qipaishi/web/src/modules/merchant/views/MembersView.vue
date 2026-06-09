<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { ApiError, merchantApi } from "@/core/api/client";
import { demoMembers } from "@/core/api/demo";
import type { MemberSummary } from "@/core/api/types";
import { formatDateTime, formatMoney, statusLabel, statusTone } from "@/shared/utils/format";

const session = useSessionStore();
const loading = ref(false);
const actioning = ref(false);
const error = ref("");
const notice = ref("");
const members = ref<MemberSummary[]>(demoMembers);
const selectedUserId = ref(demoMembers[0]?.user_id ?? "");
const cashAmount = ref("0.00");
const giftAmount = ref("20.00");
const couponTemplateId = ref("");
const reason = ref("运营补偿");

const selectedMember = computed(() =>
  members.value.find((member) => member.user_id === selectedUserId.value),
);

async function load() {
  error.value = "";
  if (!session.isConnected) {
    members.value = demoMembers;
    selectedUserId.value ||= demoMembers[0]?.user_id ?? "";
    return;
  }
  loading.value = true;
  try {
    members.value = (await merchantApi.members(200)).members;
    selectedUserId.value ||= members.value[0]?.user_id ?? "";
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "会员加载失败";
  } finally {
    loading.value = false;
  }
}

async function compensate() {
  notice.value = "";
  error.value = "";
  if (!session.isConnected) {
    notice.value = "当前为样例模式，连接后端后可发放补偿";
    return;
  }
  if (!selectedUserId.value) {
    error.value = "请选择会员";
    return;
  }
  actioning.value = true;
  try {
    const response = await merchantApi.compensate({
      user_id: selectedUserId.value,
      cash_amount: cashAmount.value,
      gift_amount: giftAmount.value,
      coupon_template_id: couponTemplateId.value || null,
      reason: reason.value,
    });
    notice.value = `补偿已完成，钱包 ${response.wallet_account_id ?? "-"}，券 ${response.coupon_id ?? "-"}`;
    await load();
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "补偿失败";
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
      <span class="muted">{{ members.length }} 位会员</span>
      <button type="button" :disabled="loading" @click="load">{{ loading ? "刷新中" : "刷新" }}</button>
    </div>

    <p v-if="error" class="alert">{{ error }}</p>
    <p v-if="notice" class="notice-line">{{ notice }}</p>

    <section class="content-grid two-columns">
      <article class="panel span-2">
        <div class="panel-head">
          <h2>会员消费画像</h2>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>会员</th>
                <th>手机号</th>
                <th>余额</th>
                <th>订单</th>
                <th>总消费</th>
                <th>券</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="member in members"
                :key="member.user_id"
                :class="{ selected: member.user_id === selectedUserId }"
                @click="selectedUserId = member.user_id"
              >
                <td>
                  <strong>{{ member.nickname || member.user_id }}</strong>
                  <small>{{ formatDateTime(member.created_at) }}</small>
                </td>
                <td>{{ member.phone || "-" }}</td>
                <td>{{ formatMoney(member.cash_balance) }} + {{ formatMoney(member.gift_balance) }}</td>
                <td>{{ member.completed_order_count }}/{{ member.order_count }}</td>
                <td>{{ formatMoney(member.total_spend) }}</td>
                <td>{{ member.available_coupon_count }}/{{ member.coupon_count }}</td>
                <td><span class="badge" :class="statusTone(member.status)">{{ statusLabel(member.status) }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="panel">
        <div class="panel-head">
          <h2>人工补偿</h2>
        </div>
        <div class="form-stack">
          <label>
            会员
            <select v-model="selectedUserId">
              <option v-for="member in members" :key="member.user_id" :value="member.user_id">
                {{ member.nickname || member.user_id }}
              </option>
            </select>
          </label>
          <label>
            现金金额
            <input v-model="cashAmount" inputmode="decimal" />
          </label>
          <label>
            赠送金额
            <input v-model="giftAmount" inputmode="decimal" />
          </label>
          <label>
            优惠券模板
            <input v-model="couponTemplateId" placeholder="可选" />
          </label>
          <label>
            原因
            <input v-model="reason" />
          </label>
          <div v-if="selectedMember" class="summary-box">
            <span>当前余额</span>
            <strong>{{ formatMoney(selectedMember.cash_balance) }} + {{ formatMoney(selectedMember.gift_balance) }}</strong>
          </div>
          <button type="button" :disabled="actioning" @click="compensate">
            {{ actioning ? "提交中" : "发放补偿" }}
          </button>
        </div>
      </article>
    </section>
  </section>
</template>
