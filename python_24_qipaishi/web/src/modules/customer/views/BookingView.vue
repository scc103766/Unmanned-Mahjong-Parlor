<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useSessionStore } from "@/app/stores/session";
import { ApiError } from "@/core/api/client";
import { customerApi } from "@/core/api/customer";
import { demoPriceQuote, demoPreorder } from "@/core/api/demo";
import type { PriceQuote, PreorderResult } from "@/core/api/types";
import { formatMoney, addHours } from "@/shared/utils/format";

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const storeId = (route.query.storeId as string) ?? "";
const roomId = (route.query.roomId as string) ?? "";

const now = new Date();
const today = now.toISOString().slice(0, 10);
const tomorrow = new Date(now.getTime() + 86400000).toISOString().slice(0, 10);

const dateOptions = [
  { value: today, label: "今天" },
  { value: tomorrow, label: "明天" },
];

const hourOptions = Array.from({ length: 15 }, (_, i) => {
  const h = i + 9;
  return { value: `${h.toString().padStart(2, "0")}:00`, label: `${h}:00` };
});

const durationOptions = [
  { value: 2, label: "2 小时" },
  { value: 4, label: "4 小时" },
  { value: 6, label: "6 小时" },
  { value: 8, label: "通宵 (8小时)" },
];

const selectedDate = ref(today);
const selectedHour = ref("14:00");
const selectedDuration = ref(4);

const quote = ref<PriceQuote | null>(null);
const quoteLoading = ref(false);
const quoteError = ref("");
const bookingLoading = ref(false);
const bookingError = ref("");

const startAt = computed(() => `${selectedDate.value}T${selectedHour.value}:00`);
const endAt = computed(() => {
  const d = new Date(selectedDate.value + "T" + selectedHour.value + ":00");
  return new Date(d.getTime() + selectedDuration.value * 3600000).toISOString();
});

function durationLabel(h: number): string {
  return h >= 8 ? "通宵" : `${h} 小时`;
}

async function doQuote() {
  quoteLoading.value = true;
  quoteError.value = "";
  quote.value = null;
  try {
    if (session.isConnected) {
      const result = await customerApi.quotePrice(roomId, startAt.value, endAt.value);
      quote.value = result;
    } else {
      quote.value = demoPriceQuote;
    }
  } catch (e) {
    quoteError.value = e instanceof ApiError ? e.message : "试算失败";
  } finally {
    quoteLoading.value = false;
  }
}

async function doBook() {
  bookingLoading.value = true;
  bookingError.value = "";
  try {
    let result: PreorderResult;
    if (session.isConnected) {
      result = await customerApi.createPreorder(roomId, startAt.value, endAt.value);
    } else {
      result = demoPreorder;
    }
    router.push({
      name: "customer-order-confirm",
      query: { orderId: result.order_id },
    });
  } catch (e) {
    bookingError.value = e instanceof ApiError ? e.message : "预订失败";
  } finally {
    bookingLoading.value = false;
  }
}

onMounted(() => {
  doQuote();
});
</script>

<template>
  <div class="page-stack">
    <!-- Date -->
    <div class="booking-group">
      <label>选择日期</label>
      <div class="chip-row">
        <button
          v-for="d in dateOptions"
          :key="d.value"
          :class="['mini', selectedDate === d.value ? '' : 'ghost']"
          @click="selectedDate = d.value; doQuote()"
        >
          {{ d.label }}
        </button>
      </div>
    </div>

    <!-- Start time -->
    <div class="booking-group">
      <label>开始时间</label>
      <div class="chip-row" style="flex-wrap:wrap">
        <button
          v-for="h in hourOptions"
          :key="h.value"
          :class="['mini', selectedHour === h.value ? '' : 'ghost']"
          @click="selectedHour = h.value; doQuote()"
        >
          {{ h.label }}
        </button>
      </div>
    </div>

    <!-- Duration -->
    <div class="booking-group">
      <label>消费时长</label>
      <div class="chip-row">
        <button
          v-for="d in durationOptions"
          :key="d.value"
          :class="['mini', selectedDuration === d.value ? '' : 'ghost']"
          @click="selectedDuration = d.value; doQuote()"
        >
          {{ d.label }}
        </button>
      </div>
    </div>

    <!-- Quote -->
    <div v-if="quoteLoading" class="muted" style="text-align:center;padding:12px">计算价格中...</div>
    <div v-else-if="quoteError" class="alert">{{ quoteError }}</div>
    <div v-else-if="quote" class="panel quote-panel">
      <div class="quote-summary">
        <span class="muted">{{ selectedDate }} {{ selectedHour }} · {{ durationLabel(selectedDuration) }}</span>
        <strong>{{ formatMoney(quote.total_amount) }}</strong>
      </div>
      <div v-if="quote.details.length > 0" class="quote-details">
        <div v-for="(d, i) in quote.details" :key="i" class="quote-row">
          <span>{{ (d as Record<string, unknown>).item ?? (d as Record<string, unknown>).description }}</span>
          <span>{{ formatMoney((d as Record<string, unknown>).amount as string | number) }}</span>
        </div>
      </div>
      <div class="quote-row quote-total">
        <span>合计</span>
        <strong>{{ formatMoney(quote.total_amount) }}</strong>
      </div>
    </div>

    <!-- Actions -->
    <div v-if="bookingError" class="alert">{{ bookingError }}</div>
    <button
      :disabled="quoteLoading || bookingLoading || !!quoteError"
      @click="doBook"
      style="height:48px;font-size:16px;margin-top:4px"
    >
      {{ bookingLoading ? "提交中..." : "立即预订" }}
    </button>
  </div>
</template>

<style scoped>
.booking-group {
  display: grid;
  gap: 8px;
  margin-bottom: 4px;
}

.booking-group label {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.chip-row {
  display: flex;
  gap: 8px;
}

.chip-row button {
  flex: 1;
}

.quote-panel {
  min-height: auto;
}

.quote-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--line);
}

.quote-summary strong {
  font-size: 24px;
  color: var(--brand);
}

.quote-details {
  padding-top: 8px;
  display: grid;
  gap: 6px;
}

.quote-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.quote-total {
  padding-top: 8px;
  margin-top: 4px;
  border-top: 1px solid var(--line);
}
</style>
