import { cn } from "@/lib/cn";
import { formatDateTime } from "@/lib/format";
import { ROLE_LABEL, STEP_STATUS_LABEL } from "@/lib/status";
import type { RequestStep, StepStatus } from "@/lib/types";

const MARKER: Record<StepStatus, string> = {
  waiting: "border-slate-200 bg-white text-slate-400",
  pending: "border-amber-400 bg-amber-50 text-amber-700",
  approved: "border-emerald-500 bg-emerald-500 text-white",
  rejected: "border-rose-500 bg-rose-500 text-white",
  sent_back: "border-amber-500 bg-amber-500 text-white",
  skipped: "border-slate-200 bg-slate-100 text-slate-400",
};

const LABEL_TONE: Record<StepStatus, string> = {
  waiting: "text-slate-400",
  pending: "text-amber-700",
  approved: "text-emerald-700",
  rejected: "text-rose-700",
  sent_back: "text-amber-700",
  skipped: "text-slate-400",
};

export function ApprovalRoute({
  steps,
  currentStepIndex,
}: {
  steps: RequestStep[];
  currentStepIndex: number;
}) {
  if (steps.length === 0) {
    return (
      <p className="px-1 py-6 text-sm text-slate-500">
        まだ承認ルートは開始されていません。提出すると承認ルートが確定します。
      </p>
    );
  }

  return (
    <ol className="relative space-y-1">
      {steps.map((step, index) => {
        const isCurrent = step.status === "pending" && index === currentStepIndex;
        return (
          <li
            key={step.id}
            data-testid={`route-step-${index}`}
            data-current={isCurrent}
            data-status={step.status}
            className={cn(
              "relative flex gap-3 rounded-lg px-2 py-3 transition-colors",
              isCurrent && "bg-amber-50/60",
            )}
          >
            {index < steps.length - 1 ? (
              <span
                className="absolute top-11 bottom-0 left-[1.4rem] w-px bg-slate-200"
                aria-hidden
              />
            ) : null}

            <span
              className={cn(
                "z-10 grid size-8 shrink-0 place-items-center rounded-full border-2 text-xs font-semibold",
                MARKER[step.status],
              )}
            >
              {step.status === "approved" ? <CheckIcon /> : index + 1}
            </span>

            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                <span data-testid="route-step-name" className="text-sm font-medium text-slate-900">
                  {step.name}
                </span>
                <span className={cn("text-xs font-medium", LABEL_TONE[step.status])}>
                  {STEP_STATUS_LABEL[step.status]}
                </span>
              </div>
              <p className="mt-0.5 truncate text-sm text-slate-600">{approverLabel(step)}</p>
              {step.comment ? (
                <p className="mt-1.5 rounded-md bg-slate-50 px-2.5 py-1.5 text-sm break-words text-slate-700 ring-1 ring-slate-100 ring-inset">
                  {step.comment}
                </p>
              ) : null}
              {step.acted_at ? (
                <p className="mt-1 text-xs text-slate-400">{formatDateTime(step.acted_at)}</p>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function approverLabel(step: RequestStep): string {
  if (step.approver) return step.approver.name;
  if (step.approver_role) return `${ROLE_LABEL[step.approver_role]}権限を持つ担当者`;
  return "承認者未設定";
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="size-4" aria-hidden>
      <path
        d="m5 10.5 3.2 3.2L15 7"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
