import type { Router } from "vue-router";

import { useSessionStore } from "@/app/stores/session";

export function installPermissionGuards(router: Router): void {
  router.beforeEach((to) => {
    const session = useSessionStore();
    const roles = to.meta.roles ?? [];
    if (roles.length > 0 && session.isConnected && !session.hasAnyRole(roles)) {
      // Redirect customer role failures to stores, merchant failures to dashboard
      const isOnCustomer = String(to.path).startsWith("/customer");
      return { name: isOnCustomer ? "customer-stores" : "dashboard" };
    }
    return true;
  });

  router.afterEach((to) => {
    const base = String(to.path).startsWith("/customer")
      ? "24H 无人棋牌室"
      : "无人棋牌室运营后台";
    document.title = to.meta.title ? `${to.meta.title} - ${base}` : base;
  });
}
