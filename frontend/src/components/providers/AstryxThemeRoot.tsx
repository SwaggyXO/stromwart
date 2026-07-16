import { Theme } from '@astryxdesign/core/theme';
import { gothicTheme } from '@astryxdesign/theme-gothic/built';
import { ColorModeProvider, useColorMode } from '@/hooks/useColorMode';
import type { ReactNode } from 'react';

function ThemedTree({ children }: { children: ReactNode }) {
  const { mode } = useColorMode();
  return (
    <Theme theme={gothicTheme} mode={mode}>
      {children}
    </Theme>
  );
}

/** Shared color-mode + Astryx Theme (activates gothic @scope CSS on <html>). */
export default function AstryxThemeRoot({ children }: { children: ReactNode }) {
  return (
    <ColorModeProvider>
      <ThemedTree>{children}</ThemedTree>
    </ColorModeProvider>
  );
}
