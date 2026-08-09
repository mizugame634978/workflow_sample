/**
 * Single-series column chart: number of requests raised per month.
 *
 * One measure, one hue — so there is no legend (the card title names the series)
 * and no y-axis: each column is direct-labelled, which reads faster at six bars.
 */
export function MonthlyChart({ data }: { data: { month: string; count: number }[] }) {
  const max = Math.max(1, ...data.map((point) => point.count));

  return (
    <div className="px-5 pt-5 pb-4">
      <ul className="flex h-40 items-end gap-2" role="list">
        {data.map((point) => {
          const ratio = point.count / max;
          return (
            <li key={point.month} className="flex h-full flex-1 flex-col justify-end gap-1.5">
              <p className="text-center text-xs font-semibold text-slate-700 tabular-nums">
                {point.count}
              </p>
              <div
                className="w-full rounded-t bg-brand-500 transition-[height]"
                style={{ height: `${Math.max(ratio * 100, point.count > 0 ? 6 : 2)}%` }}
                title={`${label(point.month)} ${point.count}件`}
                aria-hidden
              />
              <p className="text-center text-[11px] text-slate-500">{label(point.month)}</p>
            </li>
          );
        })}
      </ul>
      <p className="sr-only">
        {data.map((point) => `${label(point.month)}は${point.count}件`).join("、")}
      </p>
    </div>
  );
}

function label(month: string): string {
  return `${Number(month.slice(5, 7))}月`;
}
