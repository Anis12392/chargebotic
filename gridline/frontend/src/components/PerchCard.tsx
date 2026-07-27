'use client';

import { useState } from 'react';

import { ConfidenceBar } from '@/components/ConfidenceBar';
import { PERCH_GRADE_COLOR } from '@/lib/format';
import type { PerchSuitability } from '@/lib/types';

/**
 * Perch Suitability Score.
 *
 * The single number is the headline, but the factor breakdown is what makes it
 * actionable — a 55 driven by weak harvest is a different problem from a 55
 * driven by obstacles, and the operator needs to know which.
 */
export function PerchCard({ perch }: { perch: PerchSuitability }) {
  const [open, setOpen] = useState(false);
  const color = PERCH_GRADE_COLOR[perch.grade];
  const blocked = perch.blockers.length > 0;

  return (
    <section className="card" aria-labelledby="perch-heading">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 id="perch-heading" className="label">
            Perch suitability
          </h2>
          <p className="mt-1 flex items-baseline gap-2">
            <span className="font-mono text-3xl font-bold" style={{ color }}>
              {blocked ? '—' : perch.score.toFixed(0)}
            </span>
            <span className="text-sm text-slate-500">{blocked ? '' : '/ 100'}</span>
          </p>
          <p className="text-sm font-semibold capitalize" style={{ color }}>
            {perch.grade}
          </p>
        </div>

        {!blocked && (
          <dl className="text-right text-xs text-slate-400">
            {perch.estimated_flux_density_ut !== null && (
              <div>
                <dt className="label">Field at coupler</dt>
                <dd className="font-mono text-sm text-slate-200">
                  {perch.estimated_flux_density_ut.toFixed(1)} µT
                </dd>
              </div>
            )}
            {perch.estimated_harvest_power_w !== null && (
              <div className="mt-2">
                <dt className="label">Harvestable</dt>
                <dd className="font-mono text-sm text-slate-200">
                  ≈{perch.estimated_harvest_power_w.toFixed(1)} W
                </dd>
              </div>
            )}
          </dl>
        )}
      </div>

      <p className="mt-3 text-sm leading-relaxed text-slate-300">{perch.recommendation}</p>

      {blocked && (
        <ul className="mt-3 space-y-1.5" aria-label="Blockers">
          {perch.blockers.map((blocker) => (
            <li
              key={blocker}
              className="rounded-lg border border-signal-danger/40 bg-signal-danger/5 p-2.5 text-sm text-signal-danger"
            >
              {blocker}
            </li>
          ))}
        </ul>
      )}

      {!blocked && <ConfidenceBar value={perch.confidence} label="Score confidence" />}

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="btn-ghost mt-3 w-full text-xs"
        aria-expanded={open}
      >
        {open ? 'Hide factor breakdown' : 'Show all 10 factors'}
      </button>

      {open && (
        <ul className="mt-2 space-y-2">
          {[...perch.factors]
            .sort((a, b) => b.weight - a.weight)
            .map((factor) => (
              <li key={factor.key} className="card-tight">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-sm font-medium text-slate-200">{factor.label}</span>
                  <span className="font-mono text-xs text-slate-400">
                    {factor.score.toFixed(0)}
                    <span className="text-slate-600"> ×{factor.weight.toFixed(2)}</span>
                  </span>
                </div>
                <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-surface-700">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${factor.score}%`,
                      backgroundColor:
                        factor.score >= 70 ? '#4ade80' : factor.score >= 45 ? '#fbbf24' : '#f87171',
                    }}
                  />
                </div>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-500">
                  {factor.rationale}
                  {factor.confidence === 0 && (
                    <span className="ml-1 italic text-slate-600">(no supporting evidence)</span>
                  )}
                </p>
              </li>
            ))}
        </ul>
      )}

      {perch.harvest_assumptions.length > 0 && (
        <details className="mt-3">
          <summary className="cursor-pointer text-xs font-semibold text-slate-500">
            Harvest model assumptions
          </summary>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-relaxed text-slate-500">
            {perch.harvest_assumptions.map((assumption) => (
              <li key={assumption}>{assumption}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
