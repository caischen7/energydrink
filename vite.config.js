import { defineConfig } from 'vite';

export default defineConfig({
  // Relative base so the build works from any static host or subpath (e.g. GitHub Pages)
  base: './',
  build: {
    target: 'es2020',
    chunkSizeWarningLimit: 900,
  },
});
