/**
 * Presentation helpers.
 *
 * The rule that governs this file: a number the backend flagged as an estimate
 * must never be rendered as if it were a measurement. That means ranges stay
 * ranges, units are always shown, and "unknown" is rendered as "unknown"
 * rather than as a dash the eye reads as zero.
 */

import type { PerchGrade, Severity, VoltageClass } from './types';

export function formatVolts(volts: number | null | undefined): string {
  if (volts === null || volts === undefined) return 'unknown';
  if (volts >= 1000) {
    const kv = volts / 1000;
    return `${Number.isInteger(kv) ? kv : kv.toFixed(2).replace(/\.?0+$/, '')} kV`;
  }
  return `${volts} V`;
}

export function formatVoltageList(volts: number[]): string {
  if (!volts.length) return 'none identified';
  return volts.map(formatVolts).join(' / ');
}

export function formatCurrentRange(
  low: number | null | undefined,
  high: number | null | undefined,
): string {
  if (low === null || low === undefined || high === null || high === undefined) {
    return 'not estimated';
  }
  return `${Math.round(low)}–${Math.round(high)} A`;
}

export function formatDistance(metres: number | null | undefined): string {
  if (metres === null || metres === undefined) return '—';
  if (metres < 1000) return `${Math.round(metres)} m`;
  return `${(metres / 1000).toFixed(2)} km`;
}

export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

/** Words, not just a number: 62% means different things to different readers. */
export function confidenceLabel(value: number): string {
  if (value >= 0.8) return 'high';
  if (value >= 0.6) return 'moderate';
  if (value >= 0.35) return 'low';
  if (value > 0) return 'very low';
  return 'none';
}

export function confidenceColor(value: number): string {
  if (value >= 0.8) return 'text-signal-ok';
  if (value >= 0.5) return 'text-signal-warn';
  return 'text-signal-danger';
}

export const VOLTAGE_CLASS_COLOR: Record<VoltageClass, string> = {
  secondary: '#5eead4',
  distribution: '#60a5fa',
  subtransmission: '#c084fc',
  transmission: '#fb923c',
  ehv: '#f87171',
  unknown: '#94a3b8',
};

export function voltageClassColor(cls: string | null | undefined): string {
  return VOLTAGE_CLASS_COLOR[(cls ?? 'unknown') as VoltageClass] ?? VOLTAGE_CLASS_COLOR.unknown;
}

export const PERCH_GRADE_COLOR: Record<PerchGrade, string> = {
  excellent: '#4ade80',
  good: '#a3e635',
  marginal: '#fbbf24',
  poor: '#fb923c',
  unsuitable: '#f87171',
};

export function severityStyle(severity: Severity): { border: string; text: string; icon: string } {
  switch (severity) {
    case 'danger':
      return { border: 'border-signal-danger/60', text: 'text-signal-danger', icon: '⚠' };
    case 'caution':
      return { border: 'border-signal-warn/60', text: 'text-signal-warn', icon: '!' };
    default:
      return { border: 'border-surface-600', text: 'text-slate-400', icon: 'i' };
  }
}

export function titleCase(value: string | null | undefined): string {
  if (!value) return 'Unknown';
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function formatCoords(lat: number, lon: number): string {
  return `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
}

export function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelative(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '—';
  const seconds = Math.round((Date.now() - then) / 1000);
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} h ago`;
  return `${Math.floor(seconds / 86400)} d ago`;
}

/** Compass point from a bearing — easier to act on in the field than degrees. */
export function compassPoint(bearing: number | null | undefined): string {
  if (bearing === null || bearing === undefined) return '—';
  const points = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
  const index = Math.round((((bearing % 360) + 360) % 360) / 22.5) % 16;
  return points[index] ?? '—';
}

export function formatMeasurement(
  estimate: { value: number | null; low: number | null; high: number | null; unit: string } | null,
): string {
  if (!estimate) return 'not estimated';
  const { value, low, high, unit } = estimate;
  if (low !== null && high !== null) return `${low}–${high} ${unit}`;
  if (value !== null) return `${value} ${unit}`;
  return 'not estimated';
}
