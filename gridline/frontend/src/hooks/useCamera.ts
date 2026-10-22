'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export type CameraStatus = 'idle' | 'requesting' | 'live' | 'denied' | 'unsupported' | 'error';

/** Bind a live stream to a video element and start playback. */
function attachStream(node: HTMLVideoElement, stream: MediaStream): void {
  if (node.srcObject === stream) return;
  node.srcObject = stream;
  // Autoplay can reject when the tab is backgrounded; the element still holds
  // the stream and resumes on its own, so a rejection here is not fatal.
  void node.play?.().catch(() => undefined);
}

/**
 * Rear-camera preview and still capture.
 *
 * Captures at the video track's native resolution rather than the on-screen
 * preview size: the backend scales insulator dimensions off this frame, and a
 * 360-pixel-wide preview throws away exactly the detail that matters.
 *
 * The element is tracked with a **callback ref**, not a plain one. The consumer
 * mounts the `<video>` only after permissions are granted, which is a render
 * *after* `getUserMedia` resolves — so binding `srcObject` inside `start()`
 * would run against a null ref and leave a permanently black viewfinder whose
 * `videoWidth` stays 0 and whose captures always fail. The callback ref binds
 * whenever the node appears, and `start()` binds when the node is already
 * there (the "capture another" path). Between them, either ordering works.
 *
 * `ready` is separate from `status`. A stream can be live while the element has
 * not yet decoded a frame, and a canvas draw in that window silently produces
 * nothing — the operator taps the shutter and is told the camera returned no
 * frame. The shutter must gate on `ready`, not on `status === 'live'`.
 */
export function useCamera() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [status, setStatus] = useState<CameraStatus>('idle');
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resolution, setResolution] = useState<{ width: number; height: number } | null>(null);

  const setVideoElement = useCallback((node: HTMLVideoElement | null) => {
    videoRef.current = node;
    if (!node) return;
    const markReady = () => {
      if (node.videoWidth > 0 && node.videoHeight > 0) setReady(true);
    };
    node.addEventListener('loadeddata', markReady);
    node.addEventListener('canplay', markReady);
    node.addEventListener('playing', markReady);
    if (streamRef.current) attachStream(node, streamRef.current);
    markReady();
  }, []);

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setReady(false);
    setStatus('idle');
  }, []);

  const start = useCallback(async () => {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      setStatus('unsupported');
      setError('This browser cannot open the camera. Use the file picker instead.');
      return;
    }

    setStatus('requesting');
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 2560 },
          height: { ideal: 1920 },
        },
        audio: false,
      });
      streamRef.current = stream;
      // Covers the case where the element is already mounted; the callback ref
      // covers the case where it mounts later.
      if (videoRef.current) attachStream(videoRef.current, stream);
      const track = stream.getVideoTracks()[0];
      const settings = track?.getSettings();
      if (settings?.width && settings?.height) {
        setResolution({ width: settings.width, height: settings.height });
      }
      setStatus('live');
    } catch (err) {
      const name = err instanceof DOMException ? err.name : '';
      if (name === 'NotAllowedError' || name === 'SecurityError') {
        setStatus('denied');
        setError('Camera permission denied. Enable it in your browser settings, or attach a photo instead.');
      } else if (name === 'NotFoundError' || name === 'OverconstrainedError') {
        setStatus('error');
        setError('No rear camera was found on this device.');
      } else {
        setStatus('error');
        setError(err instanceof Error ? err.message : 'Could not open the camera.');
      }
    }
  }, []);

  const capture = useCallback(async (): Promise<Blob | null> => {
    const video = videoRef.current;
    if (!video || status !== 'live') return null;

    // Belt and braces for the gap between "stream attached" and "first frame
    // decoded". The shutter is already gated on `ready`, but a backgrounded tab
    // or a slow sensor can still land here with nothing to draw.
    const deadline = Date.now() + 2000;
    while ((!video.videoWidth || !video.videoHeight) && Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 50));
    }

    const width = video.videoWidth;
    const height = video.videoHeight;
    if (!width || !height) return null;

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext('2d');
    if (!context) return null;
    context.drawImage(video, 0, 0, width, height);

    return new Promise<Blob | null>((resolve) => {
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.92);
    });
  }, [status]);

  useEffect(() => stop, [stop]);

  return { videoRef, setVideoElement, status, ready, error, resolution, start, stop, capture };
}
