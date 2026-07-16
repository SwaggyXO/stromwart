import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAppStore } from '@/store/useAppStore';
import type { LiveEventUpdate } from '@/types';

/**
 * SSE — GET /v1/events/{event_id}/stream
 * Payload schema: LiveEventUpdate { event_id, active_sessions, incidents? }
 */
export function useSSEStream(eventId: string | undefined) {
  const qc = useQueryClient();
  const setSseConnected = useAppStore((s) => s.setSseConnected);
  const setLiveUpdate = useAppStore((s) => s.setLiveUpdate);
  const esRef = useRef<EventSource | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!eventId) return;

    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      const es = new EventSource(`/api/v1/events/${eventId}/stream`);
      esRef.current = es;

      es.onopen = () => setSseConnected(true);

      es.onmessage = (event) => {
        try {
          const msg: LiveEventUpdate = JSON.parse(event.data);
          setLiveUpdate(msg);
          qc.invalidateQueries({ queryKey: ['sessions', eventId] });
          qc.invalidateQueries({ queryKey: ['kpis', eventId] });
          qc.invalidateQueries({ queryKey: ['alerts', eventId] });
          qc.invalidateQueries({ queryKey: ['incidents', eventId] });
          qc.invalidateQueries({ queryKey: ['forecast', eventId] });
        } catch {
          // ignore malformed messages
        }
      };

      es.onerror = () => {
        setSseConnected(false);
        es.close();
        esRef.current = null;
        if (!cancelled) {
          reconnectRef.current = setTimeout(connect, 5_000);
        }
      };
    };

    connect();

    return () => {
      cancelled = true;
      setSseConnected(false);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      esRef.current?.close();
      esRef.current = null;
    };
  }, [eventId, qc, setSseConnected, setLiveUpdate]);
}
