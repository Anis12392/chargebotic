import type { Metadata, Viewport } from 'next';

import { ServiceWorkerRegistrar } from '@/components/ServiceWorkerRegistrar';

import './globals.css';

export const metadata: Metadata = {
  title: 'GridLine AI',
  description:
    'A live map of the overhead power network around you. Lines coloured by voltage class, drawn from surveyed OpenStreetMap and HIFLD data — never an estimate presented as a measurement.',
  manifest: '/manifest.webmanifest',
  applicationName: 'GridLine AI',
  appleWebApp: { capable: true, statusBarStyle: 'black-translucent', title: 'GridLine' },
  formatDetection: { telephone: false },
  icons: {
    icon: '/icons/icon-192.png',
    apple: '/icons/icon-192.png',
  },
};

export const viewport: Viewport = {
  themeColor: '#07090c',
  width: 'device-width',
  initialScale: 1,
  // The camera viewfinder needs the full screen, notch included.
  viewportFit: 'cover',
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      {/* The map fills the viewport, so the shell contributes no chrome and
          never scrolls — a page that rubber-bands under a map feels broken. */}
      <body className="h-dvh overflow-hidden bg-surface-950">
        <ServiceWorkerRegistrar />
        {children}
      </body>
    </html>
  );
}
