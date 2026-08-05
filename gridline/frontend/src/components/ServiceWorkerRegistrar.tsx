'use client';

import { useEffect } from 'react';

export function ServiceWorkerRegistrar() {
  useEffect(() => {
    if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return;
    // Registering after load keeps the worker off the critical path for the
    // first capture, which is the one that matters.
    const register = () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // A failed registration costs offline support, not the app.
      });
    };
    if (document.readyState === 'complete') register();
    else window.addEventListener('load', register, { once: true });
  }, []);

  return null;
}
