"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { ClientApiError, call } from "@/lib/client";
import type { User } from "@/lib/types";

const EMPTY = {
  email: "",
  name: "",
  password: "",
  department: "",
  job_title: "",
  role: "member" as "member" | "admin",
  manager_id: "" as string,
};

export function UserInviteForm({ users }: { users: User[] }) {
  const router = useRouter();
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [pending, setPending] = useState(false);

  function set<K extends keyof typeof EMPTY>(key: K, value: (typeof EMPTY)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setDone(false);
    try {
      await call("users", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          manager_id: form.manager_id ? Number(form.manager_id) : null,
        }),
      });
      setForm(EMPTY);
      setDone(true);
      router.refresh();
    } catch (caught) {
      setError(caught instanceof ClientApiError ? caught.message : "登録できませんでした");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="mt-4 space-y-3" onSubmit={submit} noValidate>
      {error ? (
        <p role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </p>
      ) : null}
      {done ? (
        <p data-testid="invite-success" className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          ユーザーを登録しました
        </p>
      ) : null}

      <Field label="氏名" htmlFor="new-name" required>
        <input
          id="new-name"
          className="input"
          value={form.name}
          onChange={(event) => set("name", event.target.value)}
        />
      </Field>
      <Field label="メールアドレス" htmlFor="new-email" required>
        <input
          id="new-email"
          type="email"
          className="input"
          value={form.email}
          onChange={(event) => set("email", event.target.value)}
        />
      </Field>
      <Field label="初期パスワード" htmlFor="new-password" required hint="8文字以上">
        <input
          id="new-password"
          type="password"
          className="input"
          value={form.password}
          onChange={(event) => set("password", event.target.value)}
        />
      </Field>
      <Field label="部署" htmlFor="new-department">
        <input
          id="new-department"
          className="input"
          value={form.department}
          onChange={(event) => set("department", event.target.value)}
        />
      </Field>
      <Field label="上長" htmlFor="new-manager">
        <select
          id="new-manager"
          className="input"
          value={form.manager_id}
          onChange={(event) => set("manager_id", event.target.value)}
        >
          <option value="">設定しない</option>
          {users.map((user) => (
            <option key={user.id} value={user.id}>
              {user.name}（{user.department}）
            </option>
          ))}
        </select>
      </Field>
      <Field label="権限" htmlFor="new-role">
        <select
          id="new-role"
          className="input"
          value={form.role}
          onChange={(event) => set("role", event.target.value as "member" | "admin")}
        >
          <option value="member">一般</option>
          <option value="admin">管理者</option>
        </select>
      </Field>

      <Button type="submit" className="w-full" data-testid="invite-user" disabled={pending}>
        {pending ? "登録しています…" : "ユーザーを登録"}
      </Button>
    </form>
  );
}
