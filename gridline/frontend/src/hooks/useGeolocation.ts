'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export interface Fix {
  latitude: number;
  longitude: number;
  accuracy_m: number;
  altitude_m: number | null;
  altitude_accuracy_m: number | null;
  heading_deg: number | null;
  speed_ms: number | null;
  timestamp: number;
}

export type PermissionState = 'unknown' | 'prompt' | 'granted' | 'denied' | 'unsupported';

interface State {
  fix: Fix | null;
  error: string | null;
  permission: PermissionState;
  watching: boolean;
}

/**
 * Continuous GPS watch.
 *
 * `watchPosition` rather than `getCurrentPosition` because accuracy improves
 * over the first few seconds as the receiver acquires more satellites, and the
 * whole GIS match hinges on that accuracy. The hook keeps the best fix it has
 * seen recently rather than the newest one, since a momentary degradation
 * (walking under a canopy) should not throw away a good fix.
 */
export function useGeolocation(enabled = true): State & { request: () => void } {
  const [state, setState] = useState<State>({
    fix: null,
    error: null,
    permission: 'unknown',
    watching: false,
  });
  const watchId = useRef<number | null>(null);
  const bestFix = useRef<Fix | null>(null);

  const handlePosition = useCallback((position: GeolocationPosition) => {
    const fix: Fix = {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy_m: position.coords.accuracy,
      altitude_m: position.coords.altitude,
      altitude_accuracy_m: position.coords.altitudeAccuracy,
      heading_deg: Number.isFinite(position.coords.heading) ? position.coords.heading : null,
      speed_ms: Number.isFinite(position.coords.speed) ? position.coords.speed : null,
      timestamp: position.timestamp,
    };

    const previous = bestFix.current;
    const previousIsStale = previous ? fix.timestamp - previous.timestamp > 20_000 : true;
    const isBetter = !previous || previousIsStale || fix.accuracy_m <= previous.accuracy_m;
    if (isBetter) bestFix.current = fix;

    setState((current) => ({
      ...current,
      fix: bestFix.current,
      error: null,
      permission: 'granted',
      watching: true,
    }));
  }, []);

  const handleError = useCallback((error: GeolocationPositionError) => {
    const message =
      error.code === error.PERMISSION_DENIED
        ? 'Location permission denied. GridLine cannot match GIS data without it.'
        : error.code === error.POSITION_UNAVAILABLE
          ? 'Position unavailable. Move into open sky and try again.'
          : 'Location request timed out.';
    setState((current) => ({
      ...current,
      error: message,
      permission: error.code === error.PERMISSION_DENIED ? 'denied' : current.permission,
      watching: false,
    }));
  }, []);

  const request = useCallback(() => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setState((current) => ({ ...current, permission: 'unsupported', error: 'Geolocation is not supported by this browser.' }));
      return;
    }
    if (watchId.current !== null) navigator.geolocation.clearWatch(watchId.current);
    watchId.current = navigator.geolocation.watchPosition(handlePosition, handleError, {
      enableHighAccuracy: true,
      maximumAge: 0,
      timeout: 20_000,
    });
    setState((current) => ({ ...current, watching: true }));
  }, [handleError, handlePosition]);

  useEffect(() => {
    if (!enabled) return;
    request();
    return () => {
      if (watchId.current !== null && typeof navigator !== 'undefined') {
        navigator.geolocation.clearWatch(watchId.current);
        watchId.current = null;
      }
    };
  }, [enabled, request]);

  useEffect(() => {
    if (typeof navigator === 'undefined' || !navigator.permissions?.query) return;
    let cancelled = false;
    navigator.permissions
      .query({ name: 'geolocation' as PermissionName })
      .then((status) => {
        if (cancelled) return;
        setState((current) => ({ ...current, permission: status.state as PermissionState }));
        status.onchange = () => {
          setState((current) => ({ ...current, permission: status.state as PermissionState }));
        };
      })
      .catch(() => {
        // Permissions API is not universally available; the watch itself will
        // surface a denial anyway.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { ...state, request };
}

/** Human-readable verdict on whether a fix is good enough to trust. */
export function accuracyVerdict(accuracy: number | null | undefined): {
  label: string;
  tone: 'ok' | 'warn' | 'danger';
} {
  if (accuracy === null || accuracy === undefined) return { label: 'no fix', tone: 'danger' };
  if (accuracy <= 10) return { label: 'good', tone: 'ok' };
  if (accuracy <= 30) return { label: 'usable', tone: 'warn' };
  return { label: 'poor — GIS match unreliable', tone: 'danger' };
}
