import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from 'react';

interface Auth0User {
  name?: string;
  email?: string;
  sub?: string;
}

interface Auth0ContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  user?: Auth0User;
  loginWithRedirect: (opts?: unknown) => Promise<void>;
  logout: (opts?: unknown) => void;
  getAccessTokenSilently: () => Promise<string>;
}

const Auth0Context = createContext<Auth0ContextValue | null>(null);

function readMock(): { isAuthenticated: boolean; isLoading: boolean; user?: Auth0User } {
  const mock = (window as unknown as { __AUTH0_MOCK__?: Auth0ContextValue }).__AUTH0_MOCK__;
  if (mock) {
    return {
      isAuthenticated: !!mock.isAuthenticated,
      isLoading: !!mock.isLoading,
      user: mock.user ?? { name: 'Test User', email: 'test@stromwart.dev', sub: 'auth0|test' },
    };
  }
  // Default authenticated for E2E unless a test clears the mock
  return {
    isAuthenticated: true,
    isLoading: false,
    user: { name: 'Test User', email: 'test@stromwart.dev', sub: 'auth0|test' },
  };
}

export function Auth0Provider({ children }: { children: ReactNode; [key: string]: unknown }) {
  const value = useMemo<Auth0ContextValue>(() => {
    const m = readMock();
    return {
      isAuthenticated: m.isAuthenticated,
      isLoading: m.isLoading,
      user: m.user,
      loginWithRedirect: async () => {
        window.location.assign('/login');
      },
      logout: () => {
        window.location.assign('/login');
      },
      getAccessTokenSilently: async () => 'test-token',
    };
  }, []);

  return <Auth0Context.Provider value={value}>{children}</Auth0Context.Provider>;
}

export function useAuth0(): Auth0ContextValue {
  const ctx = useContext(Auth0Context);
  if (!ctx) {
    // Provider missing — still honor window mock for early reads
    const m = readMock();
    return {
      isAuthenticated: m.isAuthenticated,
      isLoading: m.isLoading,
      user: m.user,
      loginWithRedirect: async () => undefined,
      logout: () => undefined,
      getAccessTokenSilently: async () => 'test-token',
    };
  }

  // Re-read mock each call so addInitScript overrides apply after mount via force
  const m = readMock();
  return {
    ...ctx,
    isAuthenticated: m.isAuthenticated,
    isLoading: m.isLoading,
    user: m.user ?? ctx.user,
  };
}

export function withAuthenticationRequired<P extends object>(
  Component: (props: P) => ReactNode,
): (props: P) => ReactNode {
  return function Guarded(props: P) {
    const { isAuthenticated, isLoading, loginWithRedirect } = useAuth0();
    const redirect = useCallback(() => {
      void loginWithRedirect();
    }, [loginWithRedirect]);

    if (isLoading) return null;
    if (!isAuthenticated) {
      redirect();
      return null;
    }
    return <Component {...props} />;
  };
}
