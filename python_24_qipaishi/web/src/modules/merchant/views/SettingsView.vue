<script setup lang="ts">
import { ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { ApiError, merchantApi } from "@/core/api/client";
import type { Principal } from "@/core/api/types";

const session = useSessionStore();
const apiBase = ref(session.apiBase);
const tenantName = ref("示例棋牌室");
const phone = ref("18800000000");
const nickname = ref("开发管理员");
const currentUser = ref<Principal | null>(null);
const loading = ref(false);
const error = ref("");
const notice = ref("");

async function bootstrap() {
  loading.value = true;
  error.value = "";
  notice.value = "";
  try {
    session.updateApiBase(apiBase.value);
    const token = await merchantApi.devBootstrap({
      tenant_name: tenantName.value,
      client_type: "h5",
      app_id: "dev-h5",
      phone: phone.value,
      nickname: nickname.value,
    });
    session.applyToken(token);
    currentUser.value = token.user;
    notice.value = "开发身份已写入";
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "开发登录失败";
  } finally {
    loading.value = false;
  }
}

async function loadMe() {
  loading.value = true;
  error.value = "";
  notice.value = "";
  try {
    session.updateApiBase(apiBase.value);
    currentUser.value = await merchantApi.currentUser();
    notice.value = "当前身份已刷新";
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "身份读取失败";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="page-stack">
    <p v-if="error" class="alert">{{ error }}</p>
    <p v-if="notice" class="notice-line">{{ notice }}</p>

    <section class="content-grid two-columns">
      <article class="panel">
        <div class="panel-head">
          <h2>后端连接</h2>
        </div>
        <div class="form-stack">
          <label>
            API 地址
            <input v-model="apiBase" />
          </label>
          <label>
            租户名称
            <input v-model="tenantName" />
          </label>
          <label>
            手机号
            <input v-model="phone" />
          </label>
          <label>
            昵称
            <input v-model="nickname" />
          </label>
          <div class="button-row">
            <button type="button" :disabled="loading" @click="bootstrap">开发登录</button>
            <button type="button" class="secondary" :disabled="loading || !session.token" @click="loadMe">
              读取身份
            </button>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="panel-head">
          <h2>当前身份</h2>
        </div>
        <dl class="detail-list">
          <dt>连接状态</dt>
          <dd>{{ session.isConnected ? "已连接" : "样例模式" }}</dd>
          <dt>用户</dt>
          <dd>{{ currentUser?.nickname || session.nickname || "-" }}</dd>
          <dt>用户 ID</dt>
          <dd>{{ currentUser?.user_id || session.userId || "-" }}</dd>
          <dt>租户 ID</dt>
          <dd>{{ currentUser?.tenant_id || session.tenantId || "-" }}</dd>
          <dt>角色</dt>
          <dd>{{ (currentUser?.roles || session.roles).join(", ") || "-" }}</dd>
        </dl>
      </article>
    </section>
  </section>
</template>
