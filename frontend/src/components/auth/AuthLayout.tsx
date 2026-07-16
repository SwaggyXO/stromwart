import { type ReactNode } from 'react';
import * as stylex from '@stylexjs/stylex';
import { glassProps } from '@/lib/stylex';
import StromwartLogo from '@/components/ui/StromwartLogo';

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}

const styles = stylex.create({
  root: {
    minHeight: '100dvh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'var(--sw-bg)',
    position: 'relative',
    overflow: 'hidden',
  },
  glowOrange: {
    position: 'absolute',
    width: 600,
    height: 600,
    borderRadius: '50%',
    backgroundImage: 'radial-gradient(ellipse, rgba(249,115,22,0.08) 0%, transparent 70%)',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    pointerEvents: 'none',
  },
  glowBlue: {
    position: 'absolute',
    width: 400,
    height: 400,
    borderRadius: '50%',
    backgroundImage: 'radial-gradient(ellipse, rgba(59,130,246,0.05) 0%, transparent 70%)',
    top: '30%',
    left: '60%',
    pointerEvents: 'none',
  },
  card: {
    width: 400,
    paddingTop: 40,
    paddingBottom: 40,
    paddingLeft: 36,
    paddingRight: 36,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 24,
    position: 'relative',
  },
  gloss: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '50%',
    backgroundImage: 'linear-gradient(180deg, rgba(255,255,255,0.06) 0%, transparent 100%)',
    borderTopLeftRadius: 'var(--sw-radius-lg)',
    borderTopRightRadius: 'var(--sw-radius-lg)',
    pointerEvents: 'none',
  },
  header: {
    position: 'relative',
    zIndex: 1,
    textAlign: 'center',
    width: '100%',
  },
  logo: {
    marginBottom: 20,
    display: 'flex',
    justifyContent: 'center',
  },
  title: {
    fontSize: 22,
    fontWeight: 700,
    color: 'var(--sw-text)',
    marginBottom: 6,
    letterSpacing: '-0.02em',
  },
  subtitle: {
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    lineHeight: 1.5,
  },
  body: {
    width: '100%',
    position: 'relative',
    zIndex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  badges: {
    position: 'relative',
    zIndex: 1,
    display: 'flex',
    gap: 20,
    fontSize: 11,
    color: 'var(--sw-text-faint)',
  },
  badgeItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 4,
  },
  dotGreen: {
    width: 4,
    height: 4,
    borderRadius: '50%',
    backgroundColor: 'var(--sw-green)',
    display: 'inline-block',
  },
  dotBlue: {
    width: 4,
    height: 4,
    borderRadius: '50%',
    backgroundColor: 'var(--sw-blue)',
    display: 'inline-block',
  },
  dotAccent: {
    width: 4,
    height: 4,
    borderRadius: '50%',
    backgroundColor: 'var(--sw-accent)',
    display: 'inline-block',
  },
});

export default function AuthLayout({ title, subtitle, children, footer }: AuthLayoutProps) {
  return (
    <div {...stylex.props(styles.root)}>
      <div {...stylex.props(styles.glowOrange)} />
      <div {...stylex.props(styles.glowBlue)} />

      <div {...glassProps(styles.card)}>
        <div {...stylex.props(styles.gloss)} />

        <div {...stylex.props(styles.header)}>
          <div {...stylex.props(styles.logo)}>
            <StromwartLogo />
          </div>
          <h1 {...stylex.props(styles.title)}>{title}</h1>
          <p {...stylex.props(styles.subtitle)}>{subtitle}</p>
        </div>

        <div {...stylex.props(styles.body)}>{children}</div>

        {footer}

        <div {...stylex.props(styles.badges)}>
          <span {...stylex.props(styles.badgeItem)}>
            <span {...stylex.props(styles.dotGreen)} />
            Encrypted
          </span>
          <span {...stylex.props(styles.badgeItem)}>
            <span {...stylex.props(styles.dotBlue)} />
            Audit-logged
          </span>
          <span {...stylex.props(styles.badgeItem)}>
            <span {...stylex.props(styles.dotAccent)} />
            Role-gated
          </span>
        </div>
      </div>
    </div>
  );
}
