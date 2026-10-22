'use client';

import { useState } from 'react';

import { formatConfidence } from '@/lib/format';
import type { EvidenceItem } from '@/lib/types';

const SOURCE_STYLE: Record<EvidenceItem['source'], { label: string; className: string }> = {
  vision: { label: 'Image', className: 'text-grid-distribution border-grid-distribution/40' },
  gis: { label: 'GIS', className: 'text-grid-subtransmission border-grid-subtransmission/40' },
  standards: { label: 'Standard', className: 'text-grid-secondary border-grid-secondary/40' },
  physics: { label: 'Physics', className: 'text-grid-transmission border-grid-transmission/40' },
  history: { label: 'History', className: 'text-slate-400 border-surface-600' },
  user: { label: 'Engineer', className: 'text-signal-ok border-signal-ok/40' },
};

/**
 * The audit trail. Sorted by influence so the reader sees what actually drove
 * the conclusion, not whatever the engine happened to compute first.
 */
export function EvidenceList({ evidence }: { evidence: EvidenceItem[] }) {
  const [expanded, setExpanded] = useState(false);

  if (!evidence.length) {
    return (
      <p className="text-sm text-slate-500">
        No evidence was gathered. The report has nothing to stand on.
      </p>
    );
  }

  const sorted = [...evidence].sort((a, b) => b.weight * b.confidence - a.weight * a.confidence);
  const visible = expanded ? sorted : sorted.slice(0, 4);

  return (
    <div>
      <ol className="space-y-2">
        {visible.map((item, index) => {
          const style = SOURCE_STYLE[item.source];
          return (
            <li key={`${item.source}-${index}`} className="card-tight">
              <div className="flex items-start justify-between gap-2">
                <span
                  className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${style.className}`}
                >
                  {style.label}
                </span>
                <span className="shrink-0 font-mono text-[11px] text-slate-500">
                  w {item.weight.toFixed(2)} · c {formatConfidence(item.confidence)}
                </span>
              </div>
              <p className="mt-2 text-sm font-medium text-slate-200">{item.observation}</p>
              <p className="mt-1 text-sm leading-relaxed text-slate-400">{item.implication}</p>
              {item.reference && (
                <p className="mt-1.5 text-[11px] italic text-slate-600">Ref: {item.reference}</p>
              )}
            </li>
          );
        })}
      </ol>

      {sorted.length > 4 && (
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className="btn-ghost mt-2 w-full text-xs"
          aria-expanded={expanded}
        >
          {expanded ? 'Show less' : `Show all ${sorted.length} evidence items`}
        </button>
      )}
    </div>
  );
}
