"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { ClientApiError, call } from "@/lib/client";
import type { ApproverType, FieldType, FormField, TemplateDetail, UserRef } from "@/lib/types";

interface StepDraft {
  name: string;
  approver_type: ApproverType;
  approver_user_id: number | null;
  approver_role: "admin" | "member" | null;
}

const FIELD_TYPES: { value: FieldType; label: string }[] = [
  { value: "text", label: "1行テキスト" },
  { value: "textarea", label: "複数行テキスト" },
  { value: "number", label: "数値" },
  { value: "date", label: "日付" },
  { value: "select", label: "選択肢" },
];

export function TemplateEditor({
  users,
  template,
}: {
  users: UserRef[];
  template?: TemplateDetail;
}) {
  const router = useRouter();
  const isEdit = Boolean(template);

  const [code, setCode] = useState(template?.code ?? "");
  const [name, setName] = useState(template?.name ?? "");
  const [category, setCategory] = useState(template?.category ?? "総務");
  const [description, setDescription] = useState(template?.description ?? "");
  const [fields, setFields] = useState<FormField[]>(template?.form_fields ?? []);
  const [steps, setSteps] = useState<StepDraft[]>(
    template?.steps.map((step) => ({
      name: step.name,
      approver_type: step.approver_type,
      approver_user_id: step.approver?.id ?? null,
      approver_role: step.approver_role,
    })) ?? [{ name: "上長承認", approver_type: "manager", approver_user_id: null, approver_role: null }],
  );
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function patchField(index: number, patch: Partial<FormField>) {
    setFields((current) =>
      current.map((field, i) => (i === index ? { ...field, ...patch } : field)),
    );
  }

  function patchStep(index: number, patch: Partial<StepDraft>) {
    setSteps((current) => current.map((step, i) => (i === index ? { ...step, ...patch } : step)));
  }

  function move<T>(list: T[], index: number, delta: number): T[] {
    const target = index + delta;
    if (target < 0 || target >= list.length) return list;
    const copy = [...list];
    [copy[index], copy[target]] = [copy[target], copy[index]];
    return copy;
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);

    const payload = {
      code: code.trim().toUpperCase(),
      name: name.trim(),
      description: description.trim(),
      category: category.trim(),
      form_fields: fields.map((field) => ({
        ...field,
        options: field.type === "select" ? (field.options ?? []) : [],
      })),
      steps: steps.map((step) => ({
        name: step.name.trim(),
        approver_type: step.approver_type,
        approver_user_id: step.approver_type === "user" ? step.approver_user_id : null,
        approver_role: step.approver_type === "role" ? (step.approver_role ?? "admin") : null,
      })),
    };

    try {
      if (isEdit && template) {
        const { code: _code, ...rest } = payload;
        await call(`templates/${template.id}`, { method: "PATCH", body: JSON.stringify(rest) });
        router.push("/templates");
      } else {
        await call("templates", { method: "POST", body: JSON.stringify(payload) });
        router.push("/templates");
      }
      router.refresh();
    } catch (caught) {
      setError(caught instanceof ClientApiError ? caught.message : "保存できませんでした");
      setPending(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={save} noValidate>
      {error ? (
        <p role="alert" data-testid="template-error" className="rounded-lg bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700">
          {error}
        </p>
      ) : null}

      <section className="card p-5">
        <h2 className="mb-4 text-sm font-semibold text-slate-900">基本情報</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="フォームコード" htmlFor="code" required hint="英大文字・数字・アンダースコア">
            <input
              id="code"
              className="input font-mono"
              value={code}
              disabled={isEdit}
              placeholder="EXPENSE"
              onChange={(event) => setCode(event.target.value.toUpperCase())}
            />
          </Field>
          <Field label="フォーム名" htmlFor="name" required>
            <input
              id="name"
              className="input"
              value={name}
              placeholder="経費精算申請"
              onChange={(event) => setName(event.target.value)}
            />
          </Field>
          <Field label="カテゴリ" htmlFor="category">
            <input
              id="category"
              className="input"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            />
          </Field>
          <div className="sm:col-span-2">
            <Field label="説明" htmlFor="description">
              <textarea
                id="description"
                className="input"
                rows={2}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
              />
            </Field>
          </div>
        </div>
      </section>

      <section className="card p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">入力項目</h2>
          <Button
            type="button"
            size="sm"
            variant="secondary"
            data-testid="add-field"
            onClick={() =>
              setFields((current) => [
                ...current,
                {
                  key: `field_${current.length + 1}`,
                  label: "",
                  type: "text",
                  required: false,
                  options: [],
                },
              ])
            }
          >
            項目を追加
          </Button>
        </div>

        {fields.length === 0 ? (
          <p className="py-6 text-center text-sm text-slate-500">
            入力項目がありません。「項目を追加」から作成してください。
          </p>
        ) : (
          <ul className="space-y-3">
            {fields.map((field, index) => (
              <li key={index} data-testid="field-row" className="rounded-lg border border-slate-200 p-3">
                <div className="grid gap-3 sm:grid-cols-12">
                  <div className="sm:col-span-4">
                    <label className="label text-xs" htmlFor={`field-label-${index}`}>
                      項目名
                    </label>
                    <input
                      id={`field-label-${index}`}
                      className="input"
                      value={field.label}
                      placeholder="金額（円）"
                      onChange={(event) => patchField(index, { label: event.target.value })}
                    />
                  </div>
                  <div className="sm:col-span-3">
                    <label className="label text-xs" htmlFor={`field-key-${index}`}>
                      キー
                    </label>
                    <input
                      id={`field-key-${index}`}
                      className="input font-mono text-xs"
                      value={field.key}
                      onChange={(event) => patchField(index, { key: event.target.value })}
                    />
                  </div>
                  <div className="sm:col-span-3">
                    <label className="label text-xs" htmlFor={`field-type-${index}`}>
                      種別
                    </label>
                    <select
                      id={`field-type-${index}`}
                      className="input"
                      value={field.type}
                      onChange={(event) =>
                        patchField(index, { type: event.target.value as FieldType })
                      }
                    >
                      {FIELD_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end gap-2 sm:col-span-2">
                    <label className="flex items-center gap-1.5 text-xs text-slate-600">
                      <input
                        type="checkbox"
                        className="size-4 rounded border-slate-300"
                        checked={Boolean(field.required)}
                        onChange={(event) => patchField(index, { required: event.target.checked })}
                      />
                      必須
                    </label>
                    <button
                      type="button"
                      className="ml-auto text-xs text-rose-600 hover:underline"
                      onClick={() => setFields((current) => current.filter((_, i) => i !== index))}
                    >
                      削除
                    </button>
                  </div>
                  {field.type === "select" ? (
                    <div className="sm:col-span-12">
                      <label className="label text-xs" htmlFor={`field-options-${index}`}>
                        選択肢（カンマ区切り）
                      </label>
                      <input
                        id={`field-options-${index}`}
                        className="input"
                        value={(field.options ?? []).join(",")}
                        placeholder="交通費,接待交際費,消耗品費"
                        onChange={(event) =>
                          patchField(index, {
                            options: event.target.value
                              .split(",")
                              .map((option) => option.trim())
                              .filter(Boolean),
                          })
                        }
                      />
                    </div>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">承認ルート</h2>
          <Button
            type="button"
            size="sm"
            variant="secondary"
            data-testid="add-step"
            onClick={() =>
              setSteps((current) => [
                ...current,
                {
                  name: `承認ステップ${current.length + 1}`,
                  approver_type: "manager",
                  approver_user_id: null,
                  approver_role: null,
                },
              ])
            }
          >
            ステップを追加
          </Button>
        </div>

        <ul className="space-y-3">
          {steps.map((step, index) => (
            <li key={index} data-testid="step-row" className="rounded-lg border border-slate-200 p-3">
              <div className="grid gap-3 sm:grid-cols-12">
                <div className="sm:col-span-1">
                  <span className="grid size-8 place-items-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                    {index + 1}
                  </span>
                </div>
                <div className="sm:col-span-3">
                  <label className="label text-xs" htmlFor={`step-name-${index}`}>
                    ステップ名
                  </label>
                  <input
                    id={`step-name-${index}`}
                    className="input"
                    value={step.name}
                    onChange={(event) => patchStep(index, { name: event.target.value })}
                  />
                </div>
                <div className="sm:col-span-3">
                  <label className="label text-xs" htmlFor={`step-type-${index}`}>
                    承認者の決め方
                  </label>
                  <select
                    id={`step-type-${index}`}
                    className="input"
                    value={step.approver_type}
                    onChange={(event) =>
                      patchStep(index, { approver_type: event.target.value as ApproverType })
                    }
                  >
                    <option value="manager">申請者の上長</option>
                    <option value="user">個人を指定</option>
                    <option value="role">権限で指定</option>
                  </select>
                </div>
                <div className="sm:col-span-3">
                  {step.approver_type === "user" ? (
                    <>
                      <label className="label text-xs" htmlFor={`step-approver-${index}`}>
                        承認者
                      </label>
                      <select
                        id={`step-approver-${index}`}
                        className="input"
                        value={step.approver_user_id ?? ""}
                        onChange={(event) =>
                          patchStep(index, { approver_user_id: Number(event.target.value) || null })
                        }
                      >
                        <option value="">選択してください</option>
                        {users.map((user) => (
                          <option key={user.id} value={user.id}>
                            {user.name}（{user.department}）
                          </option>
                        ))}
                      </select>
                    </>
                  ) : step.approver_type === "role" ? (
                    <>
                      <label className="label text-xs" htmlFor={`step-role-${index}`}>
                        権限
                      </label>
                      <select
                        id={`step-role-${index}`}
                        className="input"
                        value={step.approver_role ?? "admin"}
                        onChange={(event) =>
                          patchStep(index, {
                            approver_role: event.target.value as "admin" | "member",
                          })
                        }
                      >
                        <option value="admin">管理者</option>
                        <option value="member">一般</option>
                      </select>
                    </>
                  ) : (
                    <p className="mt-6 text-xs text-slate-500">申請者の上長が自動的に設定されます</p>
                  )}
                </div>
                <div className="flex items-end justify-end gap-2 sm:col-span-2">
                  <button
                    type="button"
                    aria-label="上へ"
                    className="rounded px-1.5 py-1 text-xs text-slate-500 hover:bg-slate-100"
                    onClick={() => setSteps((current) => move(current, index, -1))}
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    aria-label="下へ"
                    className="rounded px-1.5 py-1 text-xs text-slate-500 hover:bg-slate-100"
                    onClick={() => setSteps((current) => move(current, index, 1))}
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    className="pb-1 text-xs whitespace-nowrap text-rose-600 hover:underline"
                    onClick={() => setSteps((current) => current.filter((_, i) => i !== index))}
                  >
                    削除
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <div className="flex items-center gap-2">
        <Button type="submit" data-testid="save-template" disabled={pending}>
          {pending ? "保存しています…" : isEdit ? "変更を保存" : "フォームを作成"}
        </Button>
        <Button type="button" variant="secondary" onClick={() => router.push("/templates")}>
          キャンセル
        </Button>
      </div>
    </form>
  );
}
