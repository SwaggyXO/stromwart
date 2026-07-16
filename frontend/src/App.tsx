import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import AppShell from '@/components/layout/AppShell';
import TourProvider from '@/components/tour/TourProvider';
import LoginPage from '@/pages/LoginPage';
import SignUpPage from '@/pages/SignUpPage';
import LiveEventPage from '@/pages/LiveEventPage';
import IncidentDetailPage from '@/pages/IncidentDetailPage';
import AuditLogPage from '@/pages/AuditLogPage';
import SettingsPage from '@/pages/SettingsPage';
import AgentsPage from '@/pages/AgentsPage';
import LoadingScreen from '@/components/ui/LoadingScreen';

export default function App() {
  const { isLoading, isAuthenticated } = useAuth0();

  if (isLoading) return <LoadingScreen message="Authenticating…" />;

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route
        path="/signup"
        element={isAuthenticated ? <Navigate to="/" replace /> : <SignUpPage />}
      />
      <Route
        path="/*"
        element={
          isAuthenticated ? (
            <TourProvider>
              <AppShell>
                <Routes>
                  <Route path="/" element={<LiveEventPage />} />
                  <Route path="/incidents/:id" element={<IncidentDetailPage />} />
                  <Route path="/audit" element={<AuditLogPage />} />
                  <Route path="/agents" element={<AgentsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </AppShell>
            </TourProvider>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
    </Routes>
  );
}
