import * as stylex from '@stylexjs/stylex';

const styles = stylex.create({
  root: {
    minHeight: '100dvh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'var(--sw-bg)',
    gap: 20,
  },
  text: {
    color: 'var(--sw-text-muted)',
    fontSize: 14,
  },
});

export default function LoadingScreen({ message = 'Loading…' }: { message?: string }) {
  return (
    <div {...stylex.props(styles.root)}>
      <svg width="40" height="40" viewBox="0 0 28 28" fill="none">
        <rect width="28" height="28" rx="7" fill="rgba(249,115,22,0.15)" />
        <path
          d="M6 18 L10 11 L15 15.5 L19 9 L23 14"
          stroke="#f97316"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="23" cy="14" r="2" fill="#f97316" />
      </svg>
      <div {...stylex.props(styles.text)}>{message}</div>
    </div>
  );
}
