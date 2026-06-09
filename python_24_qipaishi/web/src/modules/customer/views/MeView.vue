<script setup lang="ts">
import { onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { ApiError } from "@/core/api/client";
import { customerApi } from "@/core/api/customer";
import { demoWallet } from "@/core/api/demo";
import type { WalletAccount } from "@/core/api/types";
import { formatMoney } from "@/shared/utils/format";

const session = useSessionStore();
const wallet = ref<WalletAccount | null>(null);
const loading = ref(false);

async function load() {
  if (!session.isConnected) {
    wallet.value = demoWallet;
    return;
  }
  loading.value = true;
  try {
    wallet.value = await customerApi.getMyWallet();
  } catch (e) {
    if (e instanceof ApiError) {
      wallet.value = null;
    }
  } finally {
    loading.value = false;
  }
}

function handleLogout() {
  session.clearToken();
  wallet.value = demoWallet;
}

onMounted(load);
</script>

<template>
  <div class="page-stack">
    <div class="panel" style="min-height:auto">
      <div v-if="session.isConnected">
        <h3 style="margin-bottom:6px">{{ session.displayName }}</h3>
        <small class="muted">已登录 · {{ session.roles.join(", ") || "顾客" }}</small>
      </div>
      <div v-else>
        <h3 style="margin-bottom:6px;color:var(--muted)">未登录</h3>
        <small class="muted">点击顶部"一键登录"按钮连接服务</small>
      </div>
    </div>

    <div v-if="wallet" class="panel" style="min-height:auto">
      <h3 style="margin-bottom:10px">我的钱包</h3>
      <div class="wallet-balance">
        <div class="wallet-item">
          <span class="muted">余额</span>
          <strong>{{ formatMoney(wallet.cash_balance) }}</strong>
        </div>
        <div class="wallet-item">
          <span class="muted">赠送余额</span>
          <strong>{{ formatMoney(wallet.gift_balance) }}</strong>
        </div>
      </div>
    </div>

    <div v-if="session.isConnected" class="button-row">
      <button class="ghost" style="width:100%;height:44px" @click="handleLogout">
        退出登录
      </button>
    </div>

    <div class="panel" style="min-height:auto">
      <h3 style="margin-bottom:8px">关于</h3>
      <small class="muted">
        24H 无人棋牌室管理系统<br />
        版本 0.1.0 (M8 工程化)<br />
        Vue 3 + Vite + TypeScript
      </small>
    </div>
  </div>
</template>

<style scoped>
.wallet-balance {
  display: grid;
  gap: 12px;
}

.wallet-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--panel-soft);
  border-radius: 8px;
  border: 1px solid var(--line);
}

.wallet-item strong {
  font-size: 20px;
  color: var(--brand);
}
</style>
