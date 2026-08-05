import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Dark-first: the app is used outdoors, often at dusk, one-handed.
        surface: {
          950: '#07090c',
          900: '#0d1117',
          800: '#151b23',
          700: '#1f2730',
          600: '#2d3742',
        },
        grid: {
          // Voltage-class palette, ordered by energy. Chosen for contrast
          // against the dark surface and distinguishable under deuteranopia.
          secondary: '#5eead4',
          distribution: '#60a5fa',
          subtransmission: '#c084fc',
          transmission: '#fb923c',
          ehv: '#f87171',
          unknown: '#94a3b8',
        },
        signal: {
          ok: '#4ade80',
          warn: '#fbbf24',
          danger: '#f87171',
        },
      },
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 2.4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
};

export default config;
