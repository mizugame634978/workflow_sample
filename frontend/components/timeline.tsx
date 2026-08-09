import { cn } from "@/lib/cn";
import { formatDateTime } from "@/lib/format";
import { ACTION_LABEL, ACTION_TONE } from "@/lib/status";
import type { TimelineEntry } from "@/lib/types";

export function Timeline({ entries }: { entries: TimelineEntry[] }) {
  const ordered = [...entries].sort((a, b) => b.id - a.id);

  return (
    <ol className="relative space-y-4">
      {ordered.map((entry, index) => (
        <li key={entry.id} data-testid="timeline-entry" className="relative flex gap-3">
          {index < ordered.length - 1 ? (
            <span className="absolute top-4 bottom-[-1rem] left-[0.3rem] w-px bg-slate-200" aria-hidden />
          ) : null}
          <span
            className={cn("z-10 mt-1.5 size-2.5 shrink-0 rounded-full", ACTION_TONE[entry.action])}
            aria-hidden
          />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-baseline gap-x-2">
              <span className="text-sm font-medium text-slate-900">{ACTION_LABEL[entry.action]}</span>
              {entry.step_name ? (
                <span className="text-xs text-slate-500">{entry.step_name}</span>
              ) : null}
              <span className="ml-auto text-xs text-slate-400">
                {formatDateTime(entry.created_at)}
              </span>
            </div>
            <p className="text-sm text-slate-600">{entry.actor?.name ?? "システム"}</p>
            {entry.comment ? (
              <p className="mt-1 rounded-md bg-slate-50 px-2.5 py-1.5 text-sm break-words text-slate-700 ring-1 ring-slate-100 ring-inset">
                {entry.comment}
              </p>
            ) : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
