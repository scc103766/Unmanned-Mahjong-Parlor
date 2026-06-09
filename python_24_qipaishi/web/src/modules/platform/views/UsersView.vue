<script setup lang="ts">
import { onMounted, ref } from "vue";

import { useSessionStore } from "@/app/stores/session";
import { platformApi, ApiError } from "@/core/api/platform";
import { demoUsers, demoRoles } from "@/core/api/demo";
import type { UserInfo, RoleInfo } from "@/core/api/types";

const session = useSessionStore();
const users = ref<UserInfo[]>(demoUsers);
const roles = ref<RoleInfo[]>(demoRoles);
const loading = ref(false);
const error = ref("");
const editingUser = ref<string | null>(null);
const selectedRoles = ref<string[]>([]);
const saving = ref(false);

async function load() {
  if (!session.isConnected) return;
  loading.value = true;
  error.value = "";
  try {
    const [u, r] = await Promise.all([
      platformApi.listUsers(),
      platformApi.listRoles(),
    ]);
    if (u.length > 0) users.value = u;
    if (r.length > 0) roles.value = r;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

function startEdit(user: UserInfo) {
  editingUser.value = user.id;
  selectedRoles.value = [...user.roles];
}

function cancelEdit() {
  editingUser.value = null;
  selectedRoles.value = [];
}

function toggleRole(roleName: string) {
  const idx = selectedRoles.value.indexOf(roleName);
  if (idx >= 0) {
    selectedRoles.value.splice(idx, 1);
  } else {
    selectedRoles.value.push(roleName);
  }
}

async function saveRoles(userId: string) {
  saving.value = true;
  error.value = "";
  try {
    await platformApi.assignRoles(userId, selectedRoles.value);
    editingUser.value = null;
    await load();
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "保存失败";
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="page-stack">
    <div class="page-actions">
      <h2>用户列表 ({{ users.length }})</h2>
    </div>

    <div v-if="loading" class="muted" style="text-align:center;padding:20px">加载中...</div>
    <div v-else-if="error" class="alert">{{ error }}</div>

    <table v-if="users.length > 0">
      <thead>
        <tr>
          <th>用户</th><th>手机</th><th>状态</th><th>角色</th><th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id" :class="{ selected: editingUser === u.id }">
          <td>
            <strong>{{ u.nickname ?? '未命名' }}</strong>
            <small>{{ u.id }}</small>
          </td>
          <td>{{ u.phone ?? '—' }}</td>
          <td><span :class="['badge', u.status==='active'?'good':'neutral']">{{ u.status }}</span></td>
          <td>
            <span v-for="r in u.roles" :key="r" class="chip" style="margin-right:4px">{{ r }}</span>
            <span v-if="u.roles.length === 0" class="muted">—</span>
          </td>
          <td>
            <button
              v-if="editingUser !== u.id"
              class="mini secondary"
              @click="startEdit(u)"
            >
              编辑角色
            </button>
            <div v-else class="button-row">
              <button class="mini" :disabled="saving" @click="saveRoles(u.id)">保存</button>
              <button class="mini ghost" @click="cancelEdit">取消</button>
            </div>
            <div v-if="editingUser === u.id" style="margin-top:6px">
              <div class="chip-row" style="flex-wrap:wrap;margin-top:4px">
                <button
                  v-for="r in roles"
                  :key="r.name"
                  :class="['mini', selectedRoles.includes(r.name) ? '' : 'ghost']"
                  style="margin:2px"
                  @click="toggleRole(r.name)"
                >
                  {{ r.label }}
                </button>
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.chip-row {
  display: flex;
  gap: 4px;
}
</style>
