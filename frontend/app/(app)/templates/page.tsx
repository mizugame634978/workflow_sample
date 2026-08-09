import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { apiFetch } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { ItemList, TemplateSummary } from "@/lib/types";

export const metadata: Metadata = { title: "フォーム管理" };

export default async function TemplatesPage() {
  const templates = await apiFetch<ItemList<TemplateSummary>>(
    "/api/v1/templates?include_inactive=true",
  );

  return (
    <>
      <PageHeader
        title="フォーム管理"
        description="申請フォームの入力項目と承認ルートを定義します。"
        actions={
          <Link href="/templates/new">
            <Button data-testid="new-template">フォームを作成</Button>
          </Link>
        }
      />

      <div className="card overflow-hidden">
        {templates.items.length === 0 ? (
          <EmptyState title="フォームがありません" description="最初の申請フォームを作成しましょう。" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[44rem] border-collapse">
              <thead className="border-b border-slate-100 bg-slate-50/60">
                <tr>
                  <th className="th">コード</th>
                  <th className="th">フォーム名</th>
                  <th className="th">カテゴリ</th>
                  <th className="th">承認段階</th>
                  <th className="th">状態</th>
                  <th className="th">作成日</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {templates.items.map((template) => (
                  <tr key={template.id} data-testid="template-row" className="hover:bg-slate-50/70">
                    <td className="td font-mono text-xs text-slate-500">{template.code}</td>
                    <td className="td">
                      <Link
                        href={`/templates/${template.id}`}
                        className="font-medium text-slate-900 hover:text-brand-700 hover:underline"
                      >
                        {template.name}
                      </Link>
                      <span className="mt-0.5 block line-clamp-1 text-xs text-slate-400">
                        {template.description}
                      </span>
                    </td>
                    <td className="td">{template.category}</td>
                    <td className="td tabular-nums">{template.step_count} 段階</td>
                    <td className="td">
                      <span
                        className={
                          template.is_active
                            ? "inline-flex rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200 ring-inset"
                            : "inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500 ring-1 ring-slate-200 ring-inset"
                        }
                      >
                        {template.is_active ? "利用可能" : "停止中"}
                      </span>
                    </td>
                    <td className="td text-xs text-slate-500">{formatDate(template.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
