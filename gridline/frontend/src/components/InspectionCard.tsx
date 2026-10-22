import Link from 'next/link';

import {
  PERCH_GRADE_COLOR,
  formatCoords,
  formatRelative,
  formatVolts,
  titleCase,
  voltageClassColor,
} from '@/lib/format';
import type { InspectionSummary } from '@/lib/types';

export function InspectionCard({ inspection }: { inspection: InspectionSummary }) {
  const classColor = voltageClassColor(inspection.predicted_voltage_class);

  return (
    <Link
      href={`/inspection/${inspection.id}`}
      className="card flex gap-3 transition-colors hover:border-surface-600"
    >
      {inspection.thumbnail_url ? (
        /* Presigned S3 URLs expire and carry a query signature, so the Next
           image optimiser cannot serve them. */
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={inspection.thumbnail_url}
          alt=""
          className="h-16 w-16 shrink-0 rounded-lg object-cover"
        />
      ) : (
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-lg bg-surface-800 text-slate-600">
          ⚡
        </div>
      )}

      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-2">
          <span className="truncate text-sm font-semibold" style={{ color: classColor }}>
            {titleCase(inspection.predicted_voltage_class ?? 'unknown')}
          </span>
          <span className="shrink-0 font-mono text-[11px] text-slate-500">
            {formatRelative(inspection.created_at)}
          </span>
        </div>

        <p className="truncate text-xs text-slate-400">
          {inspection.predicted_utility ?? 'Utility not attributed'}
          {inspection.predicted_nominal_v
            ? ` · ${formatVolts(inspection.predicted_nominal_v)}`
            : ''}
        </p>

        <p className="mt-0.5 font-mono text-[11px] text-slate-600">
          {formatCoords(inspection.latitude, inspection.longitude)}
        </p>

        <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
          <span className="chip py-0.5 text-[10px]">
            {Math.round(inspection.overall_confidence * 100)}% conf
          </span>
          {inspection.perch_score !== null && (
            <span
              className="chip py-0.5 text-[10px]"
              style={{
                color:
                  inspection.perch_score >= 65
                    ? PERCH_GRADE_COLOR.good
                    : inspection.perch_score >= 45
                      ? PERCH_GRADE_COLOR.marginal
                      : PERCH_GRADE_COLOR.poor,
              }}
            >
              perch {inspection.perch_score.toFixed(0)}
            </span>
          )}
          {inspection.is_verified && (
            <span className="chip border-signal-ok/40 py-0.5 text-[10px] text-signal-ok">
              verified
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
