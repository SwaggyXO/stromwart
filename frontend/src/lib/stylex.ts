import * as stylex from '@stylexjs/stylex';

/** Merge global glass-card class with StyleX props (avoids duplicate className). */
export function glassProps(
  ...styles: ReadonlyArray<stylex.StyleXStyles | null | undefined | false>
): ReturnType<typeof stylex.props> {
  const props = stylex.props(...styles);
  return {
    ...props,
    className: ['glass-card', props.className].filter(Boolean).join(' '),
  };
}

/** Merge `.sw-btn-primary` (unlayered CSS — gradients survive Astryx reset). */
export function primaryButtonProps(
  size: 'default' | 'large' = 'default',
  ...styles: ReadonlyArray<stylex.StyleXStyles | null | undefined | false>
): ReturnType<typeof stylex.props> {
  const props = stylex.props(...styles);
  const classes = [
    'sw-btn-primary',
    size === 'large' ? 'sw-btn-large' : null,
    props.className,
  ].filter(Boolean);
  return { ...props, className: classes.join(' ') };
}

/** Shared form field look for inputs/selects. */
export const formControl = stylex.create({
  field: {
    width: '100%',
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 12,
    paddingRight: 36,
    borderRadius: 'var(--sw-radius-md)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: {
      default: 'var(--sw-border)',
      ':hover': 'rgba(255,255,255,0.14)',
      ':focus': 'rgba(249,115,22,0.45)',
    },
    backgroundColor: 'var(--sw-surface-2)',
    color: 'var(--sw-text)',
    fontSize: 13,
    fontFamily: 'var(--font-body)',
    outline: 'none',
    transitionProperty: 'border-color, box-shadow, background-color',
    transitionDuration: '180ms',
    transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)',
    boxShadow: {
      default: 'none',
      ':focus': '0 0 0 3px var(--sw-accent-dim)',
    },
  },
  input: {
    paddingRight: 12,
  },
});

/** Shared page container layout for full-width content pages. */
export const pageLayout = stylex.create({
  container: {
    width: '100%',
    maxWidth: 1440,
    marginLeft: 'auto',
    marginRight: 'auto',
    paddingLeft: 'clamp(20px, 3vw, 48px)',
    paddingRight: 'clamp(20px, 3vw, 48px)',
    paddingTop: 28,
    paddingBottom: 28,
    display: 'flex',
    flexDirection: 'column',
    gap: 24,
  },
  containerNarrow: {
    width: '100%',
    maxWidth: 1200,
    marginLeft: 'auto',
    marginRight: 'auto',
    paddingLeft: 'clamp(20px, 3vw, 48px)',
    paddingRight: 'clamp(20px, 3vw, 48px)',
    paddingTop: 28,
    paddingBottom: 28,
    display: 'flex',
    flexDirection: 'column',
    gap: 22,
  },
});
