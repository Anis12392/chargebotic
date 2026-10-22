/**
 * GridLine AI service worker.
 *
 * Strategy, chosen for a field tool with intermittent signal:
 *  - App shell: cache-first, so the UI opens instantly and works with no bars.
 *  - API GETs: network-first with a cache fallback, so you see fresh data when
 *    online and the last known data when not.
 *  - API POSTs (/analyze, /verify): never cached and never replayed by the
 *    worker. The page owns retry through its IndexedDB queue, because
 *    replaying an analysis blind would bill a vision call for a capture the
 *    user may have already discarded.
 */

const VERSION = 'v1';
const SHELL_CACHE = `gridline-shell-${VERSION}`;
const DATA_CACHE = `gridline-data-${VERSION}`;

const SHELL_ASSETS = ['/', '/capture', '/map', '/history', '/manifest.webmanifest', '/offline'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      .then((cache) => cache.addAll(SHELL_ASSETS).catch(() => undefined))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== SHELL_CACHE && key !== DATA_CACHE)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  if (request.mode === 'navigate') {
    event.respondWith(navigationHandler(request));
    return;
  }

  event.respondWith(cacheFirst(request));
});

async function networkFirst(request) {
  const cache = await caches.open(DATA_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({ detail: 'Offline and no cached copy of this request is available.' }),
      { status: 503, headers: { 'Content-Type': 'application/json' } },
    );
  }
}

async function navigationHandler(request) {
  try {
    return await fetch(request);
  } catch (error) {
    const cache = await caches.open(SHELL_CACHE);
    return (
      (await cache.match(request)) ??
      (await cache.match('/offline')) ??
      (await cache.match('/')) ??
      new Response('Offline', { status: 503 })
    );
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(SHELL_CACHE);
  const cached = await cache.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok && response.type === 'basic') cache.put(request, response.clone());
    return response;
  } catch (error) {
    return new Response('', { status: 503 });
  }
}

// The page posts this after it drains its own queue, so a stale cached
// inspection list does not survive a successful upload.
self.addEventListener('message', (event) => {
  if (event.data?.type === 'INVALIDATE_DATA_CACHE') {
    event.waitUntil(caches.delete(DATA_CACHE));
  }
});
