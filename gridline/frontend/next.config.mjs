/** @type {import('next').NextConfig} */
const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,

  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          // The camera and GPS are the whole product; everything else is off.
          { key: 'Permissions-Policy', value: 'camera=(self), geolocation=(self), microphone=()' },
        ],
      },
      {
        source: '/sw.js',
        headers: [{ key: 'Cache-Control', value: 'no-cache, no-store, must-revalidate' }],
      },
    ];
  },

  async rewrites() {
    return [
      // Same-origin proxy to the API. Keeps the service worker, CORS and cookie
      // stories simple, and means the PWA has exactly one origin to trust.
      { source: '/api/:path*', destination: `${apiBase}/:path*` },
      // With no S3 credentials the backend stores photos on disk and returns
      // relative `/media/...` URLs, which the browser resolves against *this*
      // origin. Without this rewrite every thumbnail 404s in local mode — the
      // exact path `docker compose up` takes before S3 is configured. The
      // backend stays unaware of the frontend's routing, and clients calling
      // the API directly still get a URL that works for them.
      { source: '/media/:path*', destination: `${apiBase}/media/:path*` },
    ];
  },
};

export default nextConfig;
