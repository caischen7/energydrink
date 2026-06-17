import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  // Relative base so the build works from any static host or subpath (e.g. GitHub Pages)
  base: './',
  build: {
    target: 'es2020',
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      input: {
        // marketing landing page
        main: resolve(__dirname, 'index.html'),
        // founder market-intelligence terminal
        dashboard: resolve(__dirname, 'dashboard.html'),
      },
    },
  },
});
