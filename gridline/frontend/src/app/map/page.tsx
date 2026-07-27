'use client';

import dynamic from 'next/dynamic';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useState } from 'react';

import { useGeolocation } from '@/hooks/useGeolocation';
import { ApiError, getMap } from '@/lib/api';
import { formatVoltageList, titleCase, voltageClassColor } from '@/lib/format';
import type { MapResponse } from '@/lib/types';

// Leaflet touches `window` at import time, so it can only load in the browser.
const GridMap = dynamic(() => import('@/components/GridMap'), {
  ssr: false,
  loading: () => (
    <div className="flex h-[60dvh] items-center justify-center rounded-xl border border-surface-700 bg-surface-900">
      <span className="text-sm text-slate-500">Loading map…</span>
    </div>
  ),
});

const RADII = [400, 800, 1600, 3000] as const;

const LEGEND = [
  { label: 'Secondary', cls: 'secondary' },
  { label: 'Distribution', cls: 'distribution' },
  { label: 'Subtransmission', cls: 'subtransmission' },
  { label: 'Transmission', cls: 'transmission' },
  { label: 'EHV', cls: 'ehv' },
] as const;

function MapPageInner() {
  const router = useRouter();
  const params = useSearchParams();
  const gps = useGeolocation(true);

  const paramLat = Number(params.get('lat'));
  const paramLon = Number(params.get('lon'));
  const hasParamCenter = Number.isFinite(paramLat) && Number.isFinite(paramLon) && paramLat !== 0;

  const [radius, setRadius] = useState<number>(800);
  const [data, setData] = useState<MapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const center = hasParamCenter
    ? { lat: paramLat, lon: paramLon }
    : gps.fix
      ? { lat: gps.fix.latitude, lon: gps.fix.longitude }
      : null;

  const load = useCallback(async () => {
    if (!center) return;
    setLoading(true);
    setError(null);
    try {
      setData(await getMap(center.lat, center.lon, radius));
    } catch (err) {
      setError(err instanceof ApiError ? err.userMessage : 'Could not load map data.');
    } finally {
      setLoading(false);
    }
    // `center` is derived from primitives; depending on the object identity
    // would refetch on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [center?.lat, center?.lon, radius]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!center) {
    return (
      <div className="px-4 pt-8">
        <h1 className="text-xl font-bold text-slate-50">Map</h1>
        <p className="mt-2 text-sm text-slate-400">
          {gps.error ?? 'Acquiring a GPS fix to centre the map…'}
        </p>
        {gps.permission === 'denied' && (
          <button type="button" onClick={gps.request} className="btn-secondary mt-4">
            Retry location
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="px-4 pt-4">
      <header className="mb-3 flex items-baseline justify-between">
        <h1 className="text-xl font-bold text-slate-50">Nearby infrastructure</h1>
        {loading && <span className="text-xs text-slate-500">Loading…</span>}
      </header>

      <GridMap
        center={center}
        assets={data?.assets ?? []}
        inspections={data?.inspections ?? []}
        radiusM={radius}
        photoLocation={hasParamCenter ? { lat: paramLat, lon: paramLon } : null}
        onSelectInspection={(id) => router.push(`/inspection/${id}`)}
      />

      <div className="mt-3 flex items-center gap-2">
        <span className="label">Radius</span>
        {RADII.map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => setRadius(value)}
            className={`chip ${radius === value ? 'border-grid-distribution text-grid-distribution' : ''}`}
          >
            {value >= 1000 ? `${value / 1000} km` : `${value} m`}
          </button>
        ))}
      </div>

      <ul className="mt-3 flex flex-wrap gap-2" aria-label="Legend">
        {LEGEND.map((entry) => (
          <li key={entry.cls} className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <span
              aria-hidden
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: voltageClassColor(entry.cls) }}
            />
            {entry.label}
          </li>
        ))}
      </ul>

      {error && (
        <p role="alert" className="mt-3 text-sm text-signal-danger">
          {error}
        </p>
      )}

      {data && (
        <section className="mt-4 space-y-3">
          <div className="card">
            <h2 className="label mb-2">Found within {radius} m</h2>
            <dl className="grid grid-cols-3 gap-3 text-center">
              <Stat label="Assets" value={data.assets.length} />
              <Stat label="Inspections" value={data.inspections.length} />
              <Stat
                label="Substations"
                value={data.assets.filter((a) => a.asset_kind === 'substation').length}
              />
            </dl>
            {data.errors.length > 0 && (
              <p className="mt-3 text-xs text-signal-warn">
                Some sources did not respond: {data.errors.join(', ')}. Coverage may be incomplete.
              </p>
            )}
          </div>

          {data.assets.length > 0 && (
            <div className="card">
              <h2 className="label mb-2">Closest assets</h2>
              <ul className="space-y-1.5">
                {data.assets.slice(0, 12).map((asset) => (
                  <li
                    key={`${asset.source}-${asset.element_id}`}
                    className="flex items-baseline justify-between gap-2 border-b border-surface-800 pb-1.5 text-sm last:border-0"
                  >
                    <span className="min-w-0 truncate text-slate-300">
                      {titleCase(asset.asset_kind)}
                      {asset.operator ? ` · ${asset.operator}` : ''}
                    </span>
                    <span className="shrink-0 font-mono text-xs text-slate-500">
                      {asset.voltage_v.length > 0 ? formatVoltageList(asset.voltage_v) : '—'} ·{' '}
                      {asset.distance_m?.toFixed(0) ?? '—'} m
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="label">{label}</dt>
      <dd className="font-mono text-xl font-bold text-slate-100">{value}</dd>
    </div>
  );
}

export default function MapPage() {
  return (
    <Suspense fallback={<div className="px-4 pt-8 text-sm text-slate-500">Loading…</div>}>
      <MapPageInner />
    </Suspense>
  );
}
