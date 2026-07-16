import { defineConfig, mergeConfig } from 'vite';
import { resolve } from 'path';
import baseConfig from '../vite.config';

/**
 * E2E Vite config — aliases Auth0 to a deterministic mock so Playwright
 * can exercise authenticated routes without modifying application source.
 */
export default mergeConfig(
  baseConfig,
  defineConfig({
    resolve: {
      alias: {
        '@auth0/auth0-react': resolve(__dirname, 'mocks/auth0-react.tsx'),
      },
    },
    server: {
      open: false,
    },
  }),
);
