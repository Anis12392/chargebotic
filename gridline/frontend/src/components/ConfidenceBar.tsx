import { confidenceLabel, formatConfidence } from '@/lib/format';

/**
 * A confidence readout that shows the number *and* the word.
 *
 * A bare "62%" invites the reader to treat the estimate as nearly right. The
 * word ("moderate") and the colour do the interpretive work that the bar alone
 * cannot.
 */
export function ConfidenceBar({
  value,
  label = 'Confidence',
  compact = false,
}: {
  value: number;
  label?: string;
  compact?: boolean;
}) {
  const percent = Math.round(Math.max(0, Math.min(1, value)) * 100);
  const color = value >= 0.8 ? '#4ade80' : value >= 0.5 ? '#fbbf24' : '#f87171';

  return (
    <div className={compact ? '' : 'mt-2'}>
      <div className="flex items-baseline justify-between">
        <span className="label">{label}</span>
        <span className="font-mono text-xs text-slate-300">
          {formatConfidence(value)} · {confidenceLabel(value)}
        </span>
      </div>
      <div
        className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-surface-700"
        role="meter"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label}: ${percent} percent, ${confidenceLabel(value)}`}
      >
        <div
          className="h-full rounded-full transition-[width]"
          style={{ width: `${percent}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
