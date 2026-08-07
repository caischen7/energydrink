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
        main: resolve(__dirname, 'index.html'),
        dashboard: resolve(__dirname, 'dashboard.html'),
        admin: resolve(__dirname, 'admin.html'),
        insights: resolve(__dirname, 'insights.html'),
        segments: resolve(__dirname, 'segments.html'),
      },
    },
  },
});
