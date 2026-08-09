import { describe, expect, it } from "vitest";

import { validateForm } from "@/lib/validation";
import type { FormField } from "@/lib/types";

const fields: FormField[] = [
  { key: "amount", label: "金額", type: "number", required: true, min: 1 },
  { key: "purpose", label: "利用目的", type: "textarea", required: true },
  { key: "expense_date", label: "利用日", type: "date", required: true },
  { key: "category", label: "費目", type: "select", required: true, options: ["交通費", "消耗品費"] },
  { key: "memo", label: "備考", type: "text", required: false, max_length: 5 },
];

const valid = {
  amount: 1200,
  purpose: "顧客訪問",
  expense_date: "2026-08-09",
  category: "交通費",
};

describe("validateForm", () => {
  it("accepts a complete payload", () => {
    expect(validateForm(fields, valid)).toEqual({});
  });

  it("reports every missing required field", () => {
    expect(Object.keys(validateForm(fields, {})).sort()).toEqual([
      "amount",
      "category",
      "expense_date",
      "purpose",
    ]);
  });

  it("treats whitespace as empty", () => {
    expect(validateForm(fields, { ...valid, purpose: "   " })).toHaveProperty("purpose");
  });

  it("rejects non numeric input for number fields", () => {
    expect(validateForm(fields, { ...valid, amount: "たくさん" }).amount).toContain("数値");
  });

  it("enforces a minimum", () => {
    expect(validateForm(fields, { ...valid, amount: 0 })).toHaveProperty("amount");
  });

  it("rejects malformed dates", () => {
    expect(validateForm(fields, { ...valid, expense_date: "2026/08/09" })).toHaveProperty(
      "expense_date",
    );
  });

  it("rejects values outside the option list", () => {
    expect(validateForm(fields, { ...valid, category: "宇宙旅行" })).toHaveProperty("category");
  });

  it("enforces the maximum length of optional text", () => {
    expect(validateForm(fields, { ...valid, memo: "123456" })).toHaveProperty("memo");
  });

  it("ignores optional fields that are left blank", () => {
    expect(validateForm(fields, { ...valid, memo: "" })).toEqual({});
  });
});
