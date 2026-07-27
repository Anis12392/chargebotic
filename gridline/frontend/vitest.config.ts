import { resolve } from 'node:path';

import { defineConfig } from 'vitest/config';

export default defineConfig({
  resolve: {
    alias: { '@': resolve(__dirname, './src') },
  },
  // esbuild's automatic JSX runtime handles the .tsx tests, which avoids
  // pulling in a React plugin whose peer range conflicts with vitest's vite.
  esbuild: { jsx: 'automatic' },
  test: {
    // Node by default; files that need a DOM opt in with a
    // `@vitest-environment jsdom` docblock.
    environment: 'node',
    globals: true,
    include: ['src/**/*.test.{ts,tsx}'],
  },
});
