import { defineStore } from "pinia";

import type { TokenResponse } from "@/core/api/types";

const STORAGE_KEY = "qipaishi.session";
const DEFAULT_API_PORT = "8000";

interface PersistedSession {
  apiBase: string;
  token: string;
  tenantId: string;
  userId: string;
  nickname: string;
  roles: string[];
}

interface SessionState extends PersistedSession {
  lastError: string;
}

function defaultApiBase(): string {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (configured) {
    return configured.trim().replace(/\/$/, "");
  }
  if (typeof window !== "undefined" && window.location.hostname) {
    return `${window.location.protocol}//${window.location.hostname}:${DEFAULT_API_PORT}`;
  }
  return `http://127.0.0.1:${DEFAULT_API_PORT}`;
}

function fallbackSession(): PersistedSession {
  return {
    apiBase: defaultApiBase(),
    token: "",
    tenantId: "",
    userId: "",
    nickname: "",
    roles: [],
  };
}

function readSession(): PersistedSession {
  const fallback = fallbackSession();
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return fallback;
  }
  try {
    return { ...fallback, ...JSON.parse(raw) } as PersistedSession;
  } catch {
    return fallback;
  }
}

function writeSession(state: PersistedSession): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export const useSessionStore = defineStore("session", {
  state: (): SessionState => ({
    ...readSession(),
    lastError: "",
  }),
  getters: {
    isConnected: (state) => Boolean(state.token),
    displayName: (state) => state.nickname || state.userId || "未连接",
    hasAnyRole: (state) => (roles: string[]) =>
      roles.length === 0 || roles.some((role) => state.roles.includes(role)),
  },
  actions: {
    persist() {
      writeSession({
        apiBase: this.apiBase,
        token: this.token,
        tenantId: this.tenantId,
        userId: this.userId,
        nickname: this.nickname,
        roles: this.roles,
      });
    },
    updateApiBase(apiBase: string) {
      this.apiBase = apiBase.trim().replace(/\/$/, "") || fallbackSession().apiBase;
      this.persist();
    },
    applyToken(response: TokenResponse) {
      this.token = response.access_token;
      this.tenantId = response.user.tenant_id ?? "";
      this.userId = response.user.user_id;
      this.nickname = response.user.nickname ?? "";
      this.roles = response.user.roles;
      this.lastError = "";
      this.persist();
    },
    applyRawToken(token: string) {
      this.token = token.trim();
      this.lastError = "";
      this.persist();
    },
    clearToken() {
      this.token = "";
      this.tenantId = "";
      this.userId = "";
      this.nickname = "";
      this.roles = [];
      this.lastError = "";
      this.persist();
    },
    setError(message: string) {
      this.lastError = message;
    },
  },
});
