import { Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import * as stylex from '@stylexjs/stylex';
import AuthLayout from '@/components/auth/AuthLayout';
import { primaryButtonProps } from '@/lib/stylex';
import { UserPlus } from 'lucide-react';

const styles = stylex.create({
  hint: {
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 14,
    paddingRight: 14,
    borderRadius: 'var(--sw-radius-md)',
    backgroundColor: 'rgba(59,130,246,0.08)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'rgba(59,130,246,0.2)',
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    textAlign: 'center',
    lineHeight: 1.5,
  },
  code: {
    fontFamily: 'var(--font-mono)',
    color: 'var(--sw-blue)',
    fontSize: 11,
  },
  footer: {
    position: 'relative',
    zIndex: 1,
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    textAlign: 'center',
  },
  link: {
    color: 'var(--sw-accent)',
    textDecoration: 'none',
    fontWeight: 600,
  },
});

export default function SignUpPage() {
  const { loginWithRedirect } = useAuth0();

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Join the SRE command center for live streaming QoE intelligence."
      footer={
        <p {...stylex.props(styles.footer)}>
          Already have an account?{' '}
          <Link to="/login" {...stylex.props(styles.link)}>
            Sign in
          </Link>
        </p>
      }
    >
      <button
        type="button"
        onClick={() => loginWithRedirect({ authorizationParams: { screen_hint: 'signup' } })}
        {...primaryButtonProps('large')}
      >
        <UserPlus size={16} />
        Sign up with Auth0
      </button>

      <div {...stylex.props(styles.hint)}>
        Auth0 domain + client ID must be set in{' '}
        <code {...stylex.props(styles.code)}>.env.local</code>
      </div>
    </AuthLayout>
  );
}
