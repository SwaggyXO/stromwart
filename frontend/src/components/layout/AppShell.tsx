import { type ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { Activity, Bot, ClipboardList, LogOut, Settings, Sun, Moon } from 'lucide-react';
import * as stylex from '@stylexjs/stylex';
import StromwartLogo from '@/components/ui/StromwartLogo';
import { useColorMode } from '@/hooks/useColorMode';
import { useAppStore } from '@/store/useAppStore';
import { useResolvedEventId } from '@/hooks/useResolvedEventId';
import { useSSEStream } from '@/api/sse';
import { useAlertNotifications } from '@/hooks/useAlertNotifications';

const NAV = [
  { to: '/', icon: Activity, label: 'Live Event' },
  { to: '/audit', icon: ClipboardList, label: 'Audit Trail', tour: 'audit-link' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

const styles = stylex.create({
  root: {
    display: 'flex',
    minHeight: '100dvh',
    backgroundColor: 'var(--sw-bg)',
  },
  aside: {
    width: 220,
    flexShrink: 0,
    display: 'flex',
    flexDirection: 'column',
    borderRightWidth: 1,
    borderRightStyle: 'solid',
    borderRightColor: 'var(--sw-border)',
    backgroundColor: 'var(--sw-surface)',
    backgroundImage:
      'linear-gradient(180deg, var(--sw-sidebar-from) 0%, var(--sw-sidebar-to) 100%)',
    backdropFilter: 'blur(20px)',
    position: 'sticky',
    top: 0,
    height: '100dvh',
    zIndex: 40,
  },
  logoWrap: {
    paddingTop: 20,
    paddingBottom: 16,
    paddingLeft: 20,
    paddingRight: 20,
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
  },
  liveBox: {
    marginTop: 12,
    marginBottom: 12,
    marginLeft: 16,
    marginRight: 16,
    paddingTop: 8,
    paddingBottom: 8,
    paddingLeft: 12,
    paddingRight: 12,
    borderRadius: 'var(--sw-radius-md)',
    backgroundColor: 'var(--sw-accent-dim)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'rgba(249,115,22,0.25)',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    cursor: 'pointer',
  },
  liveLabel: {
    fontSize: 11,
    color: 'var(--sw-accent)',
    fontWeight: 600,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
  },
  liveMeta: {
    fontSize: 11,
    color: 'var(--sw-text-muted)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    maxWidth: 140,
  },
  nav: {
    paddingTop: 8,
    paddingBottom: 8,
    paddingLeft: 10,
    paddingRight: 10,
    // StyleX drops `flex: 1` — use longhands so the footer pins to the bottom.
    flexGrow: 1,
    flexShrink: 1,
    flexBasis: 0,
    minHeight: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
  },
  navLink: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    paddingTop: 9,
    paddingBottom: 9,
    paddingLeft: 12,
    paddingRight: 12,
    borderRadius: 'var(--sw-radius-md)',
    textDecoration: 'none',
    fontSize: 14,
    fontWeight: 500,
    color: 'var(--sw-text-muted)',
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'transparent',
  },
  navLinkActive: {
    color: 'var(--sw-accent)',
    backgroundColor: 'var(--sw-accent-dim)',
    borderColor: 'rgba(249,115,22,0.2)',
  },
  footer: {
    marginTop: 'auto',
    paddingTop: 12,
    paddingBottom: 12,
    paddingLeft: 14,
    paddingRight: 14,
    borderTopWidth: 1,
    borderTopStyle: 'solid',
    borderTopColor: 'var(--sw-border)',
    flexShrink: 0,
  },
  userRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  userName: {
    fontSize: 13,
    fontWeight: 500,
    color: 'var(--sw-text)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  userRole: {
    fontSize: 11,
    color: 'var(--sw-text-muted)',
  },
  actions: {
    display: 'flex',
    gap: 8,
  },
  modeToggle: {
    flexShrink: 0,
    width: 36,
    height: 36,
    borderRadius: 'var(--sw-radius-md)',
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    color: 'var(--sw-text-muted)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logout: {
    flex: 1,
    paddingTop: 8,
    paddingBottom: 8,
    paddingLeft: 12,
    paddingRight: 12,
    borderRadius: 'var(--sw-radius-md)',
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    color: 'var(--sw-text-muted)',
    fontSize: 13,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  main: {
    flex: 1,
    overflow: 'auto',
    minWidth: 0,
  },
  sseOk: { color: 'var(--sw-green)' },
  sseOff: { color: 'var(--sw-text-faint)' },
});

export default function AppShell({ children }: { children: ReactNode }) {
  const { logout, user } = useAuth0();
  const navigate = useNavigate();
  const { mode, toggle } = useColorMode();
  const sseConnected = useAppStore((s) => s.sseConnected);
  const activeSessions = useAppStore((s) => s.liveUpdate?.active_sessions);
  const totalSessions = useAppStore((s) => s.liveUpdate?.total_sessions);

  const eventId = useResolvedEventId();
  useSSEStream(eventId);
  useAlertNotifications(eventId);

  const handleLogout = () => {
    logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
  };

  return (
    <div {...stylex.props(styles.root)}>
      <aside {...stylex.props(styles.aside)}>
        <div {...stylex.props(styles.logoWrap)}>
          <StromwartLogo />
        </div>

        <div {...stylex.props(styles.liveBox)} onClick={() => navigate('/')}>
          <span className="glow-dot" style={{ width: 7, height: 7, flexShrink: 0 }} />
          <div>
            <div {...stylex.props(styles.liveLabel)}>
              Live{' '}
              <span {...stylex.props(sseConnected ? styles.sseOk : styles.sseOff)}>
                {sseConnected ? '· SSE' : '· …'}
              </span>
            </div>
            <div {...stylex.props(styles.liveMeta)}>
              {activeSessions != null
                ? `${activeSessions.toLocaleString()} active${
                    totalSessions != null ? ` · ${totalSessions.toLocaleString()} total` : ''
                  }`
                : 'Waiting for stream'}
            </div>
          </div>
        </div>

        <nav {...stylex.props(styles.nav)}>
          {NAV.map(({ to, icon: Icon, label, tour }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              data-tour={tour}
              {...stylex.props(styles.navLink)}
              style={({ isActive }) =>
                isActive
                  ? {
                      backgroundColor: 'var(--sw-accent-dim)',
                      borderColor: 'rgba(249,115,22,0.2)',
                      color: 'var(--sw-accent)',
                    }
                  : undefined
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div {...stylex.props(styles.footer)}>
          <div {...stylex.props(styles.userRow)}>
            <div className="sw-avatar">
              {user?.name?.[0]?.toUpperCase() ?? 'S'}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div {...stylex.props(styles.userName)}>{user?.name ?? 'SRE Operator'}</div>
              <div {...stylex.props(styles.userRole)}>Admin</div>
            </div>
          </div>
          <div {...stylex.props(styles.actions)}>
            <button
              type="button"
              onClick={toggle}
              aria-label={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}
              {...stylex.props(styles.modeToggle)}
            >
              {mode === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button type="button" onClick={handleLogout} {...stylex.props(styles.logout)}>
              <LogOut size={14} />
              Sign out
            </button>
          </div>
        </div>
      </aside>

      <main {...stylex.props(styles.main)}>{children}</main>
    </div>
  );
}
