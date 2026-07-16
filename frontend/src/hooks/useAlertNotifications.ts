import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAlerts } from '@/api/queries';
import { useAcknowledgeAlert } from '@/api/mutations';
import { showAlertToast } from '@/lib/toast';
import { useAppStore } from '@/store/useAppStore';

/**
 * Global alert toasts — fires when new open alerts appear for the active event.
 *
 * Hydration: on the first successful fetch for an eventId (even if empty),
 * seed seen IDs without toasting. Later open alerts that were not seeded toast.
 * Hydration lives in zustand so React StrictMode remounts do not re-seed.
 */
export function useAlertNotifications(eventId: string | undefined) {
  const navigate = useNavigate();
  const { data: alerts = [], isFetched } = useAlerts(eventId);
  const acknowledge = useAcknowledgeAlert(eventId);
  const seenAlertIds = useAppStore((s) => s.seenAlertIds);
  const alertHydratedEventId = useAppStore((s) => s.alertHydratedEventId);
  const markAlertsSeen = useAppStore((s) => s.markAlertsSeen);
  const setAlertHydratedEventId = useAppStore((s) => s.setAlertHydratedEventId);
  const resetAlertTracking = useAppStore((s) => s.resetAlertTracking);

  useEffect(() => {
    if (!eventId) {
      if (alertHydratedEventId !== null) {
        resetAlertTracking();
      }
      return;
    }

    if (alertHydratedEventId !== null && alertHydratedEventId !== eventId) {
      resetAlertTracking();
    }
  }, [eventId, alertHydratedEventId, resetAlertTracking]);

  useEffect(() => {
    if (!eventId || !isFetched) return;

    const hydrated = alertHydratedEventId === eventId;
    if (!hydrated) {
      markAlertsSeen(alerts.map((a) => a.id));
      setAlertHydratedEventId(eventId);
      return;
    }

    const seen = new Set(seenAlertIds);
    const newlySeen: string[] = [];

    for (const alert of alerts) {
      if (seen.has(alert.id)) continue;
      newlySeen.push(alert.id);
      if (alert.state === 'open') {
        showAlertToast(alert, {
          onAck: () => acknowledge.mutate(alert.id),
          onView: () => navigate('/'),
        });
      }
    }

    if (newlySeen.length > 0) {
      markAlertsSeen(newlySeen);
    }
  }, [
    alerts,
    eventId,
    isFetched,
    alertHydratedEventId,
    seenAlertIds,
    markAlertsSeen,
    setAlertHydratedEventId,
    acknowledge,
    navigate,
  ]);
}
