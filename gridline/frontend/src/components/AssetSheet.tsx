'use client';

import { compassPoint, formatDistance, formatVoltageList, titleCase } from '@/lib/format';
import type { GISAsset } from '@/lib/types';

/** Same voltage ramp the map draws with, so the sheet and the line agree. */
function voltageColor(volts: number | undefined): string {
  if (volts === undefined) return '#7c8da0';
  if (volts <= 1_000) return '#5eead4';
  if (volts <= 34_500) return '#60a5fa';
  if (volts <= 115_000) return '#c084fc';
  if (volts <= 345_000) return '#fb923c';
  return '#f87171';
}

function voltageClassLabel(volts: number | undefined): string {
  if (volts === undefined) return 'Voltage not tagged';
  if (volts <= 1_000) return 'Secondary / service';
  if (volts <= 34_500) return 'Primary distribution';
  if (volts <= 115_000) return 'Subtransmission';
  if (volts <= 345_000) return 'Transmission';
  return 'Extra high voltage';
}

/** OSM tags worth surfacing, in the order a field engineer would want them. */
const TAG_ROWS: Array<{ key: string; label: string }> = [
  { key: 'operator', label: 'Operator' },
  { key: 'ref', label: 'Circuit / pole ref' },
  { key: 'circuits', label: 'Circuits' },
  { key: 'cables', label: 'Cables' },
  { key: 'wires', label: 'Wires' },
  { key: 'frequency', label: 'Frequency' },
  { key: 'material', label: 'Material' },
  { key: 'structure', label: 'Structure' },
  { key: 'design', label: 'Design' },
  { key: 'location', label: 'Location' },
];

export function AssetSheet({ asset, onClose }: { asset: GISAsset | null; onClose: () => void }) {
  const open = asset !== null;
  const volts = asset?.voltage_v[0];
  const color = voltageColor(volts);

  return (
    <div
      className={`pointer-events-none fixed inset-x-0 bottom-0 z-[1200] transition-transform duration-200 ease-out ${
        open ? 'translate-y-0' : 'translate-y-full'
      }`}
      aria-hidden={!open}
    >
      <div
        role="dialog"
        aria-label="Asset details"
        className="pointer-events-auto mx-auto max-w-lg rounded-t-2xl border-t border-white/10 bg-surface-900/95 backdrop-blur"
        style={{ paddingBottom: 'max(env(safe-area-inset-bottom), 14px)' }}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Close details"
          className="mx-auto block w-full pt-2.5 pb-1"
        >
          <span className="mx-auto block h-1 w-10 rounded-full bg-white/25" />
        </button>

        {asset && (
          <div className="px-4 pb-3">
            <div className="flex items-start gap-3">
              <span
                aria-hidden
                className="mt-1.5 h-3 w-3 shrink-0 rounded-full"
                style={{ backgroundColor: color, boxShadow: `0 0 0 4px ${color}25` }}
              />
              <div className="min-w-0 flex-1">
                <h2 className="truncate text-lg font-semibold text-slate-50">
                  {asset.name || titleCase(asset.asset_kind)}
                </h2>
                <p className="text-sm" style={{ color }}>
                  {voltageClassLabel(volts)}
                  {asset.voltage_v.length > 0 && ` · ${formatVoltageList(asset.voltage_v)}`}
                </p>
              </div>
              <div className="shrink-0 text-right">
                <p className="font-mono text-sm text-slate-200">{formatDistance(asset.distance_m)}</p>
                <p className="font-mono text-[11px] text-slate-500">
                  {compassPoint(asset.bearing_deg)}
                </p>
              </div>
            </div>

            <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2">
              {TAG_ROWS.map(({ key, label }) => {
                const value = asset.tags?.[key];
                if (value === undefined || value === null || value === '') return null;
                return (
                  <div key={key}>
                    <dt className="label">{label}</dt>
                    <dd className="mt-0.5 truncate text-sm text-slate-200">{String(value)}</dd>
                  </div>
                );
              })}
            </dl>

            {asset.voltage_v.length === 0 && (
              <p className="mt-3 rounded-lg border border-signal-warn/40 bg-signal-warn/5 p-2.5 text-xs leading-relaxed text-signal-warn">
                This line carries no voltage tag in OpenStreetMap. The colour above reflects
                that absence — it is not an estimate. Treat it as energised at the highest
                plausible voltage.
              </p>
            )}

            <p className="mt-3 font-mono text-[11px] text-slate-600">
              {asset.source} · {asset.element_type}/{asset.element_id}
              {typeof asset.latitude === 'number' && typeof asset.longitude === 'number' && (
                <> · {asset.latitude.toFixed(5)}, {asset.longitude.toFixed(5)}</>
              )}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
