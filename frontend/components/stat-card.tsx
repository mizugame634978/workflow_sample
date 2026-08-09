import Link from "next/link";

import { cn } from "@/lib/cn";

const TONES = {
  brand: "bg-brand-500",
  amber: "bg-amber-500",
  emerald: "bg-emerald-500",
  slate: "bg-slate-300",
} as const;

export function StatCard({
  label,
  value,
  unit,
  hint,
  href,
  tone = "slate",
  testId,
}: {
  label: string;
  value: string | number;
  unit?: string;
  hint?: string;
  href?: string;
  tone?: keyof typeof TONES;
  testId?: string;
}) {
  const body = (
    <>
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-2 flex items-baseline gap-1">
        <span
          data-testid={testId}
          className="text-2xl font-bold tracking-tight text-slate-900 tabular-nums"
        >
          {value}
        </span>
        {unit ? <span className="text-sm text-slate-500">{unit}</span> : null}
      </p>
      {hint ? <p className="mt-1 text-xs text-slate-400">{hint}</p> : null}
      <span className={cn("mt-3 inline-block h-1 w-8 rounded-full", TONES[tone])} aria-hidden />
    </>
  );

  if (href) {
    return (
      <Link href={href} className="card block p-4 transition-shadow hover:shadow-md">
        {body}
      </Link>
    );
  }
  return <div className="card p-4">{body}</div>;
}
