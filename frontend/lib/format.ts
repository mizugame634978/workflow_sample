/** Presentation helpers. All dates are shown in Japan Standard Time. */

import type { FormField } from "@/lib/types";

const TIME_ZONE = "Asia/Tokyo";
const DASH = "—";

/** The API always returns UTC; older clients may omit the trailing Z. */
function parse(value: string | null | undefined): Date | null {
  if (!value) return null;
  const normalised = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value) ? value : `${value}Z`;
  const date = new Date(normalised);
  return Number.isNaN(date.getTime()) ? null : date;
}

function parts(date: Date) {
  const formatter = new Intl.DateTimeFormat("ja-JP", {
    timeZone: TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  return Object.fromEntries(formatter.formatToParts(date).map((p) => [p.type, p.value]));
}

export function formatDate(value: string | null | undefined): string {
  const date = parse(value);
  if (!date) return DASH;
  const p = parts(date);
  return `${p.year}/${p.month}/${p.day}`;
}

export function formatDateTime(value: string | null | undefined): string {
  const date = parse(value);
  if (!date) return DASH;
  const p = parts(date);
  return `${p.year}/${p.month}/${p.day} ${p.hour}:${p.minute}`;
}

export function formatRelative(value: string | null | undefined, now: Date = new Date()): string {
  const date = parse(value);
  if (!date) return DASH;

  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (seconds < 60) return "たった今";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}時間前`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}日前`;
  return formatDate(value);
}

export function formatNumber(value: unknown): string {
  const numeric = toNumber(value);
  return numeric === null ? String(value ?? DASH) : numeric.toLocaleString("ja-JP");
}

export function formatCurrency(value: unknown): string {
  const numeric = toNumber(value);
  return numeric === null ? String(value ?? DASH) : `¥${numeric.toLocaleString("ja-JP")}`;
}

export function formatLeadTime(hours: number): string {
  if (!hours || hours <= 0) return DASH;
  if (hours < 24) return `${round(hours)}時間`;
  return `${round(hours / 24)}日`;
}

export function formatFieldValue(field: FormField, value: unknown): string {
  if (value === null || value === undefined || value === "") return DASH;
  if (field.type === "number") {
    return isMonetary(field.label) ? formatCurrency(value) : formatNumber(value);
  }
  if (field.type === "date") return formatDate(`${value}T00:00:00Z`);
  return String(value);
}

export function initial(name: string): string {
  return name.trim().charAt(0) || "?";
}

export function pluralJa(count: number, unit: string): string {
  return `${count.toLocaleString("ja-JP")}${unit}`;
}

function isMonetary(label: string): boolean {
  return /円|金額|費用|予算|価格/.test(label);
}

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value.replace(/,/g, ""));
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function round(value: number): string {
  return (Math.round(value * 10) / 10).toString();
}
