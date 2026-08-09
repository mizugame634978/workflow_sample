import { describe, expect, it } from "vitest";

import {
  formatCurrency,
  formatDate,
  formatDateTime,
  formatFieldValue,
  formatLeadTime,
  formatRelative,
  initial,
} from "@/lib/format";

describe("formatDateTime", () => {
  it("renders UTC timestamps in Japan Standard Time", () => {
    expect(formatDateTime("2026-08-09T05:42:09Z")).toBe("2026/08/09 14:42");
  });

  it("returns a dash for missing values", () => {
    expect(formatDateTime(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
  });

  it("treats naive timestamps as UTC", () => {
    expect(formatDate("2026-08-09T05:42:09")).toBe("2026/08/09");
  });
});

describe("formatRelative", () => {
  const now = new Date("2026-08-09T12:00:00Z");

  it.each([
    ["2026-08-09T11:59:30Z", "たった今"],
    ["2026-08-09T11:45:00Z", "15分前"],
    ["2026-08-09T09:00:00Z", "3時間前"],
    ["2026-08-07T12:00:00Z", "2日前"],
  ])("renders %s as %s", (iso, expected) => {
    expect(formatRelative(iso, now)).toBe(expected);
  });

  it("falls back to an absolute date beyond a week", () => {
    expect(formatRelative("2026-07-01T12:00:00Z", now)).toBe("2026/07/01");
  });
});

describe("formatCurrency", () => {
  it("groups digits and prefixes the yen sign", () => {
    expect(formatCurrency(178000)).toBe("¥178,000");
  });

  it("accepts numeric strings", () => {
    expect(formatCurrency("12480")).toBe("¥12,480");
  });

  it("passes through values that are not numbers", () => {
    expect(formatCurrency("たくさん")).toBe("たくさん");
  });
});

describe("formatLeadTime", () => {
  it("uses hours below a day", () => {
    expect(formatLeadTime(5.4)).toBe("5.4時間");
  });

  it("switches to days beyond 24 hours", () => {
    expect(formatLeadTime(36)).toBe("1.5日");
  });

  it("shows a dash when there is no data", () => {
    expect(formatLeadTime(0)).toBe("—");
  });
});

describe("formatFieldValue", () => {
  it("formats numeric fields as currency when the label mentions money", () => {
    expect(formatFieldValue({ key: "amount", label: "金額（円）", type: "number" }, 5000)).toBe(
      "¥5,000",
    );
  });

  it("formats plain numbers with digit grouping", () => {
    expect(formatFieldValue({ key: "count", label: "数量", type: "number" }, 12000)).toBe("12,000");
  });

  it("formats date fields", () => {
    expect(formatFieldValue({ key: "d", label: "利用日", type: "date" }, "2026-08-09")).toBe(
      "2026/08/09",
    );
  });

  it("shows a dash for empty values", () => {
    expect(formatFieldValue({ key: "x", label: "備考", type: "text" }, "")).toBe("—");
  });
});

describe("initial", () => {
  it("takes the first character of the name", () => {
    expect(initial("田中 美咲")).toBe("田");
  });

  it("is safe with empty input", () => {
    expect(initial("")).toBe("?");
  });
});
