'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { ReportView } from '@/components/ReportView';
import { useCamera } from '@/hooks/useCamera';
import { accuracyVerdict, useGeolocation } from '@/hooks/useGeolocation';
import { useHeading } from '@/hooks/useHeading';
import { ApiError, analyzePhoto } from '@/lib/api';
import { compassPoint } from '@/lib/format';
import { enqueueCapture, listPending, recordFailure, removePending } from '@/lib/queue';
import type { CaptureContext, EngineeringReport } from '@/lib/types';

type Phase = 'permissions' | 'live' | 'analysing' | 'report';

export default function CapturePage() {
  const camera = useCamera();
  const gps = useGeolocation(true);
  const compass = useHeading(true);

  const [phase, setPhase] = useState<Phase>('permissions');
  const [report, setReport] = useState<EngineeringReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [queued, setQueued] = useState(0);
  const [preview, setPreview] = useState<string | null>(null);
  const [notes, setNotes] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const refreshQueue = useCallback(async () => {
    setQueued((await listPending()).length);
  }, []);

  useEffect(() => {
    void refreshQueue();
  }, [refreshQueue]);

  /**
   * Drain the offline queue.
   *
   * Runs on mount and whenever the browser reports it is back online. Uploads
   * are sequential rather than parallel: a crew returning to signal after an
   * hour in the field may have twenty captures queued, and firing twenty vision
   * calls at once is how you get rate-limited into failing all of them.
   */
  useEffect(() => {
    let draining = false;

    const drain = async () => {
      if (draining || typeof navigator === 'undefined' || !navigator.onLine) return;
      draining = true;
      try {
        for (const entry of await listPending()) {
          // A capture that has failed repeatedly is left for manual review
          // rather than retried forever against a bill-per-call API.
          if (entry.attempts >= 5) continue;
          try {
            await analyzePhoto(entry.photo, entry.capture);
            await removePending(entry.id);
          } catch (err) {
            await recordFailure(entry.id, err instanceof ApiError ? err.detail : String(err));
            if (err instanceof ApiError && err.status === 0) break; // offline again
          }
        }
        await refreshQueue();
        navigator.serviceWorker?.controller?.postMessage({ type: 'INVALIDATE_DATA_CACHE' });
      } finally {
        draining = false;
      }
    };

    void drain();
    window.addEventListener('online', drain);
    return () => window.removeEventListener('online', drain);
  }, [refreshQueue]);

  useEffect(() => () => abortRef.current?.abort(), []);
  useEffect(() => {
    if (preview) return () => URL.revokeObjectURL(preview);
    return undefined;
  }, [preview]);

  const buildCaptureContext = useCallback((): CaptureContext | null => {
    if (!gps.fix) return null;
    return {
      latitude: gps.fix.latitude,
      longitude: gps.fix.longitude,
      accuracy_m: gps.fix.accuracy_m,
      altitude_m: gps.fix.altitude_m,
      altitude_accuracy_m: gps.fix.altitude_accuracy_m,
      // Prefer the compass over the GPS course: course is only meaningful while
      // moving, and the operator is standing still under the pole.
      heading_deg: compass.heading ?? gps.fix.heading_deg,
      speed_ms: gps.fix.speed_ms,
      captured_at: new Date().toISOString(),
      device_model: typeof navigator !== 'undefined' ? navigator.userAgent.slice(0, 120) : null,
      notes: notes.trim() || null,
    };
  }, [compass.heading, gps.fix, notes]);

  const submit = useCallback(
    async (photo: Blob, capture: CaptureContext) => {
      // Persist first, upload second: a dropped connection or a killed tab must
      // never cost the operator the photograph.
      const pending = await enqueueCapture(capture, photo).catch(() => null);
      await refreshQueue();

      setPhase('analysing');
      setError(null);
      abortRef.current = new AbortController();

      try {
        const result = await analyzePhoto(photo, capture, { signal: abortRef.current.signal });
        if (pending) await removePending(pending.id);
        await refreshQueue();
        setReport(result);
        setPhase('report');
        camera.stop();
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          setPhase('live');
          return;
        }
        const apiError = err instanceof ApiError ? err : new ApiError(0, String(err));
        if (pending) await recordFailure(pending.id, apiError.detail);
        await refreshQueue();
        setError(apiError.userMessage);
        setPhase('live');
      }
    },
    [camera, refreshQueue],
  );

  const onShutter = useCallback(async () => {
    const capture = buildCaptureContext();
    if (!capture) {
      setError('Waiting for a GPS fix. The report depends on it, so capture is held until one arrives.');
      return;
    }
    const photo = await camera.capture();
    if (!photo) {
      setError('The camera did not return a frame. Try again.');
      return;
    }
    setPreview(URL.createObjectURL(photo));
    await submit(photo, capture);
  }, [buildCaptureContext, camera, submit]);

  const onFilePicked = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      event.target.value = '';
      if (!file) return;
      const capture = buildCaptureContext();
      if (!capture) {
        setError('Waiting for a GPS fix before the photo can be analysed.');
        return;
      }
      setPreview(URL.createObjectURL(file));
      await submit(file, capture);
    },
    [buildCaptureContext, submit],
  );

  const reset = useCallback(() => {
    setReport(null);
    setPreview(null);
    setError(null);
    setNotes('');
    setPhase('live');
    void camera.start();
  }, [camera]);

  const startSession = useCallback(async () => {
    if (compass.needsPermission) await compass.requestPermission();
    gps.request();
    await camera.start();
    setPhase('live');
  }, [camera, compass, gps]);

  if (phase === 'report' && report) {
    return (
      <div className="px-4 pt-4">
        <ReportView report={report} localPhotoUrl={preview} />
        <button type="button" onClick={reset} className="btn-primary mt-6 w-full">
          Capture another
        </button>
      </div>
    );
  }

  if (phase === 'permissions') {
    return (
      <PermissionsGate
        cameraStatus={camera.status}
        cameraError={camera.error}
        gpsPermission={gps.permission}
        gpsError={gps.error}
        compassNeedsPermission={compass.needsPermission}
        onStart={startSession}
      />
    );
  }

  const verdict = accuracyVerdict(gps.fix?.accuracy_m);

  return (
    <div className="relative">
      <div className="relative aspect-[3/4] w-full overflow-hidden bg-black">
        <video
          ref={camera.setVideoElement}
          playsInline
          muted
          autoPlay
          className="h-full w-full object-cover"
        />

        {/* Framing guide: the crossarm and insulator band is where the
            dimensional evidence lives, so the UI asks for it explicitly. */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute inset-x-6 top-[18%] h-[34%] rounded-md border-2 border-dashed border-white/40" />
          <p className="absolute inset-x-0 top-[54%] text-center text-[11px] font-medium uppercase tracking-wider text-white/70">
            Frame the crossarm and insulators here
          </p>
        </div>

        <div className="absolute inset-x-0 top-0 flex items-start justify-between gap-2 bg-gradient-to-b from-black/70 to-transparent p-3 text-[11px]">
          <Telemetry
            gpsLabel={
              gps.fix ? `${gps.fix.latitude.toFixed(5)}, ${gps.fix.longitude.toFixed(5)}` : 'acquiring…'
            }
            accuracy={gps.fix ? `±${gps.fix.accuracy_m.toFixed(0)} m · ${verdict.label}` : '—'}
            accuracyTone={verdict.tone}
            heading={
              compass.heading !== null
                ? `${compass.heading.toFixed(0)}° ${compassPoint(compass.heading)}`
                : 'no compass'
            }
            altitude={gps.fix?.altitude_m !== null && gps.fix?.altitude_m !== undefined ? `${gps.fix.altitude_m.toFixed(0)} m` : '—'}
          />
          {queued > 0 && (
            <span className="rounded-full bg-signal-warn/20 px-2 py-1 font-semibold text-signal-warn">
              {queued} queued
            </span>
          )}
        </div>

        {phase === 'analysing' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/80">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-grid-distribution border-t-transparent" />
            <p className="text-sm font-medium text-slate-200">Analysing image and location…</p>
            <p className="max-w-[16rem] text-center text-xs text-slate-500">
              Vision inventory and GIS lookup run in parallel. This normally takes a few seconds.
            </p>
            <button
              type="button"
              onClick={() => abortRef.current?.abort()}
              className="btn-ghost text-xs"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      <div className="px-4 pt-4">
        {error && (
          <p
            role="alert"
            className="mb-3 rounded-lg border border-signal-danger/50 bg-signal-danger/10 p-3 text-sm text-signal-danger"
          >
            {error}
          </p>
        )}

        <label className="label" htmlFor="capture-notes">
          Field notes (optional)
        </label>
        <input
          id="capture-notes"
          type="text"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Pole tag, circuit name, anything the photo misses"
          className="field mt-1"
        />

        <div className="mt-4 flex items-center gap-3">
          <button
            type="button"
            onClick={onShutter}
            disabled={phase === 'analysing' || camera.status !== 'live' || !gps.fix}
            className="btn-primary flex-1 py-4 text-base"
          >
            {gps.fix ? 'Capture' : 'Waiting for GPS…'}
          </button>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="btn-secondary px-4 py-4"
            aria-label="Attach an existing photo"
          >
            Attach
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={onFilePicked}
            className="hidden"
          />
        </div>

        {camera.resolution && (
          <p className="mt-2 text-center text-[11px] text-slate-600">
            Capturing at {camera.resolution.width}×{camera.resolution.height}
          </p>
        )}
      </div>
    </div>
  );
}

function Telemetry({
  gpsLabel,
  accuracy,
  accuracyTone,
  heading,
  altitude,
}: {
  gpsLabel: string;
  accuracy: string;
  accuracyTone: 'ok' | 'warn' | 'danger';
  heading: string;
  altitude: string;
}) {
  const toneClass =
    accuracyTone === 'ok'
      ? 'text-signal-ok'
      : accuracyTone === 'warn'
        ? 'text-signal-warn'
        : 'text-signal-danger';

  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-0.5 font-mono text-white/80">
      <div className="col-span-2">
        <dt className="sr-only">Coordinates</dt>
        <dd>{gpsLabel}</dd>
      </div>
      <div>
        <dt className="sr-only">GPS accuracy</dt>
        <dd className={toneClass}>{accuracy}</dd>
      </div>
      <div>
        <dt className="sr-only">Heading</dt>
        <dd>{heading}</dd>
      </div>
      <div>
        <dt className="sr-only">Altitude</dt>
        <dd>{altitude}</dd>
      </div>
    </dl>
  );
}

function PermissionsGate({
  cameraStatus,
  cameraError,
  gpsPermission,
  gpsError,
  compassNeedsPermission,
  onStart,
}: {
  cameraStatus: string;
  cameraError: string | null;
  gpsPermission: string;
  gpsError: string | null;
  compassNeedsPermission: boolean;
  onStart: () => void;
}) {
  return (
    <div className="px-4 pt-8">
      <h1 className="text-2xl font-bold text-slate-50">Two permissions</h1>
      <p className="mt-2 text-sm leading-relaxed text-slate-400">
        GridLine needs the camera and your location. Neither is optional: the photograph supplies
        the construction evidence and the GPS fix is what ties it to mapped infrastructure. Without
        both, the report would be a guess.
      </p>

      <ul className="mt-6 space-y-3">
        <PermissionRow
          title="Camera"
          detail="Rear camera, still frames only. Nothing is recorded."
          state={cameraStatus === 'live' ? 'granted' : cameraStatus === 'denied' ? 'denied' : 'pending'}
          error={cameraError}
        />
        <PermissionRow
          title="Location"
          detail="High-accuracy GPS, watched continuously while the viewfinder is open."
          state={gpsPermission === 'granted' ? 'granted' : gpsPermission === 'denied' ? 'denied' : 'pending'}
          error={gpsError}
        />
        <PermissionRow
          title="Compass"
          detail="Optional. Records which way the camera was pointing."
          state={compassNeedsPermission ? 'pending' : 'granted'}
          error={null}
        />
      </ul>

      <button type="button" onClick={onStart} className="btn-primary mt-8 w-full py-4 text-base">
        Grant and open viewfinder
      </button>

      <p className="mt-4 text-xs leading-relaxed text-slate-500">
        Photos are uploaded for analysis and stored with their location. EXIF metadata is stripped
        from the copy sent to the vision model.
      </p>
    </div>
  );
}

function PermissionRow({
  title,
  detail,
  state,
  error,
}: {
  title: string;
  detail: string;
  state: 'granted' | 'denied' | 'pending';
  error: string | null;
}) {
  const badge =
    state === 'granted'
      ? { text: 'granted', className: 'text-signal-ok' }
      : state === 'denied'
        ? { text: 'denied', className: 'text-signal-danger' }
        : { text: 'not yet', className: 'text-slate-500' };

  return (
    <li className="card-tight">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-100">{title}</span>
        <span className={`text-xs font-semibold uppercase ${badge.className}`}>{badge.text}</span>
      </div>
      <p className="mt-1 text-xs leading-relaxed text-slate-500">{detail}</p>
      {error && <p className="mt-2 text-xs text-signal-danger">{error}</p>}
    </li>
  );
}
