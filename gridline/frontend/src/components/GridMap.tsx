'use client';

import 'leaflet/dist/leaflet.css';

import L from 'leaflet';
import { useEffect, useMemo } from 'react';
import {
  CircleMarker,
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet';

import {
  compassPoint,
  formatDistance,
  formatVoltageList,
  titleCase,
  voltageClassColor,
} from '@/lib/format';
import type { GISAsset, InspectionSummary } from '@/lib/types';

const LINE_KINDS = new Set(['line', 'minor_line', 'cable']);
const STRUCTURE_KINDS = new Set(['tower', 'pole', 'portal']);

/** Colour a mapped asset by the voltage class its tag implies. */
function assetColor(asset: GISAsset): string {
  const volts = asset.voltage_v[0];
  if (volts === undefined) return '#64748b';
  if (volts <= 1000) return voltageClassColor('secondary');
  if (volts <= 34_500) return voltageClassColor('distribution');
  if (volts <= 115_000) return voltageClassColor('subtransmission');
  if (volts <= 345_000) return voltageClassColor('transmission');
  return voltageClassColor('ehv');
}

function userIcon(): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<span style="display:block;width:16px;height:16px;border-radius:9999px;
      background:#60a5fa;border:3px solid #0d1117;box-shadow:0 0 0 4px rgba(96,165,250,.25)"></span>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

function Recenter({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lon], map.getZoom(), { animate: true });
  }, [lat, lon, map]);
  return null;
}

export interface GridMapProps {
  center: { lat: number; lon: number };
  assets: GISAsset[];
  inspections: InspectionSummary[];
  radiusM: number;
  photoLocation?: { lat: number; lon: number } | null;
  onSelectInspection?: (id: string) => void;
  height?: string;
}

export default function GridMap({
  center,
  assets,
  inspections,
  radiusM,
  photoLocation,
  onSelectInspection,
  height = '60dvh',
}: GridMapProps) {
  const { lines, structures, substations } = useMemo(() => {
    return {
      lines: assets.filter((a) => LINE_KINDS.has(a.asset_kind)),
      structures: assets.filter((a) => STRUCTURE_KINDS.has(a.asset_kind)),
      substations: assets.filter((a) => a.asset_kind === 'substation'),
    };
  }, [assets]);

  return (
    <MapContainer
      center={[center.lat, center.lon]}
      zoom={17}
      scrollWheelZoom
      style={{ height, width: '100%' }}
      className="overflow-hidden rounded-xl border border-surface-700"
    >
      <TileLayer
        // OSM standard tiles: the same survey that supplies the power tags, so
        // what the map draws and what the engine reasons over always agree.
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={19}
      />

      <Recenter lat={center.lat} lon={center.lon} />

      {/* Search radius */}
      <CircleMarker
        center={[center.lat, center.lon]}
        radius={2}
        pathOptions={{ color: '#60a5fa', opacity: 0.4 }}
      />

      {/* Transmission corridors and distribution lines from GIS geometry */}
      {lines.map((asset) => {
        const geometry = asset.geometry;
        if (geometry?.type === 'MultiLineString') {
          const paths = geometry.coordinates as [number, number][][];
          return paths.map((path, index) => (
            <Polyline
              key={`${asset.element_id}-${index}`}
              positions={path.map(([lon, lat]) => [lat, lon] as [number, number])}
              pathOptions={{ color: assetColor(asset), weight: 3, opacity: 0.85 }}
            >
              <AssetPopup asset={asset} />
            </Polyline>
          ));
        }
        if (asset.latitude === null || asset.longitude === null) return null;
        return (
          <CircleMarker
            key={asset.element_id}
            center={[asset.latitude!, asset.longitude!]}
            radius={6}
            pathOptions={{ color: assetColor(asset), fillOpacity: 0.6 }}
          >
            <AssetPopup asset={asset} />
          </CircleMarker>
        );
      })}

      {structures.map((asset) =>
        asset.latitude !== null && asset.longitude !== null ? (
          <CircleMarker
            key={`${asset.element_type}-${asset.element_id}`}
            center={[asset.latitude!, asset.longitude!]}
            radius={3.5}
            pathOptions={{ color: '#94a3b8', fillColor: '#94a3b8', fillOpacity: 0.8, weight: 1 }}
          >
            <AssetPopup asset={asset} />
          </CircleMarker>
        ) : null,
      )}

      {substations.map((asset) =>
        asset.latitude !== null && asset.longitude !== null ? (
          <CircleMarker
            key={`sub-${asset.element_id}`}
            center={[asset.latitude!, asset.longitude!]}
            radius={9}
            pathOptions={{ color: '#fb923c', fillColor: '#fb923c', fillOpacity: 0.25, weight: 2 }}
          >
            <AssetPopup asset={asset} />
          </CircleMarker>
        ) : null,
      )}

      {/* Previous inspections, coloured by predicted class */}
      {inspections.map((inspection) => (
        <CircleMarker
          key={inspection.id}
          center={[inspection.latitude, inspection.longitude]}
          radius={7}
          pathOptions={{
            color: voltageClassColor(inspection.predicted_voltage_class),
            fillColor: voltageClassColor(inspection.predicted_voltage_class),
            fillOpacity: inspection.is_verified ? 0.85 : 0.35,
            weight: 2,
          }}
          eventHandlers={{ click: () => onSelectInspection?.(inspection.id) }}
        >
          <Popup>
            <div className="text-xs">
              <p className="font-semibold">
                {titleCase(inspection.predicted_voltage_class ?? 'unknown')}
              </p>
              <p>{inspection.predicted_utility ?? 'Utility not attributed'}</p>
              <p>Confidence {Math.round(inspection.overall_confidence * 100)}%</p>
              {inspection.perch_score !== null && <p>Perch {inspection.perch_score.toFixed(0)}/100</p>}
              <p className="mt-1 opacity-70">{inspection.is_verified ? 'Verified' : 'Unverified'}</p>
            </div>
          </Popup>
        </CircleMarker>
      ))}

      {/* Where the operator is standing */}
      <Marker position={[center.lat, center.lon]} icon={userIcon()}>
        <Popup>
          <span className="text-xs">Your location · search radius {radiusM} m</span>
        </Popup>
      </Marker>

      {photoLocation && (
        <CircleMarker
          center={[photoLocation.lat, photoLocation.lon]}
          radius={8}
          pathOptions={{ color: '#f8fafc', weight: 2, fillOpacity: 0 }}
        >
          <Popup>
            <span className="text-xs">Photo location</span>
          </Popup>
        </CircleMarker>
      )}
    </MapContainer>
  );
}

function AssetPopup({ asset }: { asset: GISAsset }) {
  return (
    <Popup>
      <div className="text-xs leading-relaxed">
        <p className="font-semibold">{titleCase(asset.asset_kind)}</p>
        {asset.name && <p>{asset.name}</p>}
        {asset.operator && <p>Operator: {asset.operator}</p>}
        {asset.voltage_v.length > 0 && <p>Voltage: {formatVoltageList(asset.voltage_v)}</p>}
        {asset.ref && <p>Ref: {asset.ref}</p>}
        {asset.circuits && <p>Circuits: {asset.circuits}</p>}
        <p className="mt-1 opacity-70">
          {formatDistance(asset.distance_m)} {compassPoint(asset.bearing_deg)} · {asset.source}
        </p>
      </div>
    </Popup>
  );
}
