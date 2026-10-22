'use client';

import 'leaflet/dist/leaflet.css';

import L from 'leaflet';
import { useCallback, useEffect, useMemo, useRef } from 'react';
import { CircleMarker, MapContainer, Marker, Polyline, TileLayer, useMap, useMapEvents } from 'react-leaflet';

import type { Fix } from '@/hooks/useGeolocation';
import type { GISAsset, InspectionSummary } from '@/lib/types';

export type BasemapStyle = 'night' | 'day' | 'satellite';

const TILES: Record<BasemapStyle, { url: string; attribution: string; maxZoom: number }> = {
  // CARTO's dark basemap is the closest free equivalent to a navigation view:
  // desaturated ground, bright labels, so coloured overlays carry the meaning.
  night: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 20,
  },
  day: {
    url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 20,
  },
  // Aerial is genuinely useful here: you can trace a right-of-way through
  // vegetation that no basemap draws.
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; Esri, Maxar, Earthstar Geographics',
    maxZoom: 19,
  },
};

const LINE_KINDS = new Set(['line', 'minor_line', 'cable']);
const STRUCTURE_KINDS = new Set(['tower', 'pole', 'portal']);

/** Voltage-class colours, matched to the rest of the app. */
function voltageColor(volts: number | undefined): string {
  if (volts === undefined) return '#7c8da0';
  if (volts <= 1_000) return '#5eead4';
  if (volts <= 34_500) return '#60a5fa';
  if (volts <= 115_000) return '#c084fc';
  if (volts <= 345_000) return '#fb923c';
  return '#f87171';
}

/** Transmission lines are drawn heavier, the way a motorway outranks a lane. */
function lineWeight(volts: number | undefined): number {
  if (volts === undefined) return 3;
  if (volts <= 1_000) return 2.5;
  if (volts <= 34_500) return 3.5;
  if (volts <= 115_000) return 5;
  if (volts <= 345_000) return 6.5;
  return 8;
}

function assetLatLngs(asset: GISAsset): [number, number][][] {
  const geometry = asset.geometry;
  if (geometry?.type === 'MultiLineString') {
    return (geometry.coordinates as [number, number][][]).map((path) =>
      path.map(([lon, lat]) => [lat, lon] as [number, number]),
    );
  }
  if (geometry?.type === 'LineString') {
    return [(geometry.coordinates as [number, number][]).map(([lon, lat]) => [lat, lon] as [number, number])];
  }
  return [];
}

/**
 * The position puck.
 *
 * A plain dot cannot show which way you are facing, and facing is the whole
 * point when the thing you are looking for is a line overhead. The chevron
 * rotates with the compass; when there is no heading it falls back to a dot so
 * it never implies a direction it does not know.
 */
function puckIcon(heading: number | null, following: boolean): L.DivIcon {
  const ring = following ? '#38bdf8' : '#7c8da0';
  const body =
    heading === null
      ? `<span style="display:block;width:18px;height:18px;border-radius:9999px;background:${ring};
           border:3px solid #0b0e13;box-shadow:0 0 0 6px ${ring}33,0 2px 8px rgba(0,0,0,.6)"></span>`
      : `<span style="display:block;width:34px;height:34px;transform:rotate(${heading}deg);
           transition:transform .25s ease-out">
           <svg viewBox="0 0 34 34" width="34" height="34">
             <circle cx="17" cy="17" r="15" fill="${ring}22"/>
             <path d="M17 3 L26 27 L17 21.5 L8 27 Z" fill="${ring}" stroke="#0b0e13" stroke-width="2"
                   stroke-linejoin="round"/>
           </svg>
         </span>`;
  return L.divIcon({ className: '', html: body, iconSize: [34, 34], iconAnchor: [17, 17] });
}

/** Keeps the map centred on the user while follow mode is on. */
function FollowController({ fix, following }: { fix: Fix | null; following: boolean }) {
  const map = useMap();
  const lastPan = useRef(0);

  useEffect(() => {
    if (!following || !fix) return;
    // Throttle: a high-accuracy watch can fire several times a second, and
    // panning on every one makes the map judder rather than glide.
    const now = Date.now();
    if (now - lastPan.current < 700) return;
    lastPan.current = now;
    map.panTo([fix.latitude, fix.longitude], { animate: true, duration: 0.6 });
  }, [fix, following, map]);

  return null;
}

/** Reports viewport changes so the page can load data for where you are looking. */
function ViewportWatcher({
  onChange,
  onUserPan,
}: {
  onChange: (center: { lat: number; lon: number }, radiusM: number) => void;
  onUserPan: () => void;
}) {
  const map = useMap();
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const report = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    // Debounced: panning fires continuously, and every fetch is an Overpass
    // query somebody else pays for.
    timer.current = setTimeout(() => {
      const center = map.getCenter();
      const bounds = map.getBounds();
      // Radius that covers the visible corner, so nothing on screen is missing.
      const radius = Math.min(5000, Math.round(center.distanceTo(bounds.getNorthEast())));
      onChange({ lat: center.lat, lon: center.lng }, Math.max(150, radius));
    }, 600);
  }, [map, onChange]);

  useMapEvents({
    moveend: report,
    zoomend: report,
    dragstart: onUserPan,
  });

  useEffect(() => {
    report();
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [report]);

  return null;
}

export interface LiveMapProps {
  fix: Fix | null;
  heading: number | null;
  following: boolean;
  style: BasemapStyle;
  assets: GISAsset[];
  inspections: InspectionSummary[];
  initialCenter: { lat: number; lon: number };
  onViewportChange: (center: { lat: number; lon: number }, radiusM: number) => void;
  onUserPan: () => void;
  onSelectAsset: (asset: GISAsset) => void;
  onMapReady: (map: L.Map) => void;
}

export default function LiveMap({
  fix,
  heading,
  following,
  style,
  assets,
  inspections,
  initialCenter,
  onViewportChange,
  onUserPan,
  onSelectAsset,
  onMapReady,
}: LiveMapProps) {
  const tiles = TILES[style];

  const { lines, structures, substations } = useMemo(
    () => ({
      lines: assets.filter((a) => LINE_KINDS.has(a.asset_kind)),
      structures: assets.filter((a) => STRUCTURE_KINDS.has(a.asset_kind)),
      substations: assets.filter((a) => a.asset_kind === 'substation'),
    }),
    [assets],
  );

  return (
    <MapContainer
      center={[initialCenter.lat, initialCenter.lon]}
      zoom={17}
      zoomControl={false}
      attributionControl={false}
      // Canvas rendering: a dense urban query can return hundreds of features,
      // and one SVG node each turns panning into a slideshow on a phone.
      preferCanvas
      style={{ position: 'absolute', inset: 0, background: '#0b0e13' }}
      ref={(map) => {
        if (map) onMapReady(map);
      }}
    >
      <TileLayer url={tiles.url} attribution={tiles.attribution} maxZoom={tiles.maxZoom} />

      <FollowController fix={fix} following={following} />
      <ViewportWatcher onChange={onViewportChange} onUserPan={onUserPan} />

      {/* Lines, drawn with a dark casing underneath so they read against any
          basemap — the same trick road maps use. */}
      {lines.map((asset) =>
        assetLatLngs(asset).map((path, index) => {
          const volts = asset.voltage_v[0];
          return (
            <Polyline
              key={`casing-${asset.element_id}-${index}`}
              positions={path}
              pathOptions={{
                color: '#05070a',
                weight: lineWeight(volts) + 3,
                opacity: 0.9,
                lineCap: 'round',
              }}
              interactive={false}
            />
          );
        }),
      )}
      {lines.map((asset) =>
        assetLatLngs(asset).map((path, index) => {
          const volts = asset.voltage_v[0];
          return (
            <Polyline
              key={`line-${asset.element_id}-${index}`}
              positions={path}
              pathOptions={{
                color: voltageColor(volts),
                weight: lineWeight(volts),
                opacity: 1,
                lineCap: 'round',
              }}
              eventHandlers={{ click: () => onSelectAsset(asset) }}
            />
          );
        }),
      )}

      {/* Lines with no geometry still deserve a mark at their centre. */}
      {lines
        .filter((a) => assetLatLngs(a).length === 0 && a.latitude !== null && a.longitude !== null)
        .map((asset) => (
          <CircleMarker
            key={`pin-${asset.element_id}`}
            center={[asset.latitude!, asset.longitude!]}
            radius={6}
            pathOptions={{
              color: '#05070a',
              weight: 2,
              fillColor: voltageColor(asset.voltage_v[0]),
              fillOpacity: 1,
            }}
            eventHandlers={{ click: () => onSelectAsset(asset) }}
          />
        ))}

      {structures.map((asset) =>
        asset.latitude !== null && asset.longitude !== null ? (
          <CircleMarker
            key={`st-${asset.element_type}-${asset.element_id}`}
            center={[asset.latitude!, asset.longitude!]}
            radius={4}
            pathOptions={{
              color: '#05070a',
              weight: 1.5,
              fillColor: '#cbd5e1',
              fillOpacity: 0.95,
            }}
            eventHandlers={{ click: () => onSelectAsset(asset) }}
          />
        ) : null,
      )}

      {substations.map((asset) =>
        asset.latitude !== null && asset.longitude !== null ? (
          <CircleMarker
            key={`sub-${asset.element_id}`}
            center={[asset.latitude!, asset.longitude!]}
            radius={11}
            pathOptions={{
              color: '#fb923c',
              weight: 3,
              fillColor: '#fb923c',
              fillOpacity: 0.28,
            }}
            eventHandlers={{ click: () => onSelectAsset(asset) }}
          />
        ) : null,
      )}

      {inspections.map((inspection) => (
        <CircleMarker
          key={inspection.id}
          center={[inspection.latitude, inspection.longitude]}
          radius={7}
          pathOptions={{
            color: '#0b0e13',
            weight: 2,
            fillColor: '#4ade80',
            fillOpacity: 0.9,
          }}
        />
      ))}

      {/* Accuracy halo, then the puck on top. */}
      {fix && (
        <CircleMarker
          center={[fix.latitude, fix.longitude]}
          radius={Math.max(14, Math.min(60, fix.accuracy_m))}
          pathOptions={{ color: '#38bdf8', weight: 1, opacity: 0.35, fillOpacity: 0.08 }}
          interactive={false}
        />
      )}
      {fix && (
        <Marker
          position={[fix.latitude, fix.longitude]}
          icon={puckIcon(heading, following)}
          zIndexOffset={1000}
          interactive={false}
        />
      )}
    </MapContainer>
  );
}
