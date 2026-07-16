import * as stylex from '@stylexjs/stylex';

const styles = stylex.create({
  root: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  title: {
    fontWeight: 700,
    fontSize: 15,
    color: 'var(--sw-text)',
    letterSpacing: '-0.02em',
  },
  subtitle: {
    fontSize: 10,
    color: 'var(--sw-text-muted)',
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
  },
});

export default function StromwartLogo() {
  return (
    <div {...stylex.props(styles.root)}>
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-label="Stromwart">
        <rect width="28" height="28" rx="7" fill="rgba(249,115,22,0.15)" />
        <rect width="28" height="28" rx="7" stroke="rgba(249,115,22,0.4)" strokeWidth="1" />
        <path
          d="M6 18 L10 11 L15 15.5 L19 9 L23 14"
          stroke="#f97316"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="23" cy="14" r="2" fill="#f97316" />
      </svg>
      <div>
        <div {...stylex.props(styles.title)}>Stromwart</div>
        <div {...stylex.props(styles.subtitle)}>QoE Intelligence</div>
      </div>
    </div>
  );
}
