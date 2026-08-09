"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";

const DEMO_PASSWORD = "Password123!";

export function LoginForm({
  next,
  demoAccounts,
}: {
  next?: string;
  demoAccounts: { email: string; name: string; role: string }[];
}) {
  const router = useRouter();
  const [email, setEmail] = useState("tanaka@acme.co.jp");
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);

    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      setError(body.message ?? "ログインできませんでした");
      setPending(false);
      return;
    }

    router.replace(next ?? "/dashboard");
    router.refresh();
  }

  return (
    <>
      <form onSubmit={handleSubmit} className="mt-8 space-y-4" noValidate>
        {error ? (
          <p
            role="alert"
            data-testid="login-error"
            className="rounded-lg bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700 ring-1 ring-rose-200 ring-inset"
          >
            {error}
          </p>
        ) : null}

        <Field label="メールアドレス" htmlFor="email">
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="username"
            className="input"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </Field>

        <Field label="パスワード" htmlFor="password">
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            className="input"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </Field>

        <Button type="submit" className="w-full" disabled={pending}>
          {pending ? "ログインしています…" : "ログイン"}
        </Button>
      </form>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-4">
        <p className="text-xs font-semibold text-slate-700">デモアカウント</p>
        <p className="mt-1 text-xs text-slate-500">
          パスワードはいずれも <code className="rounded bg-slate-100 px-1">{DEMO_PASSWORD}</code>
        </p>
        <ul className="mt-3 space-y-1.5">
          {demoAccounts.map((account) => (
            <li key={account.email}>
              <button
                type="button"
                onClick={() => {
                  setEmail(account.email);
                  setPassword(DEMO_PASSWORD);
                }}
                className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left hover:bg-slate-50"
              >
                <span className="text-sm text-slate-700">{account.name}</span>
                <span className="text-xs text-slate-400">{account.role}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}
