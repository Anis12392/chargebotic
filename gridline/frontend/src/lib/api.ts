/**
 * API client.
 *
 * Requests go to the same origin (`/api/...`) and Next rewrites them to the
 * backend, so the PWA has exactly one origin and the service worker does not
 * have to reason about cross-origin caching.
 */

import type {
  AdminStats,
  CaptureContext,
  EngineeringReport,
  InspectionDetail,
  InspectionSummary,
  MapResponse,
  VerificationRead,
  VerifyRequest,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_PATH ?? '/api';

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }

  /** Wording a field user can act on, rather than an HTTP status. */
  get userMessage(): string {
    switch (this.status) {
      case 413:
        return 'That photo is too large. Try again — the app will downscale it.';
      case 415:
        return 'That file is not a photo the app can read. Use the camera.';
      case 429:
        return 'Too many analyses in a short window. Wait a moment and retry.';
      case 0:
        return 'No connection to the analysis service. The capture is saved and will retry.';
      default:
        return this.detail || 'The analysis service returned an error.';
    }
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { Accept: 'application/json', ...(init?.headers ?? {}) },
    });
  } catch (error) {
    throw new ApiError(0, error instanceof Error ? error.message : 'Network request failed');
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body?.detail === 'string') detail = body.detail;
      else if (Array.isArray(body?.detail)) {
        detail = body.detail.map((d: { msg?: string }) => d.msg ?? '').join('; ') || detail;
      }
    } catch {
      // Body was not JSON; the status-derived message stands.
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function analyzePhoto(
  photo: Blob,
  capture: CaptureContext,
  options: { includePerchScore?: boolean; gisRadiusM?: number; signal?: AbortSignal } = {},
): Promise<EngineeringReport> {
  const form = new FormData();
  form.append('photo', photo, 'capture.jpg');
  form.append('capture', JSON.stringify(capture));
  form.append('include_perch_score', String(options.includePerchScore ?? true));
  if (options.gisRadiusM) form.append('gis_radius_m', String(options.gisRadiusM));

  return request<EngineeringReport>('/analyze', {
    method: 'POST',
    body: form,
    signal: options.signal,
  });
}

export function getInspection(id: string): Promise<InspectionDetail> {
  return request<InspectionDetail>(`/inspection/${encodeURIComponent(id)}`);
}

export function listInspections(
  params: {
    limit?: number;
    offset?: number;
    verifiedOnly?: boolean;
    voltageClass?: string;
    utility?: string;
    minPerchScore?: number;
  } = {},
): Promise<InspectionSummary[]> {
  const query = new URLSearchParams();
  if (params.limit) query.set('limit', String(params.limit));
  if (params.offset) query.set('offset', String(params.offset));
  if (params.verifiedOnly) query.set('verified_only', 'true');
  if (params.voltageClass) query.set('voltage_class', params.voltageClass);
  if (params.utility) query.set('utility', params.utility);
  if (params.minPerchScore !== undefined) query.set('min_perch_score', String(params.minPerchScore));
  return request<InspectionSummary[]>(`/inspections?${query.toString()}`);
}

export function getPerchRanking(minScore = 0, limit = 25): Promise<InspectionSummary[]> {
  return request<InspectionSummary[]>(`/perch/ranking?min_score=${minScore}&limit=${limit}`);
}

export function submitVerification(body: VerifyRequest): Promise<VerificationRead> {
  return request<VerificationRead>('/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function getMap(
  lat: number,
  lon: number,
  radiusM = 800,
  includeInspections = true,
): Promise<MapResponse> {
  const query = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    radius_m: String(radiusM),
    include_inspections: String(includeInspections),
  });
  return request<MapResponse>(`/map?${query.toString()}`);
}

export function getAdminStats(adminKey?: string, days = 30): Promise<AdminStats> {
  return request<AdminStats>(`/admin/stats?days=${days}`, {
    headers: adminKey ? { 'X-Admin-Key': adminKey } : {},
  });
}

export function trainingDataUrl(onlyCorrections = false): string {
  return `${API_BASE}/admin/training-data.jsonl?only_corrections=${onlyCorrections}`;
}
