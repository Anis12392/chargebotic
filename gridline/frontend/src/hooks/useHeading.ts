'use client';

import { useCallback, useEffect, useState } from 'react';

interface WebkitDeviceOrientationEvent extends DeviceOrientationEvent {
  webkitCompassHeading?: number;
  webkitCompassAccuracy?: number;
}

type DeviceOrientationEventConstructor = typeof DeviceOrientationEvent & {
  requestPermission?: () => Promise<'granted' | 'denied'>;
};

/**
 * Compass heading, which tells the backend which way the camera was pointing.
 *
 * Three sources, in descending order of trust:
 *   1. `webkitCompassHeading` (iOS) — already true north, already corrected.
 *   2. `deviceorientationabsolute` — absolute frame, alpha measured
 *      counter-clockwise from east, so the heading is 360 - alpha.
 *   3. `deviceorientation` with `absolute: true`.
 *
 * A relative-only orientation event is deliberately ignored: a heading with an
 * arbitrary zero is worse than no heading, because the backend would treat it
 * as real.
 */
export function useHeading(enabled = true) {
  const [heading, setHeading] = useState<number | null>(null);
  const [accuracy, setAccuracy] = useState<number | null>(null);
  const [needsPermission, setNeedsPermission] = useState(false);
  const [granted, setGranted] = useState(false);

  const handle = useCallback((event: DeviceOrientationEvent) => {
    const webkit = event as WebkitDeviceOrientationEvent;
    if (typeof webkit.webkitCompassHeading === 'number') {
      setHeading(((webkit.webkitCompassHeading % 360) + 360) % 360);
      setAccuracy(webkit.webkitCompassAccuracy ?? null);
      return;
    }
    if (event.absolute && typeof event.alpha === 'number') {
      setHeading(((360 - event.alpha) % 360 + 360) % 360);
      setAccuracy(null);
    }
  }, []);

  const requestPermission = useCallback(async () => {
    const ctor = (typeof DeviceOrientationEvent !== 'undefined'
      ? DeviceOrientationEvent
      : undefined) as DeviceOrientationEventConstructor | undefined;
    if (!ctor?.requestPermission) {
      setGranted(true);
      return true;
    }
    try {
      const result = await ctor.requestPermission();
      const ok = result === 'granted';
      setGranted(ok);
      setNeedsPermission(!ok);
      return ok;
    } catch {
      setNeedsPermission(true);
      return false;
    }
  }, []);

  useEffect(() => {
    if (!enabled || typeof window === 'undefined') return;

    const ctor = (typeof DeviceOrientationEvent !== 'undefined'
      ? DeviceOrientationEvent
      : undefined) as DeviceOrientationEventConstructor | undefined;

    // iOS 13+ gates the sensor behind a user gesture.
    if (ctor?.requestPermission && !granted) {
      setNeedsPermission(true);
      return;
    }

    window.addEventListener('deviceorientationabsolute', handle as EventListener);
    window.addEventListener('deviceorientation', handle as EventListener);
    return () => {
      window.removeEventListener('deviceorientationabsolute', handle as EventListener);
      window.removeEventListener('deviceorientation', handle as EventListener);
    };
  }, [enabled, granted, handle]);

  return { heading, accuracy, needsPermission, requestPermission };
}
