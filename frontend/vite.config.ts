import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import stylex from '@stylexjs/unplugin';
import { resolve } from 'path';

export default defineConfig({
  plugins: [
    // Keep StyleX before React for Fast Refresh.
    // Astryx cascade: reset → astryx-base → astryx-theme → product StyleX.
    // Missing astryx-theme in `before` lets theme.css register last and
    // override product styles. Prefix avoids colliding with other layer names.
    stylex.vite({
      useCSSLayers: {
        before: ['reset', 'astryx-base', 'astryx-theme'],
        prefix: 'stylex',
      },
      // Must track NODE_ENV — `dev: true` in production breaks CSS emission.
      dev: process.env.NODE_ENV !== 'production',
    }),
    react(),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // OpenAPI paths are /v1/... — strip the /api prefix used by the browser client
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
