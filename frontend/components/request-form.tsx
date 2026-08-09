"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { ClientApiError, call } from "@/lib/client";
import type { FormField, RequestDetail, TemplateDetail } from "@/lib/types";
import { validateForm, type FormErrors, type FormValues } from "@/lib/validation";

export function RequestForm({
  template,
  requestId,
  initialTitle = "",
  initialValues = {},
}: {
  template: Pick<TemplateDetail, "id" | "name" | "form_fields">;
  requestId?: number;
  initialTitle?: string;
  initialValues?: FormValues;
}) {
  const router = useRouter();
  const [title, setTitle] = useState(initialTitle);
  const [values, setValues] = useState<FormValues>(initialValues);
  const [errors, setErrors] = useState<FormErrors>({});
  const [message, setMessage] = useState<string | null>(null);
  const [pending, setPending] = useState<"draft" | "submit" | null>(null);

  function update(key: string, value: unknown) {
    setValues((current) => ({ ...current, [key]: value }));
    setErrors((current) => {
      if (!current[key]) return current;
      const { [key]: _removed, ...rest } = current;
      return rest;
    });
  }

  async function save(mode: "draft" | "submit") {
    setMessage(null);

    const nextErrors: FormErrors = {};
    if (!title.trim()) nextErrors.title = "件名は必須項目です";
    if (mode === "submit") Object.assign(nextErrors, validateForm(template.form_fields, values));
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      setMessage("入力内容を確認してください。");
      return;
    }

    setPending(mode);
    try {
      const payload = { title: title.trim(), form_data: values };
      const detail = requestId
        ? await call<RequestDetail>(`requests/${requestId}`, {
            method: "PATCH",
            body: JSON.stringify(payload),
          })
        : await call<RequestDetail>("requests", {
            method: "POST",
            body: JSON.stringify({ ...payload, template_id: template.id, submit: false }),
          });

      if (mode === "submit") {
        await call<RequestDetail>(`requests/${detail.id}/submit`, { method: "POST" });
      }
      router.push(`/requests/${detail.id}`);
      router.refresh();
    } catch (error) {
      if (error instanceof ClientApiError) {
        setErrors(error.fieldErrors);
        setMessage(error.message);
      } else {
        setMessage("保存できませんでした。時間をおいて再度お試しください。");
      }
      setPending(null);
    }
  }

  return (
    <form
      className="space-y-5"
      onSubmit={(event) => {
        event.preventDefault();
        void save("submit");
      }}
      noValidate
    >
      {message ? (
        <p
          role="alert"
          data-testid="form-error"
          className="rounded-lg bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700 ring-1 ring-rose-200 ring-inset"
        >
          {message}
        </p>
      ) : null}

      <Field label="件名" htmlFor="title" required error={errors.title}>
        <input
          id="title"
          name="title"
          className="input"
          value={title}
          placeholder="例）10月度 交通費精算"
          onChange={(event) => setTitle(event.target.value)}
        />
      </Field>

      {template.form_fields.map((field) => (
        <DynamicField
          key={field.key}
          field={field}
          value={values[field.key]}
          error={errors[field.key]}
          onChange={(value) => update(field.key, value)}
        />
      ))}

      <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-5">
        <Button type="submit" data-testid="submit-request" disabled={pending !== null}>
          {pending === "submit" ? "提出しています…" : "この内容で申請する"}
        </Button>
        <Button
          type="button"
          variant="secondary"
          data-testid="save-draft"
          disabled={pending !== null}
          onClick={() => void save("draft")}
        >
          下書き保存
        </Button>
        <button
          type="button"
          className="ml-auto text-sm text-slate-500 hover:text-slate-700 hover:underline"
          onClick={() => router.back()}
        >
          キャンセル
        </button>
      </div>
    </form>
  );
}

function DynamicField({
  field,
  value,
  error,
  onChange,
}: {
  field: FormField;
  value: unknown;
  error?: string;
  onChange: (value: unknown) => void;
}) {
  const id = `field-${field.key}`;
  const common = {
    id,
    name: field.key,
    className: "input",
    "aria-invalid": error ? true : undefined,
  };

  return (
    <Field
      label={field.label}
      htmlFor={id}
      required={field.required}
      hint={field.help_text}
      error={error}
    >
      {field.type === "textarea" ? (
        <textarea
          {...common}
          rows={4}
          placeholder={field.placeholder}
          value={String(value ?? "")}
          onChange={(event) => onChange(event.target.value)}
        />
      ) : field.type === "select" ? (
        <select {...common} value={String(value ?? "")} onChange={(e) => onChange(e.target.value)}>
          <option value="">選択してください</option>
          {(field.options ?? []).map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      ) : (
        <input
          {...common}
          type={field.type === "number" ? "number" : field.type === "date" ? "date" : "text"}
          placeholder={field.placeholder}
          value={String(value ?? "")}
          onChange={(event) =>
            onChange(
              field.type === "number"
                ? event.target.value === ""
                  ? ""
                  : Number(event.target.value)
                : event.target.value,
            )
          }
        />
      )}
    </Field>
  );
}
