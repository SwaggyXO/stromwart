import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { Loader2 } from 'lucide-react';
import * as stylex from '@stylexjs/stylex';
import { primaryButtonProps } from '@/lib/stylex';

const styles = stylex.create({
  base: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 'var(--sw-radius-md)',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    transitionProperty: 'opacity, background-color, border-color',
    transitionDuration: '180ms',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'transparent',
  },
  primary: {
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 18,
    paddingRight: 18,
  },
  secondary: {
    paddingTop: 8,
    paddingBottom: 8,
    paddingLeft: 14,
    paddingRight: 14,
    backgroundColor: 'transparent',
    borderColor: 'var(--sw-border)',
    color: 'var(--sw-text-muted)',
  },
  compact: {
    paddingTop: 6,
    paddingBottom: 6,
    paddingLeft: 12,
    paddingRight: 12,
    fontSize: 11,
    backgroundColor: 'transparent',
    borderColor: 'var(--sw-border)',
    color: 'var(--sw-text-muted)',
  },
  disabled: {
    opacity: 0.55,
    cursor: 'not-allowed',
  },
});

export interface AsyncButtonProps {
  children: ReactNode;
  loading?: boolean;
  loadingLabel?: string;
  disabled?: boolean;
  icon?: LucideIcon;
  variant?: 'primary' | 'secondary' | 'compact';
  type?: 'button' | 'submit';
  onClick?: () => void | Promise<void>;
  'aria-label'?: string;
}

export default function AsyncButton({
  children,
  loading = false,
  loadingLabel,
  disabled = false,
  icon: Icon,
  variant = 'primary',
  type = 'button',
  onClick,
  'aria-label': ariaLabel,
}: AsyncButtonProps) {
  const isDisabled = disabled || loading;
  const variantStyle =
    variant === 'primary'
      ? styles.primary
      : variant === 'compact'
        ? styles.compact
        : styles.secondary;

  const buttonProps =
    variant === 'primary'
      ? primaryButtonProps('default', variantStyle, isDisabled && styles.disabled)
      : stylex.props(styles.base, variantStyle, isDisabled && styles.disabled);

  return (
    <button
      type={type}
      aria-label={ariaLabel}
      disabled={isDisabled}
      onClick={onClick}
      {...buttonProps}
    >
      {loading ? (
        <>
          <Loader2 size={14} className="sw-spin" aria-hidden />
          {loadingLabel ?? children}
        </>
      ) : (
        <>
          {Icon ? <Icon size={14} aria-hidden /> : null}
          {children}
        </>
      )}
    </button>
  );
}
