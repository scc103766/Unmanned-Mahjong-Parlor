<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";

import { useSessionStore } from "@/app/stores/session";
import { ApiError, merchantApi } from "@/core/api/client";

const route = useRoute();
const session = useSessionStore();
const connecting = ref(false);
const notice = ref("");

const tabs = [
  { name: "cleaner-tasks", label: "任务", icon: "📋" },
  { name: "cleaner-me", label: "我的", icon: "👤" },
];

const currentTitle = computed(() => route.meta.title ?? "保洁工作台");

async function devBootstrap() {
  connecting.value = true;
  notice.value = "";
  try {
    const response = await merchantApi.devBootstrap({
      tenant_name: "示例棋牌室",
      client_type: "h5",
      app_id: "dev-h5",
      phone: "18800003333",
      nickname: "保洁员_李姐",
    });
    session.applyToken(response);
    notice.value = "已登录";
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "登录失败";
    session.setError(message);
    notice.value = message;
  } finally {
    connecting.value = false;
  }
}
</script>

<template>
  <div class="customer-shell">
    <header class="customer-topbar">
      <h2>{{ currentTitle }}</h2>
      <div class="customer-topbar-right">
        <span v-if="notice" class="notice">{{ notice }}</span>
        <button
          v-if="!session.isConnected"
          class="mini"
          :disabled="connecting"
          @click="devBootstrap"
        >
          {{ connecting ? "登录中" : "一键登录" }}
        </button>
        <span v-else class="chip">{{ session.displayName }}</span>
      </div>
    </header>

    <main class="customer-main">
      <RouterView />
    </main>

    <nav class="customer-tabs">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.name"
        class="tab-item"
        :to="{ name: tab.name }"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
      </RouterLink>
    </nav>
  </div>
</template>

<style scoped>
.customer-shell {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f3f5f7;
}

.customer-topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 50px;
  padding: 0 14px;
  background: #4a7c59;
  color: #fff;
}

.customer-topbar h2 {
  font-size: 16px;
  color: #fff;
}

.customer-topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.customer-topbar .chip {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  font-size: 12px;
}

.customer-topbar .notice {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
}

.customer-topbar .mini {
  background: #fff;
  color: #4a7c59;
  font-size: 12px;
}

.customer-main {
  flex: 1;
  padding: 14px;
  padding-bottom: 80px;
}

.customer-tabs {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  background: #fff;
  border-top: 1px solid var(--line);
  z-index: 10;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  min-height: 56px;
  padding: 6px 4px 8px;
  color: var(--muted);
  text-decoration: none;
  font-size: 11px;
  transition: color 120ms;
}

.tab-item.router-link-active {
  color: #4a7c59;
}

.tab-icon {
  font-size: 20px;
}
</style>
