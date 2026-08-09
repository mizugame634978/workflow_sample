import type { Metadata } from "next";
import Link from "next/link";

import { MonthlyChart } from "@/components/monthly-chart";
import { PageHeader } from "@/components/page-header";
import { RequestTable } from "@/components/request-table";
import { StatCard } from "@/components/stat-card";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { formatLeadTime } from "@/lib/format";
import type { AnalyticsSummary, ItemList, Page, Profile, RequestSummary, TemplateSummary } from "@/lib/types";

export const metadata: Metadata = { title: "ダッシュボード" };

export default async function DashboardPage() {
  const [profile, summary, inbox, mine, templates] = await Promise.all([
    apiFetch<Profile>("/api/v1/auth/me"),
    apiFetch<AnalyticsSummary>("/api/v1/analytics/summary"),
    apiFetch<Page<RequestSummary>>("/api/v1/requests?scope=inbox&per_page=5"),
    apiFetch<Page<RequestSummary>>("/api/v1/requests?scope=mine&per_page=5"),
    apiFetch<ItemList<TemplateSummary>>("/api/v1/templates"),
  ]);

  const now = new Date();
  const greeting = now.getHours() < 11 ? "おはようございます" : "お疲れさまです";

  return (
    <>
      <PageHeader
        title="ダッシュボード"
        description={`${greeting}、${profile.name}さん。本日の申請状況です。`}
        actions={
          <Link href="/requests/new">
            <Button>新規申請</Button>
          </Link>
        }
      />

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard
          label="自分の承認待ち"
          value={summary.awaiting_my_approval}
          unit="件"
          hint="あなたの決裁を待っています"
          href="/inbox"
          tone="amber"
          testId="stat-awaiting"
        />
        <StatCard
          label="進行中の自分の申請"
          value={summary.my_open_requests}
          unit="件"
          hint="下書き・承認待ちの合計"
          href="/requests?scope=mine"
          tone="brand"
          testId="stat-open"
        />
        <StatCard
          label="承認済み"
          value={summary.by_status.approved}
          unit="件"
          hint="集計対象期間の累計"
          tone="emerald"
          testId="stat-approved"
        />
        <StatCard
          label="平均承認リードタイム"
          value={formatLeadTime(summary.average_lead_time_hours)}
          hint="提出から最終承認まで"
          tone="slate"
          testId="stat-lead-time"
        />
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <div className="card-header">
            <h2 className="card-title">月別の申請件数</h2>
            <span className="text-xs text-slate-400">直近6か月</span>
          </div>
          <MonthlyChart data={summary.monthly} />
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">よく使われるフォーム</h2>
          </div>
          <ul className="divide-y divide-slate-100">
            {summary.by_template.length === 0 ? (
              <li className="px-5 py-8 text-center text-sm text-slate-500">
                まだ申請の実績がありません
              </li>
            ) : (
              summary.by_template.map((item) => (
                <li key={item.name} className="flex items-center justify-between px-5 py-3">
                  <span className="text-sm text-slate-700">{item.name}</span>
                  <span className="text-sm font-semibold text-slate-900 tabular-nums">
                    {item.count}
                    <span className="ml-0.5 text-xs font-normal text-slate-500">件</span>
                  </span>
                </li>
              ))
            )}
          </ul>
        </div>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <div className="card overflow-hidden">
          <div className="card-header">
            <h2 className="card-title">あなたの承認待ち</h2>
            <Link href="/inbox" className="text-xs font-medium text-brand-600 hover:underline">
              すべて見る
            </Link>
          </div>
          <RequestTable
            requests={inbox.items}
            compact
            emptyTitle="承認待ちの申請はありません"
            emptyDescription="新しい承認依頼が届くとここに表示されます。"
          />
        </div>

        <div className="card overflow-hidden">
          <div className="card-header">
            <h2 className="card-title">自分の申請</h2>
            <Link
              href="/requests?scope=mine"
              className="text-xs font-medium text-brand-600 hover:underline"
            >
              すべて見る
            </Link>
          </div>
          <RequestTable
            requests={mine.items}
            compact
            showApplicant={false}
            emptyTitle="申請はまだありません"
            emptyDescription="「新規申請」から最初の申請を作成しましょう。"
          />
        </div>
      </section>

      <section className="mt-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">申請フォームから始める</h2>
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {templates.items.map((template) => (
            <li key={template.id}>
              <Link
                href={`/requests/new/${template.id}`}
                className="card block h-full p-4 transition-shadow hover:shadow-md"
              >
                <span className="inline-block rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-600">
                  {template.category}
                </span>
                <p className="mt-2 text-sm font-semibold text-slate-900">{template.name}</p>
                <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-slate-500">
                  {template.description}
                </p>
                <p className="mt-2.5 text-[11px] text-slate-400">
                  承認ステップ {template.step_count} 段階
                </p>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
