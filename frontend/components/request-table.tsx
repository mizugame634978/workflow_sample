import Link from "next/link";

import { StatusBadge } from "@/components/status-badge";
import { EmptyState } from "@/components/ui/empty-state";
import { formatDate, formatDateTime, initial } from "@/lib/format";
import type { RequestSummary } from "@/lib/types";

export function RequestTable({
  requests,
  emptyTitle = "該当する申請はありません",
  emptyDescription,
  showApplicant = true,
  compact = false,
}: {
  requests: RequestSummary[];
  emptyTitle?: string;
  emptyDescription?: string;
  showApplicant?: boolean;
  /** Drops the wider columns so the table fits inside a dashboard card. */
  compact?: boolean;
}) {
  if (requests.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  const withNumber = !compact;
  const withApprover = !compact;
  const withApplicant = showApplicant;

  return (
    <div className="overflow-x-auto">
      <table className={compact ? "w-full border-collapse" : "w-full min-w-[46rem] border-collapse"}>
        <thead className="border-b border-slate-100 bg-slate-50/60">
          <tr>
            {withNumber ? <th className="th">申請番号</th> : null}
            <th className="th">件名</th>
            {withApplicant ? <th className="th">申請者</th> : null}
            {withApprover ? <th className="th">現在の承認者</th> : null}
            <th className="th">状態</th>
            <th className="th">更新日時</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {requests.map((request) => (
            <tr key={request.id} data-testid="request-row" className="hover:bg-slate-50/70">
              {withNumber ? (
                <td className="td font-mono text-xs whitespace-nowrap text-slate-500">
                  {request.request_number}
                </td>
              ) : null}
              <td className="td">
                <Link
                  href={`/requests/${request.id}`}
                  className="font-medium text-slate-900 hover:text-brand-700 hover:underline"
                >
                  {request.title}
                </Link>
                <span className="mt-0.5 block text-xs text-slate-400">
                  {compact ? request.request_number : request.template_name}
                </span>
              </td>
              {withApplicant ? (
                <td className="td whitespace-nowrap">
                  <span className="inline-flex items-center gap-2">
                    <span className="grid size-6 place-items-center rounded-full bg-slate-100 text-[11px] font-semibold text-slate-600">
                      {initial(request.applicant.name)}
                    </span>
                    {request.applicant.name}
                  </span>
                </td>
              ) : null}
              {withApprover ? (
                <td className="td whitespace-nowrap text-slate-600">
                  {request.current_approver_name ?? "—"}
                  {request.current_step_name ? (
                    <span className="mt-0.5 block text-xs text-slate-400">
                      {request.current_step_name}
                    </span>
                  ) : null}
                </td>
              ) : null}
              <td className="td">
                <StatusBadge status={request.status} size="sm" />
              </td>
              <td className="td text-xs whitespace-nowrap text-slate-500">
                {compact ? formatDate(request.updated_at) : formatDateTime(request.updated_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
