/**
 * Custom onboarding tour (Floating UI + StyleX).
 *
 * Do NOT `npm install react-spotlight` — registry name is still squatted by
 * MatisLepik/react-spotlight@1.1.0 (2017 dimmer). The pack's API
 * (SpotlightProvider + SpotlightTour + start('id')) belongs to
 * github.com/btahir/react-spotlight, which is not that npm package.
 * Keep this in-repo tour until btahir publishes under a unique name/scope.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';
import { computePosition, flip, offset, shift, autoUpdate } from '@floating-ui/dom';
import * as stylex from '@stylexjs/stylex';
import { onboardingSteps, type TourStep } from './tourSteps';

const TOUR_SEEN_KEY = 'stromwart-tour-completed';
const TOUR_ID = 'onboarding';

interface SpotlightContextValue {
  start: (id?: string) => void;
  stop: () => void;
  isActive: boolean;
}

const SpotlightContext = createContext<SpotlightContextValue>({
  start: () => {},
  stop: () => {},
  isActive: false,
});

export function useSpotlight() {
  return useContext(SpotlightContext);
}

interface Props {
  children: ReactNode;
}

function lockPageScroll() {
  const html = document.documentElement;
  const body = document.body;
  const main = document.querySelector('main');

  const prev = {
    htmlOverflow: html.style.overflow,
    bodyOverflow: body.style.overflow,
    bodyPaddingRight: body.style.paddingRight,
    mainOverflow: main instanceof HTMLElement ? main.style.overflow : '',
  };

  // Avoid layout shift when the scrollbar disappears.
  const scrollbar = window.innerWidth - html.clientWidth;
  if (scrollbar > 0) {
    body.style.paddingRight = `${scrollbar}px`;
  }

  html.style.overflow = 'hidden';
  body.style.overflow = 'hidden';
  if (main instanceof HTMLElement) main.style.overflow = 'hidden';

  const block = (e: Event) => {
    e.preventDefault();
  };
  // Capture wheel/touch so nested overflow:auto panes cannot scroll either.
  document.addEventListener('wheel', block, { passive: false, capture: true });
  document.addEventListener('touchmove', block, { passive: false, capture: true });

  return () => {
    html.style.overflow = prev.htmlOverflow;
    body.style.overflow = prev.bodyOverflow;
    body.style.paddingRight = prev.bodyPaddingRight;
    if (main instanceof HTMLElement) main.style.overflow = prev.mainOverflow;
    document.removeEventListener('wheel', block, true);
    document.removeEventListener('touchmove', block, true);
  };
}

export default function TourProvider({ children }: Props) {
  const [active, setActive] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [anchorRect, setAnchorRect] = useState<DOMRect | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);
  const targetRef = useRef<HTMLElement | null>(null);

  const steps = onboardingSteps;
  const step: TourStep | undefined = steps[stepIndex];

  const markDone = useCallback(() => {
    localStorage.setItem(TOUR_SEEN_KEY, 'true');
    setActive(false);
    setStepIndex(0);
    setAnchorRect(null);
    setTooltipPos(null);
    targetRef.current = null;
  }, []);

  const start = useCallback((id?: string) => {
    if (id && id !== TOUR_ID) return;
    setStepIndex(0);
    setActive(true);
  }, []);

  const stop = useCallback(() => {
    markDone();
  }, [markDone]);

  const value = useMemo(
    () => ({ start, stop, isActive: active }),
    [start, stop, active],
  );

  // Per step: scroll target into place → measure → then freeze the page.
  useEffect(() => {
    if (!active || !step) return;

    let cancelled = false;
    let unlockScroll: (() => void) | null = null;

    const el = document.querySelector(step.target) as HTMLElement | null;
    if (!el) {
      if (stepIndex < steps.length - 1) {
        setStepIndex((i) => i + 1);
      } else {
        markDone();
      }
      return;
    }

    targetRef.current = el;

    // Unlock any prior freeze so scrollIntoView can actually move the page.
    document.documentElement.style.overflow = '';
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    const main = document.querySelector('main');
    if (main instanceof HTMLElement) {
      main.style.overflow = '';
    }

    el.scrollIntoView({ behavior: 'instant', block: 'center', inline: 'nearest' });

    // Wait two frames so layout/scroll settle before we measure + lock.
    const measureAndLock = () => {
      if (cancelled) return;
      const rect = el.getBoundingClientRect();
      setAnchorRect(rect);
      setTooltipPos(null);
      unlockScroll = lockPageScroll();
    };

    let raf2 = 0;
    const raf1 = requestAnimationFrame(() => {
      raf2 = requestAnimationFrame(measureAndLock);
    });

    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') markDone();
    };
    const onResize = () => {
      if (targetRef.current) setAnchorRect(targetRef.current.getBoundingClientRect());
    };
    window.addEventListener('keydown', onKey);
    window.addEventListener('resize', onResize);

    return () => {
      cancelled = true;
      cancelAnimationFrame(raf1);
      cancelAnimationFrame(raf2);
      unlockScroll?.();
      window.removeEventListener('keydown', onKey);
      window.removeEventListener('resize', onResize);
    };
  }, [active, step, stepIndex, steps.length, markDone]);

  useLayoutEffect(() => {
    if (!active || !step || !anchorRect || !tooltipRef.current) return;

    const reference = {
      getBoundingClientRect: () =>
        targetRef.current?.getBoundingClientRect() ?? anchorRect,
    };
    const floating = tooltipRef.current;
    const placement = step.placement ?? 'bottom';

    return autoUpdate(reference, floating, () => {
      void computePosition(reference, floating, {
        placement,
        middleware: [offset(16), flip({ padding: 16 }), shift({ padding: 16 })],
      }).then(({ x, y }) => setTooltipPos({ x, y }));
    });
  }, [active, step, anchorRect, stepIndex]);

  // Spotlight uses the live target box (re-read on each tooltip reposition render).
  const spotlightRect = targetRef.current?.getBoundingClientRect() ?? anchorRect;

  const onNext = () => {
    if (stepIndex >= steps.length - 1) {
      markDone();
    } else {
      setStepIndex((i) => i + 1);
    }
  };

  const onPrev = () => setStepIndex((i) => Math.max(0, i - 1));

  return (
    <SpotlightContext.Provider value={value}>
      {children}
      {active &&
        step &&
        createPortal(
          <>
            {/* Full-screen shield: only the dialog receives clicks */}
            <div
              {...stylex.props(styles.blocker)}
              aria-hidden
              onClick={(e) => e.stopPropagation()}
            />
            {spotlightRect && (
              <div
                {...stylex.props(styles.spotlight)}
                style={{
                  top: spotlightRect.top - 8,
                  left: spotlightRect.left - 8,
                  width: spotlightRect.width + 16,
                  height: spotlightRect.height + 16,
                }}
              />
            )}
            {spotlightRect && (
              <div
                ref={tooltipRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="tour-title"
                {...stylex.props(styles.tooltip)}
                style={
                  tooltipPos
                    ? { top: tooltipPos.y, left: tooltipPos.x, visibility: 'visible' }
                    : { top: 0, left: 0, visibility: 'hidden' }
                }
              >
                <div id="tour-title" {...stylex.props(styles.title)}>
                  {step.title}
                </div>
                <div {...stylex.props(styles.content)}>{step.content}</div>
                <div {...stylex.props(styles.footer)}>
                  <span {...stylex.props(styles.progress)}>
                    {stepIndex + 1}/{steps.length}
                  </span>
                  <div {...stylex.props(styles.actions)}>
                    {stepIndex > 0 && (
                      <button
                        type="button"
                        onClick={onPrev}
                        {...stylex.props(styles.button, styles.buttonSecondary)}
                      >
                        Back
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={markDone}
                      {...stylex.props(styles.button, styles.buttonSecondary)}
                    >
                      Skip
                    </button>
                    <button
                      type="button"
                      onClick={onNext}
                      {...stylex.props(styles.button, styles.buttonPrimary)}
                    >
                      {stepIndex >= steps.length - 1 ? 'Done' : 'Next'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>,
          document.body,
        )}
    </SpotlightContext.Provider>
  );
}

const styles = stylex.create({
  blocker: {
    position: 'fixed',
    inset: 0,
    zIndex: 99999,
    backgroundColor: 'transparent',
    cursor: 'default',
  },
  spotlight: {
    position: 'fixed',
    borderRadius: 'var(--sw-radius-md)',
    boxShadow: '0 0 0 9999px rgba(0,0,0,0.65)',
    borderWidth: 2,
    borderStyle: 'solid',
    borderColor: 'var(--sw-accent)',
    zIndex: 100000,
    pointerEvents: 'none',
    transitionProperty: 'top, left, width, height',
    transitionDuration: '200ms',
  },
  tooltip: {
    position: 'fixed',
    backgroundColor: 'var(--sw-surface)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    borderRadius: 'var(--sw-radius-lg)',
    paddingTop: 20,
    paddingBottom: 20,
    paddingLeft: 24,
    paddingRight: 24,
    maxWidth: 360,
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
    zIndex: 100001,
  },
  title: {
    fontSize: 15,
    fontWeight: 700,
    color: 'var(--sw-text)',
    marginBottom: 8,
  },
  content: {
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    lineHeight: 1.6,
    marginBottom: 16,
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 8,
  },
  actions: {
    display: 'flex',
    gap: 8,
  },
  button: {
    paddingTop: 6,
    paddingBottom: 6,
    paddingLeft: 14,
    paddingRight: 14,
    borderRadius: 'var(--sw-radius-sm)',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    borderWidth: 0,
    borderStyle: 'none',
  },
  buttonPrimary: {
    backgroundColor: 'var(--sw-accent)',
    color: '#fff',
  },
  buttonSecondary: {
    backgroundColor: 'transparent',
    color: 'var(--sw-text-muted)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
  },
  progress: {
    fontSize: 11,
    color: 'var(--sw-text-muted)',
    fontFamily: 'var(--font-mono)',
  },
});
