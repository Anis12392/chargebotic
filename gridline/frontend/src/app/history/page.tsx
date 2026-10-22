'use client';

import { useCallback, useEffect, useState } from 'react';

import { InspectionCard } from '@/components/InspectionCard';
import { ApiError, listInspections } from '@/lib/api';
import { listPending, type PendingCapture } from '@/lib/queue';
import type { InspectionSummary } from '@/lib/types';

const CLASS_FILTERS = [
  { value: '', label: 'All' },
  { value: 'secondary', label: 'Secondary' },
  { value: 'distribution', label: 'Distribution' },
  { value: 'subtransmission', label: 'Subtrans.' },
  { value: 'transmission', label: 'Transmission' },
] as const;

const PAGE_SIZE = 25;

export default function HistoryPage() {
  const [inspections, setInspections] = useState<InspectionSummary[]>([]);
  const [pending, setPending] = useState<PendingCapture[]>([]);
  const [voltageClass, setVoltageClass] = useState('');
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [offset, setOffset] = useState(0);
  const [exhausted, setExhausted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (nextOffset: number, replace: boolean) => {
      setLoading(true);
      setError(null);
      try {
        const rows = await listInspections({
          limit: PAGE_SIZE,
          offset: nextOffset,
          voltageClass: voltageClass || undefined,
          verifiedOnly,
        });
        setExhausted(rows.length < PAGE_SIZE);
        setInspections((current) => (replace ? rows : [...current, ...rows]));
      } catch (err) {
        setError(err instanceof ApiError ? err.userMessage : 'Could not load inspections.');
      } finally {
        setLoading(false);
      }
    },
    [verifiedOnly, voltageClass],
  );

  useEffect(() => {
    setOffset(0);
    void load(0, true);
  }, [load]);

  useEffect(() => {
    void listPending().then(setPending);
  }, []);

  return (
    <div className="px-4 pt-4">
      <h1 className="text-xl font-bold text-slate-50">Inspections</h1>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {CLASS_FILTERS.map((filter) => (
          <button
            key={filter.value}
            type="button"
            onClick={() => setVoltageClass(filter.value)}
            className={`chip ${
              voltageClass === filter.value ? 'border-grid-distribution text-grid-distribution' : ''
            }`}
          >
            {filter.label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => setVerifiedOnly((value) => !value)}
          aria-pressed={verifiedOnly}
          className={`chip ${verifiedOnly ? 'border-signal-ok text-signal-ok' : ''}`}
        >
          Verified only
        </button>
      </div>

      {pending.length > 0 && (
        <section className="mt-4 rounded-xl border border-signal-warn/40 bg-signal-warn/5 p-3">
          <h2 className="text-sm font-semibold text-signal-warn">
            {pending.length} capture{pending.length === 1 ? '' : 's'} waiting to upload
          </h2>
          <p className="mt-1 text-xs leading-relaxed text-slate-400">
            These are stored on this device. They upload automatically the next time you open the
            capture screen with a connection.
          </p>
          <ul className="mt-2 space-y-1 text-xs text-slate-500">
            {pending.slice(0, 5).map((entry) => (
              <li key={entry.id} className="font-mono">
                {entry.capture.latitude.toFixed(4)}, {entry.capture.longitude.toFixed(4)}
                {entry.attempts > 0 && ` · ${entry.attempts} failed attempt(s)`}
              </li>
            ))}
          </ul>
        </section>
      )}

      {error && (
        <p role="alert" className="mt-4 text-sm text-signal-danger">
          {error}
        </p>
      )}

      <div className="mt-4 space-y-3">
        {inspections.map((inspection) => (
          <InspectionCard key={inspection.id} inspection={inspection} />
        ))}
      </div>

      {!loading && inspections.length === 0 && !error && (
        <p className="mt-8 text-center text-sm text-slate-500">
          No inspections yet. Capture one to get started.
        </p>
      )}

      {loading && <p className="mt-4 text-center text-sm text-slate-500">Loading…</p>}

      {!loading && !exhausted && inspections.length > 0 && (
        <button
          type="button"
          onClick={() => {
            const next = offset + PAGE_SIZE;
            setOffset(next);
            void load(next, false);
          }}
          className="btn-secondary mt-4 w-full"
        >
          Load more
        </button>
      )}
    </div>
  );
}
