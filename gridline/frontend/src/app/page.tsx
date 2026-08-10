'use client';

import type { Map as LeafletMap } from 'leaflet';
import dynamic from 'next/dynamic';
import { useCallback, useEffect, useRef, useState } from 'react';

import { AssetSheet } from '@/components/AssetSheet';
import type { BasemapStyle } from '@/components/LiveMap';
import { accuracyVerdict, useGeolocation } from '@/hooks/useGeolocation';
import { useHeading } from '@/hooks/useHeading';
import { ApiError, getMap } from '@/lib/api';
import type { GISAsset, InspectionSummary } from '@/lib/types';

// Leaflet touches `window` at import time, so it can only load in the browser.
const LiveMap = dynamic(() => import('@/components/LiveMap'), {
  ssr: false,
  loading: () => <div className="absolute inset-0 bg-surface-950" />,
});

/** Fallback view until a fix arrives — central San Francisco. */
const FALLBACK_CENTER = { lat: 37.7749, lon: -122.4194 };

const STYLE_LABEL: Record<BasemapStyle, string> = {
  night: 'Night',
  day: 'Day',
  satellite: 'Satellite',
};

export default function MapScreen() {
  const gps = useGeolocation(true);
  const compass = useHeading(true);

  const [assets, setAssets] = useState<GISAsset[]>([]);
  const [inspections, setInspections] = useState<InspectionSummary[]>([]);
  const [selected, setSelected] = useState<GISAsset | null>(null);
  const [following, setFollowing] = useState(true);
  const [style, setStyle] = useState<BasemapStyle>('night');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sources, setSources] = useState<string[]>([]);

  const mapRef = useRef<LeafletMap | null>(null);
  const requestSeq = useRef(0);
  const initialCenter = useRef(FALLBACK_CENTER);

  // Freeze the opening view at the first fix; afterwards follow mode owns the
  // camera, so re-centring on every render would fight the user's panning.
  if (gps.live && initialCenter.current === FALLBACK_CENTER) {
    initialCenter.current = { lat: gps.live.latitude, lon: gps.live.longitude };
  }

  const loadViewport = useCallback(
    async (center: { lat: number; lon: number }, radiusM: number) => {
      const seq = ++requestSeq.current;
      setLoading(true);
      try {
        const data = await getMap(center.lat, center.lon, radiusM, true);
        // Ignore a slow response that a newer pan has already superseded,
        // otherwise the map flickers back to stale features.
        if (seq !== requestSeq.current) return;
        setAssets(data.assets);
        setInspections(data.inspections);
        setSources(data.sources);
        setError(data.errors.length ? `Some sources did not answer: ${data.errors.join(', ')}` : null);
      } catch (err) {
        if (seq !== requestSeq.current) return;
        setError(err instanceof ApiError ? err.userMessage : 'Could not load infrastructure.');
      } finally {
        if (seq === requestSeq.current) setLoading(false);
      }
    },
    [],
  );

  const recenter = useCallback(() => {
    const fix = gps.live ?? gps.fix;
    if (!fix || !mapRef.current) return;
    setFollowing(true);
    mapRef.current.flyTo([fix.latitude, fix.longitude], Math.max(mapRef.current.getZoom(), 17), {
      duration: 0.7,
    });
  }, [gps.fix, gps.live]);

  // The compass needs a user gesture on iOS, so ask on the first tap anywhere.
  useEffect(() => {
    if (!compass.needsPermission) return;
    const ask = () => void compass.requestPermission();
    window.addEventListener('touchend', ask, { once: true });
    window.addEventListener('click', ask, { once: true });
    return () => {
      window.removeEventListener('touchend', ask);
      window.removeEventListener('click', ask);
    };
  }, [compass]);

  const verdict = accuracyVerdict(gps.live?.accuracy_m);
  const heading = compass.heading ?? gps.live?.heading_deg ?? null;
  const lineCount = assets.filter((a) =>
    ['line', 'minor_line', 'cable'].includes(a.asset_kind),
  ).length;
  const substationCount = assets.filter((a) => a.asset_kind === 'substation').length;

  return (
    <div className="fixed inset-0 overflow-hidden bg-surface-950">
      <LiveMap
        fix={gps.live}
        heading={heading}
        following={following}
        style={style}
        assets={assets}
        inspections={inspections}
        initialCenter={initialCenter.current}
        onViewportChange={loadViewport}
        onUserPan={() => setFollowing(false)}
        onSelectAsset={setSelected}
        onMapReady={(map) => {
          mapRef.current = map;
        }}
      />

      {/* --- Top status bar ------------------------------------------------ */}
      <div
        className="pointer-events-none absolute inset-x-0 top-0 z-[1000] flex items-start justify-between gap-2 p-3"
        style={{ paddingTop: 'max(env(safe-area-inset-top), 12px)' }}
      >
        <div className="pointer-events-auto flex items-center gap-2 rounded-full border border-white/10 bg-surface-900/90 px-3 py-2 backdrop-blur">
          <span
            aria-hidden
            className={`h-2 w-2 rounded-full ${
              verdict.tone === 'ok'
                ? 'bg-signal-ok'
                : verdict.tone === 'warn'
                  ? 'bg-signal-warn'
                  : 'bg-signal-danger animate-pulse'
            }`}
          />
          <span className="font-mono text-xs text-slate-200">
            {gps.live ? `±${gps.live.accuracy_m.toFixed(0)} m` : 'locating…'}
          </span>
          <span className="text-xs text-slate-500">·</span>
          <span className="font-mono text-xs text-slate-400">
            {lineCount} line{lineCount === 1 ? '' : 's'}
            {substationCount > 0 && ` · ${substationCount} sub`}
          </span>
          {loading && (
            <span
              aria-label="Loading"
              className="ml-1 h-3 w-3 animate-spin rounded-full border-2 border-grid-distribution border-t-transparent"
            />
          )}
        </div>

        <div className="pointer-events-auto flex overflow-hidden rounded-full border border-white/10 bg-surface-900/90 backdrop-blur">
          {(Object.keys(STYLE_LABEL) as BasemapStyle[]).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setStyle(key)}
              aria-pressed={style === key}
              className={`px-3 py-2 text-xs font-medium transition-colors ${
                style === key ? 'bg-grid-distribution text-surface-950' : 'text-slate-400 hover:text-slate-100'
              }`}
            >
              {STYLE_LABEL[key]}
            </button>
          ))}
        </div>
      </div>

      {/* --- Legend --------------------------------------------------------- */}
      <div className="pointer-events-none absolute left-3 top-20 z-[1000] rounded-xl border border-white/10 bg-surface-900/85 px-2.5 py-2 backdrop-blur">
        <ul className="space-y-1">
          {[
            { c: '#5eead4', l: '<1 kV' },
            { c: '#60a5fa', l: '1–35 kV' },
            { c: '#c084fc', l: '35–115 kV' },
            { c: '#fb923c', l: '115–345 kV' },
            { c: '#f87171', l: '>345 kV' },
            { c: '#7c8da0', l: 'untagged' },
          ].map((row) => (
            <li key={row.l} className="flex items-center gap-2 text-[10px] text-slate-300">
              <span aria-hidden className="h-1 w-4 rounded-full" style={{ backgroundColor: row.c }} />
              {row.l}
            </li>
          ))}
        </ul>
      </div>

      {/* --- Errors --------------------------------------------------------- */}
      {error && (
        <div
          role="status"
          className="pointer-events-none absolute inset-x-3 bottom-28 z-[1000] mx-auto max-w-md rounded-xl border border-signal-warn/40 bg-surface-900/95 p-3 text-xs leading-relaxed text-signal-warn backdrop-blur"
        >
          {error}
        </div>
      )}

      {gps.error && !gps.live && (
        <div className="absolute inset-x-6 top-1/2 z-[1100] mx-auto max-w-sm -translate-y-1/2 rounded-xl border border-white/10 bg-surface-900/95 p-4 text-center backdrop-blur">
          <p className="text-sm text-slate-200">{gps.error}</p>
          <button type="button" onClick={gps.request} className="btn-primary mt-3 w-full">
            Retry location
          </button>
        </div>
      )}

      {/* --- Controls ------------------------------------------------------- */}
      <div
        className="absolute bottom-0 right-3 z-[1000] flex flex-col items-end gap-2 pb-4"
        style={{ paddingBottom: 'max(env(safe-area-inset-bottom), 16px)' }}
      >
        <button
          type="button"
          onClick={() => mapRef.current?.zoomIn()}
          aria-label="Zoom in"
          className="flex h-11 w-11 items-center justify-center rounded-full border border-white/10 bg-surface-900/90 text-xl text-slate-200 backdrop-blur active:bg-surface-700"
        >
          +
        </button>
        <button
          type="button"
          onClick={() => mapRef.current?.zoomOut()}
          aria-label="Zoom out"
          className="flex h-11 w-11 items-center justify-center rounded-full border border-white/10 bg-surface-900/90 text-xl text-slate-200 backdrop-blur active:bg-surface-700"
        >
          −
        </button>
        <button
          type="button"
          onClick={recenter}
          disabled={!gps.live}
          aria-label={following ? 'Following your location' : 'Recentre on your location'}
          aria-pressed={following}
          className={`flex h-14 w-14 items-center justify-center rounded-full border shadow-lg backdrop-blur transition-colors disabled:opacity-40 ${
            following
              ? 'border-grid-distribution bg-grid-distribution text-surface-950'
              : 'border-white/10 bg-surface-900/90 text-slate-200'
          }`}
        >
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3.5" />
            <path d="M12 2v3M12 19v3M2 12h3M19 12h3" strokeLinecap="round" />
            <circle cx="12" cy="12" r="8" opacity="0.45" />
          </svg>
        </button>
      </div>

      {/* Attribution has to stay visible — it is a licence condition of the tiles. */}
      <p className="pointer-events-none absolute bottom-0 left-0 z-[1000] bg-surface-950/70 px-2 py-0.5 text-[9px] text-slate-500">
        © OpenStreetMap{sources.includes('hifld_transmission') ? ', HIFLD' : ''}
        {style === 'satellite' ? ', Esri' : ', CARTO'}
      </p>

      <AssetSheet asset={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
