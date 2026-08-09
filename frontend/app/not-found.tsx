import Link from "next/link";

export default function NotFound() {
  return (
    <main className="grid min-h-dvh place-items-center px-6">
      <div className="text-center">
        <p className="text-sm font-semibold text-brand-600">404</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
          お探しのページは見つかりませんでした
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          URLが変更されたか、アクセス権限のないデータの可能性があります。
        </p>
        <Link
          href="/dashboard"
          className="mt-6 inline-block rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white"
        >
          ダッシュボードへ戻る
        </Link>
      </div>
    </main>
  );
}
