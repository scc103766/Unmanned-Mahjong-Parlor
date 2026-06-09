import { createRouter, createWebHistory } from "vue-router";

import { installPermissionGuards } from "@/app/permissions/guards";
import MerchantLayout from "@/layouts/merchant/MerchantLayout.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: MerchantLayout,
      redirect: { name: "dashboard" },
      children: [
        {
          path: "dashboard",
          name: "dashboard",
          component: () => import("@/modules/merchant/views/DashboardView.vue"),
          meta: { title: "运营总览", roles: ["merchant_admin", "clerk", "support"] },
        },
        {
          path: "orders",
          name: "orders",
          component: () => import("@/modules/merchant/views/OrdersView.vue"),
          meta: { title: "订单管理", roles: ["merchant_admin", "clerk", "support"] },
        },
        {
          path: "members",
          name: "members",
          component: () => import("@/modules/merchant/views/MembersView.vue"),
          meta: { title: "会员运营", roles: ["merchant_admin", "support"] },
        },
        {
          path: "withdrawals",
          name: "withdrawals",
          component: () => import("@/modules/merchant/views/WithdrawalsView.vue"),
          meta: { title: "提现审核", roles: ["merchant_admin", "support"] },
        },
        {
          path: "exceptions",
          name: "exceptions",
          component: () => import("@/modules/merchant/views/ExceptionsView.vue"),
          meta: { title: "异常与审计", roles: ["merchant_admin", "support"] },
        },
        {
          path: "settings",
          name: "settings",
          component: () => import("@/modules/merchant/views/SettingsView.vue"),
          meta: { title: "连接设置" },
        },
      ],
    },
    {
      path: "/customer",
      component: () => import("@/layouts/customer/CustomerLayout.vue"),
      redirect: { name: "customer-stores" },
      children: [
        {
          path: "stores",
          name: "customer-stores",
          component: () => import("@/modules/customer/views/StoresView.vue"),
          meta: { title: "门店", roles: [] },
        },
        {
          path: "stores/:storeId",
          name: "customer-store-detail",
          component: () => import("@/modules/customer/views/StoreDetailView.vue"),
          meta: { title: "门店详情", roles: [] },
        },
        {
          path: "booking",
          name: "customer-booking",
          component: () => import("@/modules/customer/views/BookingView.vue"),
          meta: { title: "预约", roles: ["customer"] },
        },
        {
          path: "order-confirm",
          name: "customer-order-confirm",
          component: () => import("@/modules/customer/views/OrderConfirmView.vue"),
          meta: { title: "确认订单", roles: ["customer"] },
        },
        {
          path: "orders/:orderId",
          name: "customer-order-detail",
          component: () => import("@/modules/customer/views/OrderDetailView.vue"),
          meta: { title: "订单详情", roles: ["customer"] },
        },
        {
          path: "orders",
          name: "customer-orders",
          component: () => import("@/modules/customer/views/OrdersView.vue"),
          meta: { title: "我的订单", roles: ["customer"] },
        },
        {
          path: "me",
          name: "customer-me",
          component: () => import("@/modules/customer/views/MeView.vue"),
          meta: { title: "我的", roles: [] },
        },
      ],
    },
    {
      path: "/cleaner",
      component: () => import("@/layouts/cleaner/CleanerLayout.vue"),
      redirect: { name: "cleaner-tasks" },
      children: [
        {
          path: "tasks",
          name: "cleaner-tasks",
          component: () => import("@/modules/cleaner/views/TasksView.vue"),
          meta: { title: "保洁任务", roles: ["cleaner"] },
        },
        {
          path: "tasks/:taskId",
          name: "cleaner-task-detail",
          component: () => import("@/modules/cleaner/views/TaskDetailView.vue"),
          meta: { title: "任务详情", roles: ["cleaner"] },
        },
        {
          path: "me",
          name: "cleaner-me",
          component: () => import("@/modules/cleaner/views/CleanerMeView.vue"),
          meta: { title: "我的", roles: [] },
        },
      ],
    },
    {
      path: "/platform",
      component: () => import("@/layouts/platform/PlatformLayout.vue"),
      redirect: { name: "platform-tenants" },
      children: [
        {
          path: "tenants",
          name: "platform-tenants",
          component: () => import("@/modules/platform/views/TenantsView.vue"),
          meta: { title: "租户管理", roles: ["platform_admin"] },
        },
        {
          path: "tenants/:tenantId",
          name: "platform-tenant-detail",
          component: () => import("@/modules/platform/views/TenantDetailView.vue"),
          meta: { title: "租户详情", roles: ["platform_admin"] },
        },
        {
          path: "users",
          name: "platform-users",
          component: () => import("@/modules/platform/views/UsersView.vue"),
          meta: { title: "用户管理", roles: ["platform_admin"] },
        },
        {
          path: "devices",
          name: "platform-devices",
          component: () => import("@/modules/platform/views/DevicesView.vue"),
          meta: { title: "设备管理", roles: ["platform_admin"] },
        },
        {
          path: "exceptions",
          name: "platform-exceptions",
          component: () => import("@/modules/platform/views/ExceptionsView.vue"),
          meta: { title: "异常监控", roles: ["platform_admin"] },
        },
        {
          path: "audit",
          name: "platform-audit",
          component: () => import("@/modules/platform/views/AuditLogsView.vue"),
          meta: { title: "审计日志", roles: ["platform_admin"] },
        },
        {
          path: "settings",
          name: "platform-settings",
          component: () => import("@/modules/merchant/views/SettingsView.vue"),
          meta: { title: "连接设置" },
        },
      ],
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: { name: "dashboard" },
    },
  ],
});

installPermissionGuards(router);

export default router;
