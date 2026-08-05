'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const TABS = [
  { href: '/capture', label: 'Capture', glyph: '◎' },
  { href: '/map', label: 'Map', glyph: '⬡' },
  { href: '/history', label: 'History', glyph: '☰' },
  { href: '/perch', label: 'Perch', glyph: '⚡' },
  { href: '/admin', label: 'Admin', glyph: '▤' },
] as const;

export function NavBar() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 border-t border-surface-700 bg-surface-950/95 backdrop-blur"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
      aria-label="Primary"
    >
      <ul className="mx-auto flex w-full max-w-2xl">
        {TABS.map((tab) => {
          const active = pathname === tab.href || pathname.startsWith(`${tab.href}/`);
          return (
            <li key={tab.href} className="flex-1">
              <Link
                href={tab.href}
                aria-current={active ? 'page' : undefined}
                className={`flex flex-col items-center gap-0.5 py-2.5 text-[11px] font-medium transition-colors ${
                  active ? 'text-grid-distribution' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                <span aria-hidden className="text-lg leading-none">
                  {tab.glyph}
                </span>
                {tab.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
