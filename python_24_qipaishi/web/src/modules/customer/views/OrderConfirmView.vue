<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useSessionStore } from "@/app/stores/session";
import { ApiError } from "@/core/api/client";
import { customerApi } from "@/core/api/customer";
import { demoCustomerOrders, demoCoupons, demoPayment } from "@/core/api/demo";
import type { OrderSummary, CouponInfo } from "@/core/api/types";
import { formatMoney } from "@/shared/utils/format";

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const orderId = (route.query.orderId as string) ?? "";

const order = ref<OrderSummary | null>(null);
const coupons = ref<CouponInfo[]>(demoCoupons);
const loading = ref(false);
const error = ref("");
const paying = ref(false);
const payError = ref("");
const selectedCouponId = ref("");

const totalAmount = computed(() =>
  order.value ? formatMoney(order.value.total_amount) : "¥0.00",
);
const payableAmount = computed(() =>
  order.value ? formatMoney(order.value.payable_amount) : "¥0.00",
);
const selectedCoupon = computed(() =>
  coupons.value.find((c) => c.id === selectedCouponId.value),
);
const finalPayable = computed(() => {
  if (!order.value) return "¥0.00";
  const base = Number(order.value.payable_amount);
  if (selectedCoupon.value) {
    return formatMoney(Math.max(0, base - Number(selectedCoupon.value.amount)));
  }
  return payableAmount.value;
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    if (session.isConnected) {
      const [o, c] = await Promise.all([
        customerApi.getOrder(orderId),
        customerApi.getMyCoupons().catch(() => [] as CouponInfo[]),
      ]);
      order.value = o;
      if (c.length > 0) coupons.value = c;
    } else {
      order.value = demoCustomerOrders[0] ?? null;
    }
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

function selectCoupon(id: string) {
  selectedCouponId.value = selectedCouponId.value === id ? "" : id;
}

async function doWechatPay() {
  paying.value = true;
  payError.value = "";
  try {
    let pay: { id: string };
    if (session.isConnected) {
      pay = await customerApi.wechatPrepay(orderId);
      // Simulate payment callback
      await customerApi.mockPayCallback(pay.id);
    } else {
      pay = demoPayment;
    }
    router.replace({
      name: "customer-order-detail",
      params: { orderId },
    });
  } catch (e) {
    payError.value = e instanceof ApiError ? e.message : "支付失败";
  } finally {
    paying.value = false;
  }
}

async function doBalancePay() {
  paying.value = true;
  payError.value = "";
  try {
    // For balance pay, just call createOrder which completes from wallet
    router.replace({
      name: "customer-order-detail",
      params: { orderId },
    });
  } catch (e) {
    payError.value = e instanceof ApiError ? e.message : "支付失败";
  } finally {
    paying.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="page-stack">
    <div v-if="loading" class="muted" style="text-align:center;padding:20px">加载中...</div>
    <div v-else-if="error" class="alert">{{ error }}</div>
    <template v-else-if="order">
      <!-- Order summary -->
      <div class="panel" style="min-height:auto">
        <h3 style="margin-bottom:10px">订单确认</h3>
        <dl class="detail-list">
          <dt>订单号</dt><dd>{{ order.order_no }}</dd>
          <dt>总金额</dt><dd><strong>{{ totalAmount }}</strong></dd>
          <dt>应付金额</dt><dd><strong style="color:var(--brand);font-size:20px">{{ payableAmount }}</strong></dd>
        </dl>
      </div>

      <!-- Coupons -->
      <div v-if="coupons.length > 0" class="panel" style="min-height:auto">
        <h3 style="margin-bottom:8px">可用优惠券</h3>
        <div class="coupon-list">
          <div
            v-for="c in coupons"
            :key="c.id"
            :class="['coupon-item', { selected: c.id === selectedCouponId }]"
            @click="selectCoupon(c.id)"
          >
            <div class="coupon-amount">
              <strong>¥{{ c.amount }}</strong>
              <small>满{{ c.min_order_amount ?? "0" }}可用</small>
            </div>
            <div class="coupon-info">
              <span>{{ c.name ?? "优惠券" }}</span>
              <small v-if="c.expires_at">有效期至 {{ new Date(c.expires_at).toLocaleDateString("zh-CN") }}</small>
            </div>
            <span v-if="c.id === selectedCouponId" class="coupon-check">✓</span>
          </div>
        </div>
        <div v-if="selectedCoupon" class="notice-line" style="margin-top:8px">
          使用「{{ selectedCoupon.name }}」抵扣 ¥{{ selectedCoupon.amount }}，实付 {{ finalPayable }}
        </div>
      </div>

      <!-- Payment -->
      <div v-if="payError" class="alert">{{ payError }}</div>
      <div class="pay-actions">
        <button
          class="secondary"
          style="flex:1;height:50px;font-size:15px"
          :disabled="paying"
          @click="doBalancePay"
        >
          💰 余额支付
        </button>
        <button
          style="flex:1;height:50px;font-size:15px"
          :disabled="paying"
          @click="doWechatPay"
        >
          {{ paying ? "支付中..." : "💳 微信支付" }}
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.coupon-list {
  display: grid;
  gap: 8px;
}

.coupon-item {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 10px;
  border: 2px solid var(--line);
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 120ms;
}

.coupon-item.selected {
  border-color: var(--brand);
  background: #f0faf8;
}

.coupon-amount {
  text-align: center;
  min-width: 56px;
}

.coupon-amount strong {
  font-size: 18px;
  color: var(--brand);
  display: block;
}

.coupon-amount small {
  font-size: 11px;
}

.coupon-info {
  flex: 1;
  min-width: 0;
}

.coupon-info span {
  display: block;
  font-size: 14px;
}

.coupon-check {
  font-size: 20px;
  color: var(--brand);
  font-weight: 800;
}

.pay-actions {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}
</style>
