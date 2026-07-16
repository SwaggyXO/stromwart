import { toast as sonnerToast } from 'sonner';
import type { AlertRead, AlertSeverity } from '@/types';

export { sonnerToast as toast };

function severityPrefix(severity: AlertSeverity): string {
  return severity.toUpperCase();
}

export function showAlertToast(
  alert: AlertRead,
  actions: { onAck: () => void; onView: () => void },
) {
  const title = `${severityPrefix(alert.severity)} · ${alert.description}`;
  const options = {
    description: alert.slice_key,
    duration: 12_000,
    action: {
      label: 'Ack',
      onClick: actions.onAck,
    },
    cancel: {
      label: 'View',
      onClick: actions.onView,
    },
  };

  if (alert.severity === 'critical' || alert.severity === 'high') {
    sonnerToast.error(title, options);
  } else if (alert.severity === 'medium') {
    sonnerToast.warning(title, options);
  } else {
    sonnerToast(title, options);
  }
}
