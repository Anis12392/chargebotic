import { severityStyle } from '@/lib/format';
import type { Warning } from '@/lib/types';

const ORDER: Record<Warning['severity'], number> = { danger: 0, caution: 1, info: 2 };

export function WarningList({ warnings }: { warnings: Warning[] }) {
  if (!warnings.length) return null;

  // Safety-critical first, always. A danger notice below three info notices is
  // a danger notice nobody reads.
  const sorted = [...warnings].sort((a, b) => ORDER[a.severity] - ORDER[b.severity]);

  return (
    <ul className="space-y-2" aria-label="Warnings">
      {sorted.map((warning) => {
        const style = severityStyle(warning.severity);
        return (
          <li
            key={`${warning.code}-${warning.message.slice(0, 24)}`}
            className={`flex gap-2.5 rounded-lg border ${style.border} bg-surface-900/60 p-3`}
          >
            <span aria-hidden className={`mt-0.5 text-sm font-bold ${style.text}`}>
              {style.icon}
            </span>
            <div>
              <p className={`text-xs font-semibold uppercase tracking-wide ${style.text}`}>
                {warning.severity}
              </p>
              <p className="mt-0.5 text-sm leading-relaxed text-slate-300">{warning.message}</p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
