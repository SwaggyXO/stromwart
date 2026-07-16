import React from 'react';
import ReactDOM from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Auth0Provider } from '@auth0/auth0-react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import AstryxThemeRoot from '@/components/providers/AstryxThemeRoot';
import '@/styles/globals.css';
import App from './App';

// StyleX Vite unplugin: load aggregated CSS + HMR runtime in development.
// Without this, atomic classNames land on the DOM but the matching CSS sheet
// is often missing in dev — which collapses every StyleX layout.
if (import.meta.env.DEV) {
  void import('virtual:stylex:runtime');
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5_000,
      retry: 1,
    },
  },
});

const AUTH0_DOMAIN =
  import.meta.env.VITE_AUTH0_CUSTOM_DOMAIN ||
  import.meta.env.VITE_AUTH0_DOMAIN ||
  '';

const AUTH0_CLIENT_ID = import.meta.env.VITE_AUTH0_CLIENT_ID ?? '';

const router = createBrowserRouter([{ path: '*', element: <App /> }]);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AstryxThemeRoot>
      <Auth0Provider
        domain={AUTH0_DOMAIN}
        clientId={AUTH0_CLIENT_ID}
        authorizationParams={{
          redirect_uri: window.location.origin,
        }}
        cacheLocation="localstorage"
      >
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
          <Toaster position="bottom-right" richColors closeButton />
        </QueryClientProvider>
      </Auth0Provider>
    </AstryxThemeRoot>
  </React.StrictMode>,
);
