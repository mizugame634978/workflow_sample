import { ROLE_LABEL } from "@/lib/status";
import type { TemplateStep } from "@/lib/types";

const APPROVER_TYPE_HINT = {
  user: "指名された承認者",
  manager: "提出時に自動で決定されます",
  role: "権限による承認",
} as const;

export function RoutePreview({ steps }: { steps: TemplateStep[] }) {
  if (steps.length === 0) {
    return <p className="px-5 py-6 text-sm text-slate-500">承認ステップが未設定です。</p>;
  }

  return (
    <ol className="divide-y divide-slate-100">
      {steps.map((step, index) => (
        <li key={step.id} className="flex items-start gap-3 px-5 py-3">
          <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
            {index + 1}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-900">{step.name}</p>
            <p className="mt-0.5 truncate text-xs text-slate-500">{approver(step)}</p>
            <p className="text-[11px] text-slate-400">{APPROVER_TYPE_HINT[step.approver_type]}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

function approver(step: TemplateStep): string {
  if (step.approver) return `${step.approver.name}（${step.approver.department}）`;
  if (step.approver_role) return `${ROLE_LABEL[step.approver_role]}権限を持つ担当者`;
  return "申請者の上長";
}
