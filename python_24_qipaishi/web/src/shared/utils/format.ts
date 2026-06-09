import type { MoneyLike } from "@/core/api/types";

const moneyFormatter = new Intl.NumberFormat("zh-CN", {
  style: "currency",
  currency: "CNY",
  maximumFractionDigits: 2,
});

const numberFormatter = new Intl.NumberFormat("zh-CN", {
  maximumFractionDigits: 2,
});

export function toNumber(value: MoneyLike | null | undefined): number {
  if (value === null || value === undefined || value === "") {
    return 0;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatMoney(value: MoneyLike | null | undefined): string {
  return moneyFormatter.format(toNumber(value));
}

export function formatNumber(value: MoneyLike | null | undefined): string {
  return numberFormatter.format(toNumber(value));
}

export function formatPercent(value: MoneyLike | null | undefined): string {
  const raw = toNumber(value);
  const normalized = raw > 1 ? raw : raw * 100;
  return `${numberFormatter.format(normalized)}%`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function toDateTimeInputValue(value: Date): string {
  const offset = value.getTimezoneOffset();
  const local = new Date(value.getTime() - offset * 60_000);
  return local.toISOString().slice(0, 16);
}

export function addHours(base: Date, hours: number): Date {
  return new Date(base.getTime() + hours * 60 * 60 * 1000);
}

export function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending_payment: "待支付",
    paid: "已支付",
    in_use: "使用中",
    completed: "已完成",
    cancelled: "已取消",
    pending: "待处理",
    approved: "已审核",
    rejected: "已驳回",
    paid_out: "已打款",
    active: "正常",
    disabled: "停用",
    open: "未处理",
    closed: "已关闭",
    failed: "失败",
    succeeded: "成功",
  };
  return labels[status] ?? status;
}

export function statusTone(status: string): "good" | "warn" | "bad" | "neutral" {
  if (["completed", "paid_out", "succeeded", "active", "closed"].includes(status)) {
    return "good";
  }
  if (["pending", "pending_payment", "paid", "in_use", "approved", "open"].includes(status)) {
    return "warn";
  }
  if (["cancelled", "rejected", "failed", "disabled"].includes(status)) {
    return "bad";
  }
  return "neutral";
}

export function severityLabel(severity: string): string {
  const labels: Record<string, string> = {
    critical: "严重",
    high: "高",
    medium: "中",
    low: "低",
  };
  return labels[severity] ?? severity;
}

export function sourceLabel(source: string): string {
  const labels: Record<string, string> = {
    payment: "支付",
    refund: "退款",
    withdrawal: "提现",
    device: "设备",
    cleaning: "保洁",
  };
  return labels[source] ?? source;
}
