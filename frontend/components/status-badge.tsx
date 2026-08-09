import { cn } from "@/lib/cn";
import { STATUS_DOT, STATUS_LABEL, STATUS_TONE } from "@/lib/status";
import type { RequestStatus } from "@/lib/types";

export function StatusBadge({
  status,
  size = "md",
}: {
  status: RequestStatus;
  size?: "sm" | "md";
}) {
  return (
    <span
      data-testid="status-badge"
      data-status={status}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full font-medium ring-1 ring-inset whitespace-nowrap",
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs",
        STATUS_TONE[status],
      )}
    >
      <span className={cn("size-1.5 rounded-full", STATUS_DOT[status])} aria-hidden />
      {STATUS_LABEL[status]}
    </span>
  );
}
