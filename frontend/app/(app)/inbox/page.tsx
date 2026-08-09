import type { Metadata } from "next";

import { PageHeader } from "@/components/page-header";
import { RequestTable } from "@/components/request-table";
import { apiFetch } from "@/lib/api";
import type { Page, RequestSummary } from "@/lib/types";

export const metadata: Metadata = { title: "承認待ち" };

export default async function InboxPage() {
  const inbox = await apiFetch<Page<RequestSummary>>("/api/v1/requests?scope=inbox&per_page=50");

  return (
    <>
      <PageHeader
        title="承認待ち"
        description="あなたの決裁を待っている申請です。古いものから順に処理しましょう。"
      />

      <div className="card overflow-hidden">
        <div className="card-header">
          <h2 className="card-title">
            未処理 <span data-testid="inbox-count">{inbox.total}</span> 件
          </h2>
        </div>
        <RequestTable
          requests={inbox.items}
          emptyTitle="承認待ちの申請はありません"
          emptyDescription="すべて処理済みです。新しい承認依頼が届くとここに表示されます。"
        />
      </div>
    </>
  );
}
