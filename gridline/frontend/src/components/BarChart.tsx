/**
 * Minimal horizontal bar chart.
 *
 * No charting library: these are labelled proportions, and a dependency that
 * ships a canvas renderer to a phone for four bars is a bad trade.
 */
export function BarChart({
  data,
  colorFor,
  emptyMessage = 'No data yet.',
  max: providedMax,
}: {
  data: Record<string, number>;
  colorFor?: (key: string) => string;
  emptyMessage?: string;
  max?: number;
}) {
  const entries = Object.entries(data).filter(([, value]) => value > 0);
  if (!entries.length) {
    return <p className="text-sm text-slate-500">{emptyMessage}</p>;
  }

  const max = providedMax ?? Math.max(...entries.map(([, value]) => value));
  const sorted = entries.sort((a, b) => b[1] - a[1]);

  return (
    <ul className="space-y-1.5">
      {sorted.map(([key, value]) => (
        <li key={key}>
          <div className="flex items-baseline justify-between gap-2 text-xs">
            <span className="min-w-0 truncate capitalize text-slate-300">
              {key.replace(/_/g, ' ')}
            </span>
            <span className="shrink-0 font-mono text-slate-400">{value}</span>
          </div>
          <div className="mt-0.5 h-1.5 w-full overflow-hidden rounded-full bg-surface-700">
            <div
              className="h-full rounded-full"
              style={{
                width: `${max ? (value / max) * 100 : 0}%`,
                backgroundColor: colorFor?.(key) ?? '#60a5fa',
              }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
