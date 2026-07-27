import type { Metadata, Viewport } from 'next';

import { NavBar } from '@/components/NavBar';
import { ServiceWorkerRegistrar } from '@/components/ServiceWorkerRegistrar';

import './globals.css';

export const metadata: Metadata = {
  title: 'GridLine AI',
  description:
    'Identify overhead power lines from a photograph and a GPS fix. Evidence-based estimates with confidence scores — never a claim of measured voltage or current.',
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
      <body className="min-h-dvh bg-surface-950">
        <ServiceWorkerRegistrar />
        <div className="mx-auto flex min-h-dvh w-full max-w-2xl flex-col">
          <main className="flex-1 pb-20">{children}</main>
          <NavBar />
        </div>
      </body>
    </html>
  );
}
