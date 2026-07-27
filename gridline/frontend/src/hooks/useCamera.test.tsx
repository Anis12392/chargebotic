/**
 * Regression cover for a bug found by driving the real app in a browser.
 *
 * The capture screen mounts its `<video>` only *after* permissions are granted,
 * which is a render after `getUserMedia` resolves. The original hook bound
 * `srcObject` inside `start()`, where the ref was still null — so the stream
 * was live (the resolution readout even worked, since that reads the track) but
 * the element never received it. The viewfinder stayed black, `videoWidth`
 * stayed 0, and every capture failed with "the camera did not return a frame".
 *
 * @vitest-environment jsdom
 */

import { act, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useCamera } from './useCamera';

function fakeStream(width = 2560, height = 1920): MediaStream {
  const track = {
    kind: 'video',
    stop: vi.fn(),
    getSettings: () => ({ width, height }),
  };
  return {
    getTracks: () => [track],
    getVideoTracks: () => [track],
  } as unknown as MediaStream;
}

/** Mirrors the capture page: the video mounts only once permissions are done. */
function CaptureHarness() {
  const camera = useCamera();
  const [showViewfinder, setShowViewfinder] = useState(false);

  return (
    <div>
      {!showViewfinder && (
        <button
          type="button"
          onClick={async () => {
            await camera.start();
            setShowViewfinder(true);
          }}
        >
          Grant and open viewfinder
        </button>
      )}
      {showViewfinder && <video data-testid="viewfinder" ref={camera.setVideoElement} />}
      <span data-testid="status">{camera.status}</span>
      <span data-testid="resolution">
        {camera.resolution ? `${camera.resolution.width}x${camera.resolution.height}` : 'none'}
      </span>
    </div>
  );
}

let stream: MediaStream;

beforeEach(() => {
  stream = fakeStream();
  Object.defineProperty(globalThis.navigator, 'mediaDevices', {
    configurable: true,
    value: { getUserMedia: vi.fn().mockResolvedValue(stream) },
  });
  // jsdom implements neither play() nor srcObject on HTMLMediaElement.
  HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(HTMLMediaElement.prototype, 'srcObject', {
    configurable: true,
    writable: true,
    value: null,
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('useCamera stream binding', () => {
  it('binds the stream when the video mounts after start() resolves', async () => {
    render(<CaptureHarness />);

    // Before granting, there is no video element at all — this is the ordering
    // that broke the original implementation.
    expect(screen.queryByTestId('viewfinder')).toBeNull();

    await act(async () => {
      screen.getByRole('button', { name: /Grant and open viewfinder/ }).click();
    });

    const video = screen.getByTestId('viewfinder') as HTMLVideoElement;
    expect(video.srcObject).toBe(stream);
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled();
  });

  it('reports the track resolution, not the preview size', async () => {
    render(<CaptureHarness />);
    await act(async () => {
      screen.getByRole('button', { name: /Grant and open viewfinder/ }).click();
    });
    expect(screen.getByTestId('resolution').textContent).toBe('2560x1920');
    expect(screen.getByTestId('status').textContent).toBe('live');
  });

  it('binds when the element is already mounted (the "capture another" path)', async () => {
    function AlwaysMounted() {
      const camera = useCamera();
      return (
        <div>
          <video data-testid="viewfinder" ref={camera.setVideoElement} />
          <button type="button" onClick={() => void camera.start()}>
            start
          </button>
        </div>
      );
    }

    render(<AlwaysMounted />);
    await act(async () => {
      screen.getByRole('button', { name: 'start' }).click();
    });

    expect((screen.getByTestId('viewfinder') as HTMLVideoElement).srcObject).toBe(stream);
  });

  it('surfaces a denied permission instead of silently showing a black frame', async () => {
    const denial = new DOMException('Permission denied', 'NotAllowedError');
    (navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>).mockRejectedValue(denial);

    render(<CaptureHarness />);
    await act(async () => {
      screen.getByRole('button', { name: /Grant and open viewfinder/ }).click();
    });

    expect(screen.getByTestId('status').textContent).toBe('denied');
  });

  it('reports unsupported when the browser has no getUserMedia', async () => {
    Object.defineProperty(globalThis.navigator, 'mediaDevices', {
      configurable: true,
      value: undefined,
    });

    render(<CaptureHarness />);
    await act(async () => {
      screen.getByRole('button', { name: /Grant and open viewfinder/ }).click();
    });

    expect(screen.getByTestId('status').textContent).toBe('unsupported');
  });
});
