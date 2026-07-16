import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import * as stylex from '@stylexjs/stylex';
import { ChevronDown, Check } from 'lucide-react';

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  'aria-label'?: string;
}

const styles = stylex.create({
  root: {
    position: 'relative',
    width: '100%',
  },
  trigger: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 12,
    paddingRight: 12,
    borderRadius: 'var(--sw-radius-md)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: {
      default: 'var(--sw-border)',
      ':hover': 'var(--sw-border-glow)',
    },
    backgroundColor: 'var(--sw-surface-2)',
    color: 'var(--sw-text)',
    fontSize: 13,
    fontFamily: 'var(--font-body)',
    cursor: {
      default: 'pointer',
      ':disabled': 'not-allowed',
    },
    opacity: {
      default: 1,
      ':disabled': 0.5,
    },
    outline: 'none',
    boxShadow: {
      default: 'none',
      ':focus-visible': '0 0 0 3px var(--sw-accent-dim)',
    },
    transitionProperty: 'border-color, box-shadow, background-color',
    transitionDuration: '180ms',
    transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)',
    textAlign: 'left',
  },
  triggerOpen: {
    borderColor: 'rgba(249,115,22,0.45)',
    boxShadow: '0 0 0 3px var(--sw-accent-dim)',
  },
  value: {
    flex: 1,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  placeholder: {
    color: 'var(--sw-text-muted)',
  },
  chevron: {
    color: 'var(--sw-text-muted)',
    flexShrink: 0,
    transitionProperty: 'transform',
    transitionDuration: '180ms',
  },
  chevronOpen: {
    transform: 'rotate(180deg)',
    color: 'var(--sw-accent)',
  },
});

interface MenuCoords {
  top: number;
  left: number;
  width: number;
}

export default function Select({
  value,
  options,
  onChange,
  placeholder = 'Select…',
  disabled,
  'aria-label': ariaLabel,
}: SelectProps) {
  const [open, setOpen] = useState(false);
  const [coords, setCoords] = useState<MenuCoords | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const listId = useId();
  const selected = options.find((o) => o.value === value);

  const updateCoords = () => {
    const trigger = rootRef.current?.querySelector('button');
    if (!trigger) return;
    const rect = trigger.getBoundingClientRect();
    setCoords({
      top: rect.bottom + 6,
      left: rect.left,
      width: rect.width,
    });
  };

  useLayoutEffect(() => {
    if (!open) {
      setCoords(null);
      return;
    }
    updateCoords();
  }, [open]);

  useEffect(() => {
    if (!open) return;

    const onDoc = (e: MouseEvent) => {
      const target = e.target as Node;
      if (rootRef.current?.contains(target)) return;
      if (menuRef.current?.contains(target)) return;
      setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    const onReposition = () => {
      updateCoords();
    };

    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    window.addEventListener('resize', onReposition);
    window.addEventListener('scroll', onReposition, true);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onKey);
      window.removeEventListener('resize', onReposition);
      window.removeEventListener('scroll', onReposition, true);
    };
  }, [open]);

  const menu =
    open && coords
      ? createPortal(
          <div
            ref={menuRef}
            id={listId}
            role="listbox"
            className="sw-select-menu sw-select-menu--portal"
            style={{
              top: coords.top,
              left: coords.left,
              width: coords.width,
            }}
          >
            {options.map((opt) => {
              const active = opt.value === value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  role="option"
                  aria-selected={active}
                  className="sw-select-option"
                  onClick={() => {
                    onChange(opt.value);
                    setOpen(false);
                  }}
                >
                  <span>{opt.label}</span>
                  {active && <Check size={14} />}
                </button>
              );
            })}
          </div>,
          document.body,
        )
      : null;

  return (
    <div ref={rootRef} {...stylex.props(styles.root)}>
      <button
        type="button"
        disabled={disabled}
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        onClick={() => setOpen((v) => !v)}
        {...stylex.props(styles.trigger, open && styles.triggerOpen)}
      >
        <span {...stylex.props(styles.value, !selected && styles.placeholder)}>
          {selected?.label ?? placeholder}
        </span>
        <ChevronDown
          size={15}
          {...stylex.props(styles.chevron, open && styles.chevronOpen)}
        />
      </button>
      {menu}
    </div>
  );
}
