'use client';

import { useCallback, useEffect, useState } from 'react';

import { InspectionCard } from '@/components/InspectionCard';
import { ApiError, getPerchRanking } from '@/lib/api';
import type { InspectionSummary } from '@/lib/types';

const THRESHOLDS = [
  { value: 0, label: 'All' },
  { value: 45, label: 'Marginal+' },
  { value: 65, label: 'Good+' },
  { value: 80, label: 'Excellent' },
] as const;

export default function PerchPage() {
  const [minScore, setMinScore] = useState(0);
  const [rows, setRows] = useState<InspectionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRows(await getPerchRanking(minScore, 50));
    } catch (err) {
      setError(err instanceof ApiError ? err.userMessage : 'Could not load the ranking.');
    } finally {
      setLoading(false);
    }
  }, [minScore]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="px-4 pt-4">
      <h1 className="text-xl font-bold text-slate-50">Perch ranking</h1>
      <p className="mt-1 text-sm leading-relaxed text-slate-400">
        Spans ranked by suitability for autonomous energy harvesting. Scores combine estimated
        magnetic field and harvestable power with accessibility, clearance, approach safety and
        logged outcomes.
      </p>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {THRESHOLDS.map((threshold) => (
          <button
            key={threshold.value}
            type="button"
            onClick={() => setMinScore(threshold.value)}
            className={`chip ${
              minScore === threshold.value ? 'border-grid-distribution text-grid-distribution' : ''
            }`}
          >
            {threshold.label}
          </button>
        ))}
      </div>

      {error && (
        <p role="alert" className="mt-4 text-sm text-signal-danger">
          {error}
        </p>
      )}

      <ol className="mt-4 space-y-3">
        {rows.map((inspection, index) => (
          <li key={inspection.id} className="relative">
            <span className="absolute -left-1 -top-1 z-10 flex h-6 w-6 items-center justify-center rounded-full bg-surface-700 font-mono text-[11px] font-bold text-slate-300">
              {index + 1}
            </span>
            <InspectionCard inspection={inspection} />
          </li>
        ))}
      </ol>

      {loading && <p className="mt-4 text-center text-sm text-slate-500">Loading…</p>}

      {!loading && rows.length === 0 && !error && (
        <p className="mt-8 text-center text-sm text-slate-500">
          No spans scored at or above this threshold yet.
        </p>
      )}

      <p className="mt-6 text-[11px] leading-relaxed text-slate-600">
        Every score rests on an estimated line current, not a measurement. A field measurement
        entered through the verification form will change the ranking materially — record one
        whenever you have it.
      </p>
    </div>
  );
}
