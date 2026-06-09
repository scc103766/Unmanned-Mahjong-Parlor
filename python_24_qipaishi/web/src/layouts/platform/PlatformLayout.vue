<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";

import { useSessionStore } from "@/app/stores/session";
import { merchantApi } from "@/core/api/client";
import { ApiError } from "@/core/api/client";

const route = useRoute();
const session = useSessionStore();

const apiBaseInput = ref(session.apiBase);
const tokenInput = ref(session.token);
const connecting = ref(false);
const notice = ref("");

const navItems = [
  { name: "platform-tenants", label: "租户", symbol: "租" },
  { name: "platform-users", label: "用户", symbol: "户" },
  { name: "platform-devices", label: "设备", symbol: "设" },
  { name: "platform-exceptions", label: "异常", symbol: "警" },
  { name: "platform-audit", label: "审计", symbol: "审" },
  { name: "platform-settings", label: "设置", symbol: "设" },
];

const currentTitle = computed(() => route.meta.title ?? "平台管理");
const connectionState = computed(() => (session.isConnected ? "已连接" : "样例模式"));

async function devBootstrap() {
  connecting.value = true;
  notice.value = "";
  try {
    session.updateApiBase(apiBaseInput.value);
    const response = await merchantApi.devBootstrap({
      tenant_name: "示例棋牌室",
      client_type: "h5",
      app_id: "dev-h5",
      phone: "18809999999",
      nickname: "平台管理员",
    });
    session.applyToken(response);
    tokenInput.value = response.access_token;
    notice.value = "平台管理员已连接";
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "连接失败";
    session.setError(message);
    notice.value = message;
  } finally {
    connecting.value = false;
  }
}

function saveConnection() {
  session.updateApiBase(apiBaseInput.value);
  session.applyRawToken(tokenInput.value);
  notice.value = "连接参数已保存";
}

function clearToken() {
  session.clearToken();
  tokenInput.value = "";
  notice.value = "已切回样例模式";
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar platform-sidebar">
      <RouterLink class="brand" :to="{ name: 'platform-tenants' }">
        <span class="brand-mark">管</span>
        <span>
          <strong>平台管理</strong>
          <small>Platform Admin</small>
        </span>
      </RouterLink>

      <nav class="nav-list" aria-label="平台管理">
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
          <small>{{ session.displayName }}</small>
        </div>
      </div>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">M8 平台后台</p>
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
        <span v-for="role in session.roles" :key="role" class="chip">{{ role }}</span>
        <span v-if="notice" class="notice">{{ notice }}</span>
      </section>

      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.platform-sidebar {
  background: #2c1810;
}

.platform-sidebar .brand-mark {
  background: #e8a838;
}
</style>
