import type { Metadata } from "next";

import { LoginForm } from "@/components/login-form";
import { Logo } from "@/components/logo";

export const metadata: Metadata = { title: "ログイン" };

const DEMO_ACCOUNTS = [
  { email: "tanaka@acme.co.jp", name: "田中 美咲", role: "申請者（主任）" },
  { email: "suzuki@acme.co.jp", name: "鈴木 健一", role: "承認者（課長）" },
  { email: "nakamura@acme.co.jp", name: "中村 彩", role: "経理・管理者" },
];

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;

  return (
    <main className="grid min-h-dvh lg:grid-cols-2">
      <section className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <Logo />
          <h1 className="mt-8 text-2xl font-bold tracking-tight text-slate-900">ログイン</h1>
          <p className="mt-1.5 text-sm text-slate-500">
            社内アカウントで申請・承認業務にアクセスします。
          </p>
          <LoginForm next={next} demoAccounts={DEMO_ACCOUNTS} />
        </div>
      </section>

      <section className="relative hidden overflow-hidden bg-slate-900 lg:block">
        <div
          className="absolute inset-0 opacity-90"
          style={{
            backgroundImage:
              "radial-gradient(120% 80% at 15% 10%, #312e81 0%, #0f172a 55%, #020617 100%)",
          }}
          aria-hidden
        />
        <div className="relative flex h-full flex-col justify-between p-12 text-white">
          <p className="text-sm font-medium text-slate-300">Nagare Workflow</p>
          <div>
            <h2 className="text-3xl leading-tight font-bold tracking-tight">
              紙とハンコの決裁を、
              <br />
              追跡できるワークフローへ。
            </h2>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-slate-300">
              申請フォームと承認ルートをテンプレート化し、承認状況・所要時間・監査ログを一元管理します。
              差戻しや代理承認も、誰がいつ何を判断したかがすべて記録されます。
            </p>
            <dl className="mt-10 grid grid-cols-3 gap-6 border-t border-white/10 pt-6">
              {[
                ["5", "申請フォーム"],
                ["3", "段階の承認ルート"],
                ["100%", "監査ログ取得"],
              ].map(([value, label]) => (
                <div key={label}>
                  <dt className="text-2xl font-bold">{value}</dt>
                  <dd className="mt-1 text-xs text-slate-400">{label}</dd>
                </div>
              ))}
            </dl>
          </div>
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} Nagare Workflow — ローカルデモ環境
          </p>
        </div>
      </section>
    </main>
  );
}
