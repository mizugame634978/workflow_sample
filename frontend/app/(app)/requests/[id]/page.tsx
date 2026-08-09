import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ApprovalRoute } from "@/components/approval-route";
import { CommentThread } from "@/components/comment-thread";
import { RequestActions } from "@/components/request-actions";
import { StatusBadge } from "@/components/status-badge";
import { Timeline } from "@/components/timeline";
import { ApiRequestError, apiFetch, apiFetchOrNull } from "@/lib/api";
import { formatDateTime, formatFieldValue, initial } from "@/lib/format";
import type { RequestDetail } from "@/lib/types";

/** 403 renders an explanation; 404 falls through to the not-found page. */
async function loadRequest(id: string): Promise<RequestDetail | "forbidden" | null> {
  try {
    return await apiFetch<RequestDetail>(`/api/v1/requests/${id}`);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 403) return "forbidden";
    if (error instanceof ApiRequestError && error.status === 404) return null;
    throw error;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const request = await apiFetchOrNull<RequestDetail>(`/api/v1/requests/${id}`);
  return { title: request ? `${request.request_number} ${request.title}` : "申請詳細" };
}

export default async function RequestDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const request = await loadRequest(id);
  if (request === null) notFound();
  if (request === "forbidden") {
    return (
      <div className="card mx-auto max-w-lg p-8 text-center">
        <h1 className="text-lg font-bold text-slate-900">この申請を閲覧する権限がありません</h1>
        <p className="mt-2 text-sm text-slate-500">
          申請者・承認者・管理者のみが内容を確認できます。誤ってアクセスした場合は申請一覧に戻ってください。
        </p>
        <Link
          href="/requests"
          className="mt-5 inline-block rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white"
        >
          申請一覧へ戻る
        </Link>
      </div>
    );
  }

  const showSendBackNotice =
    request.status === "draft" && Boolean(request.last_send_back_comment) && request.permissions.can_edit;

  return (
    <>
      <nav className="mb-4 text-sm text-slate-500" aria-label="パンくず">
        <Link href="/requests" className="hover:underline">
          申請一覧
        </Link>
        <span className="mx-1.5">/</span>
        <span className="font-mono text-xs">{request.request_number}</span>
      </nav>

      <header className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={request.status} />
            <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
              {request.template_name}
            </span>
            {request.round_no > 1 ? (
              <span className="rounded bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
                再提出 {request.round_no} 回目
              </span>
            ) : null}
          </div>
          <h1 data-testid="request-title" className="mt-2 text-xl font-bold tracking-tight text-slate-900">
            {request.title}
          </h1>
          <p className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-500">
            <span className="inline-flex items-center gap-1.5">
              <span className="grid size-5 place-items-center rounded-full bg-slate-100 text-[10px] font-semibold text-slate-600">
                {initial(request.applicant.name)}
              </span>
              {request.applicant.name}（{request.applicant.department}）
            </span>
            <span>提出日時: {formatDateTime(request.submitted_at)}</span>
            {request.completed_at ? <span>完了: {formatDateTime(request.completed_at)}</span> : null}
          </p>
        </div>
        {request.permissions.can_edit ? (
          <Link
            href={`/requests/${request.id}/edit`}
            data-testid="edit-request"
            className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-slate-700 ring-1 ring-slate-300 ring-inset hover:bg-slate-50"
          >
            編集する
          </Link>
        ) : null}
      </header>

      {showSendBackNotice ? (
        <div
          data-testid="send-back-notice"
          className="mb-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3"
        >
          <p className="text-sm font-semibold text-amber-900">この申請は差し戻されています</p>
          <p className="mt-1 text-sm text-amber-800">{request.last_send_back_comment}</p>
          <p className="mt-1.5 text-xs text-amber-700">
            内容を修正して再提出してください。承認ルートは最初からやり直しになります。
          </p>
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <section className="card">
            <div className="card-header">
              <h2 className="card-title">申請内容</h2>
              <span className="text-xs text-slate-400">{request.template.code}</span>
            </div>
            <dl className="divide-y divide-slate-100">
              {request.template.form_fields.map((field) => (
                <div key={field.key} className="grid gap-1 px-5 py-3 sm:grid-cols-3 sm:gap-4">
                  <dt className="text-sm text-slate-500">{field.label}</dt>
                  <dd
                    data-testid={`field-${field.key}`}
                    className="text-sm break-words whitespace-pre-wrap text-slate-900 sm:col-span-2"
                  >
                    {formatFieldValue(field, request.form_data[field.key])}
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="card">
            <div className="card-header">
              <h2 className="card-title">コメント（{request.comments.length}）</h2>
            </div>
            <CommentThread
              requestId={request.id}
              comments={request.comments}
              canComment={request.permissions.can_comment}
            />
          </section>
        </div>

        <aside className="space-y-4">
          <section className="card">
            <div className="card-header">
              <h2 className="card-title">操作</h2>
            </div>
            <RequestActions request={request} />
          </section>

          <section className="card">
            <div className="card-header">
              <h2 className="card-title">承認ルート</h2>
            </div>
            <div className="px-3 py-2">
              <ApprovalRoute steps={request.steps} currentStepIndex={request.current_step_index} />
            </div>
          </section>

          <section className="card">
            <div className="card-header">
              <h2 className="card-title">履歴</h2>
            </div>
            <div className="px-5 py-4">
              <Timeline entries={request.timeline} />
            </div>
          </section>
        </aside>
      </div>
    </>
  );
}
