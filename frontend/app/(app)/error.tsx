"use client";

import { useEffect } from "react";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="card mx-auto max-w-lg p-8 text-center">
      <h1 className="text-lg font-bold text-slate-900">画面を表示できませんでした</h1>
      <p className="mt-2 text-sm text-slate-500">
        APIサーバーとの通信に失敗した可能性があります。時間をおいて再試行してください。
      </p>
      {error.digest ? (
        <p className="mt-2 font-mono text-xs text-slate-400">エラーID: {error.digest}</p>
      ) : null}
      <button
        type="button"
        onClick={reset}
        className="mt-5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white"
      >
        再読み込み
      </button>
    </div>
  );
}
