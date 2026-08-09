import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { Pagination } from "@/components/pagination";
import { PageHeader } from "@/components/page-header";
import { RequestFilters } from "@/components/request-filters";
import { RequestTable } from "@/components/request-table";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Page, Profile, RequestSummary } from "@/lib/types";

export const metadata: Metadata = { title: "申請一覧" };

type Search = { scope?: string; status?: string; q?: string; page?: string };

export default async function RequestsPage({
  searchParams,
}: {
  searchParams: Promise<Search>;
}) {
  const search = await searchParams;
  const profile = await apiFetch<Profile>("/api/v1/auth/me");

  const scope = normaliseScope(search.scope, profile.role === "admin");
  const page = Math.max(1, Number(search.page ?? "1") || 1);
  const query = new URLSearchParams({ scope, page: String(page), per_page: "20" });
  if (search.status) query.set("status", search.status);
  if (search.q) query.set("q", search.q);

  const result = await apiFetch<Page<RequestSummary>>(`/api/v1/requests?${query.toString()}`);

  const tabs = [
    { scope: "mine", label: "自分の申請" },
    { scope: "inbox", label: "承認待ち" },
    ...(profile.role === "admin" ? [{ scope: "all", label: "組織全体" }] : []),
  ];

  return (
    <>
      <PageHeader
        title="申請一覧"
        description="提出した申請と、あなたが承認者になっている申請を確認できます。"
        actions={
          <Link href="/requests/new">
            <Button>新規申請</Button>
          </Link>
        }
      />

      <div className="card overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-3">
          <div className="flex gap-1" role="tablist" aria-label="表示範囲">
            {tabs.map((tab) => (
              <Link
                key={tab.scope}
                href={`/requests?scope=${tab.scope}`}
                role="tab"
                aria-selected={scope === tab.scope}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                  scope === tab.scope
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100",
                )}
              >
                {tab.label}
              </Link>
            ))}
          </div>
          <Suspense fallback={null}>
            <RequestFilters basePath="/requests" />
          </Suspense>
        </div>

        <RequestTable
          requests={result.items}
          showApplicant={scope !== "mine"}
          emptyTitle="該当する申請はありません"
          emptyDescription="検索条件を変更するか、新しい申請を作成してください。"
        />

        <Pagination
          page={result.page}
          pages={result.pages}
          total={result.total}
          perPage={result.per_page}
          buildHref={(target) => {
            const next = new URLSearchParams(query);
            next.set("page", String(target));
            next.delete("per_page");
            return `/requests?${next.toString()}`;
          }}
        />
      </div>
    </>
  );
}

function normaliseScope(scope: string | undefined, isAdmin: boolean): string {
  if (scope === "inbox") return "inbox";
  if (scope === "all" && isAdmin) return "all";
  return "mine";
}
