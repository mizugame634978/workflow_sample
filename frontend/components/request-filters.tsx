"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { STATUS_LABEL } from "@/lib/status";
import type { RequestStatus } from "@/lib/types";

const STATUSES: RequestStatus[] = ["draft", "pending", "approved", "rejected", "cancelled"];

export function RequestFilters({ basePath }: { basePath: string }) {
  const router = useRouter();
  const params = useSearchParams();
  const [keyword, setKeyword] = useState(params.get("q") ?? "");

  useEffect(() => setKeyword(params.get("q") ?? ""), [params]);

  function push(changes: Record<string, string>) {
    const next = new URLSearchParams(params.toString());
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    next.delete("page");
    router.push(`${basePath}?${next.toString()}`);
  }

  return (
    <form
      className="flex flex-wrap items-center gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        push({ q: keyword.trim() });
      }}
      role="search"
    >
      <input
        type="search"
        name="q"
        aria-label="件名・申請番号で検索"
        placeholder="件名・申請番号で検索"
        className="input h-9 w-56"
        value={keyword}
        onChange={(event) => setKeyword(event.target.value)}
      />
      <select
        aria-label="ステータスで絞り込む"
        className="input h-9 w-36"
        value={params.get("status") ?? ""}
        onChange={(event) => push({ status: event.target.value })}
      >
        <option value="">すべての状態</option>
        {STATUSES.map((status) => (
          <option key={status} value={status}>
            {STATUS_LABEL[status]}
          </option>
        ))}
      </select>
      <button type="submit" className="sr-only">
        検索
      </button>
    </form>
  );
}
