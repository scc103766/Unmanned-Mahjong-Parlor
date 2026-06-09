<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";

import { useSessionStore } from "@/app/stores/session";
import { ApiError, merchantApi } from "@/core/api/client";

const route = useRoute();
const session = useSessionStore();

const apiBaseInput = ref(session.apiBase);
const tokenInput = ref(session.token);
const connecting = ref(false);
const notice = ref("");

const navItems = [
  { name: "dashboard", label: "总览", symbol: "览" },
  { name: "orders", label: "订单", symbol: "单" },
  { name: "members", label: "会员", symbol: "会" },
  { name: "withdrawals", label: "提现", symbol: "款" },
  { name: "exceptions", label: "异常", symbol: "警" },
  { name: "settings", label: "设置", symbol: "设" },
];

const currentTitle = computed(() => route.meta.title ?? "运营总览");
const connectionState = computed(() => (session.isConnected ? "已连接" : "样例模式"));
const tokenPreview = computed(() => {
  if (!session.token) {
    return "未写入 token";
  }
  return `${session.token.slice(0, 10)}...${session.token.slice(-6)}`;
});

function saveConnection() {
  session.updateApiBase(apiBaseInput.value);
  session.applyRawToken(tokenInput.value);
  notice.value = "连接参数已保存";
}

async function devBootstrap() {
  connecting.value = true;
  notice.value = "";
  try {
    session.updateApiBase(apiBaseInput.value);
    const response = await merchantApi.devBootstrap({
      tenant_name: "示例棋牌室",
      client_type: "h5",
      app_id: "dev-h5",
      phone: "18800000000",
      nickname: "开发管理员",
    });
    session.applyToken(response);
    tokenInput.value = response.access_token;
    notice.value = "开发管理员已连接";
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "连接失败";
    session.setError(message);
    notice.value = message;
  } finally {
    connecting.value = false;
  }
}

function clearToken() {
  session.clearToken();
  tokenInput.value = "";
  notice.value = "已切回样例模式";
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <RouterLink class="brand" :to="{ name: 'dashboard' }">
        <span class="brand-mark">棋</span>
        <span>
          <strong>无人棋牌室</strong>
          <small>Merchant Ops</small>
        </span>
      </RouterLink>

      <nav class="nav-list" aria-label="商家后台">
        <RouterLink
          v-for="item in navItems"
          :key="item.name"
          class="nav-item"
          :to="{ name: item.name }"
        >
          <span class="nav-symbol">{{ item.symbol }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar-status">
        <span class="status-dot" :class="{ connected: session.isConnected }"></span>
        <div>
          <strong>{{ connectionState }}</strong>
          <small>{{ tokenPreview }}</small>
        </div>
      </div>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">M8 工程化后台</p>
          <h1>{{ currentTitle }}</h1>
        </div>

        <form class="connection" @submit.prevent="saveConnection">
          <label>
            API 地址
            <input v-model="apiBaseInput" aria-label="API 地址" />
          </label>
          <label>
            Bearer Token
            <input v-model="tokenInput" aria-label="Bearer Token" autocomplete="off" />
          </label>
          <div class="connection-actions">
            <button type="submit">保存</button>
            <button type="button" class="secondary" :disabled="connecting" @click="devBootstrap">
              {{ connecting ? "连接中" : "开发登录" }}
            </button>
            <button type="button" class="ghost" @click="clearToken">清除</button>
          </div>
        </form>
      </header>

      <section class="operator-strip">
        <span>{{ session.displayName }}</span>
        <span v-if="session.tenantId">租户 {{ session.tenantId }}</span>
        <span v-for="role in session.roles" :key="role" class="chip">{{ role }}</span>
        <span v-if="notice" class="notice">{{ notice }}</span>
      </section>

      <RouterView />
    </main>
  </div>
</template>
