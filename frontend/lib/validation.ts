/** Client-side mirror of `backend/app/services/form_validation.py`.
 *
 * The server stays the authority; this exists so the user gets feedback before
 * a round trip. Both implementations are covered by their own test suites.
 */

import type { FormField } from "@/lib/types";

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

export type FormValues = Record<string, unknown>;
export type FormErrors = Record<string, string>;

export function validateForm(fields: FormField[], values: FormValues): FormErrors {
  const errors: FormErrors = {};

  for (const field of fields) {
    const value = values[field.key];

    if (isBlank(value)) {
      if (field.required) errors[field.key] = `${field.label}は必須項目です`;
      continue;
    }

    switch (field.type) {
      case "number": {
        const numeric = toNumber(value);
        if (numeric === null) {
          errors[field.key] = `${field.label}は数値で入力してください`;
        } else if (field.min != null && numeric < field.min) {
          errors[field.key] = `${field.label}は${field.min.toLocaleString("ja-JP")}以上で入力してください`;
        } else if (field.max != null && numeric > field.max) {
          errors[field.key] = `${field.label}は${field.max.toLocaleString("ja-JP")}以下で入力してください`;
        }
        break;
      }
      case "date":
        if (!isIsoDate(value)) {
          errors[field.key] = `${field.label}はYYYY-MM-DD形式で入力してください`;
        }
        break;
      case "select":
        if (!(field.options ?? []).includes(String(value))) {
          errors[field.key] = `${field.label}は選択肢から選んでください`;
        }
        break;
      default:
        if (field.max_length != null && String(value).length > field.max_length) {
          errors[field.key] = `${field.label}は${field.max_length}文字以内で入力してください`;
        }
    }
  }

  return errors;
}

export function isBlank(value: unknown): boolean {
  return value === null || value === undefined || (typeof value === "string" && !value.trim());
}

function toNumber(value: unknown): number | null {
  if (typeof value === "boolean") return null;
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "string") {
    const parsed = Number(value.replace(/,/g, "").trim());
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function isIsoDate(value: unknown): boolean {
  if (typeof value !== "string" || !ISO_DATE.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().startsWith(value);
}
