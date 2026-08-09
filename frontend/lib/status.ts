import type { AuditAction, NotificationType, RequestStatus, StepStatus } from "@/lib/types";

export const STATUS_LABEL: Record<RequestStatus, string> = {
  draft: "下書き",
  pending: "承認待ち",
  approved: "承認済み",
  rejected: "却下",
  cancelled: "取り下げ",
};

/** Tailwind utility sets, kept out of the components so tones stay consistent. */
export const STATUS_TONE: Record<RequestStatus, string> = {
  draft: "bg-slate-100 text-slate-700 ring-slate-200",
  pending: "bg-amber-50 text-amber-800 ring-amber-200",
  approved: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  rejected: "bg-rose-50 text-rose-800 ring-rose-200",
  cancelled: "bg-slate-100 text-slate-500 ring-slate-200",
};

export const STATUS_DOT: Record<RequestStatus, string> = {
  draft: "bg-slate-400",
  pending: "bg-amber-500",
  approved: "bg-emerald-500",
  rejected: "bg-rose-500",
  cancelled: "bg-slate-400",
};

export const STEP_STATUS_LABEL: Record<StepStatus, string> = {
  waiting: "未着手",
  pending: "承認待ち",
  approved: "承認済み",
  rejected: "却下",
  sent_back: "差戻し",
  skipped: "スキップ",
};

export const ACTION_LABEL: Record<AuditAction, string> = {
  created: "申請を作成",
  updated: "内容を更新",
  submitted: "申請を提出",
  approved: "承認",
  rejected: "却下",
  sent_back: "差戻し",
  cancelled: "取り下げ",
  commented: "コメント",
};

export const ACTION_TONE: Record<AuditAction, string> = {
  created: "bg-slate-400",
  updated: "bg-slate-400",
  submitted: "bg-sky-500",
  approved: "bg-emerald-500",
  rejected: "bg-rose-500",
  sent_back: "bg-amber-500",
  cancelled: "bg-slate-400",
  commented: "bg-indigo-400",
};

export const NOTIFICATION_LABEL: Record<NotificationType, string> = {
  approval_requested: "承認依頼",
  step_approved: "承認の進捗",
  completed: "承認完了",
  rejected: "却下",
  sent_back: "差戻し",
  commented: "コメント",
};

export const ROLE_LABEL = { admin: "管理者", member: "一般" } as const;
