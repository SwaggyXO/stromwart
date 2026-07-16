/// <reference types="vite/client" />

declare module 'virtual:stylex:runtime';
declare module 'virtual:stylex.css';

interface ImportMetaEnv {
  readonly VITE_AUTH0_DOMAIN?: string;
  readonly VITE_AUTH0_CUSTOM_DOMAIN?: string;
  readonly VITE_AUTH0_CLIENT_ID?: string;
  readonly VITE_ACTIVE_EVENT_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
