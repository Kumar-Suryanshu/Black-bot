import { useEffect, useRef, useState } from 'react';
import type { Event } from '../api/types';

export interface UseEventStreamOptions {
  projectId: string | null;
  onEvent?: (event: Event) => void;
  onError?: (err: any) => void;
}

export function useEventStream({ projectId, onEvent, onError }: UseEventStreamOptions) {
  const [events, setEvents] = useState<Event[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connected' | 'reconnecting' | 'offline'>('idle');
  const lastEventIdRef = useRef<number>(0);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!projectId) {
      setConnectionStatus('idle');
      return;
    }

    // Restore last seen event id from sessionStorage for seamless reload resume
    const storedLastId = sessionStorage.getItem(`rerun_last_event_${projectId}`);
    if (storedLastId) {
      const parsed = parseInt(storedLastId, 10);
      if (!isNaN(parsed) && parsed > 0) {
        lastEventIdRef.current = Math.max(lastEventIdRef.current, parsed);
      }
    }

    setConnectionStatus('reconnecting');
    let reconnectTimeout: any = null;

    function connect() {
      if (esRef.current) {
        esRef.current.close();
      }

      // Resume from Last-Event-ID across page refreshes and disconnects
      const resumeId = lastEventIdRef.current;
      const url = `/api/projects/${projectId}/events?last_event_id=${resumeId}`;
      const es = new EventSource(url);
      esRef.current = es;

      es.onopen = () => {
        setConnectionStatus('connected');
      };

      es.onmessage = (msgEvent) => {
        try {
          const data: Event = JSON.parse(msgEvent.data);
          if (data && data.id) {
            lastEventIdRef.current = Math.max(lastEventIdRef.current, data.id);
            sessionStorage.setItem(`rerun_last_event_${projectId}`, String(lastEventIdRef.current));
            setEvents((prev) => {
              if (prev.some((e) => e.id === data.id)) return prev;
              return [...prev, data];
            });
            onEvent?.(data);
          }
        } catch (e) {
          console.error('Failed to parse SSE event data', e);
        }
      };

      es.onerror = (err) => {
        setConnectionStatus('reconnecting');
        onError?.(err);
        es.close();
        reconnectTimeout = setTimeout(connect, 3000);
      };
    }

    connect();

    return () => {
      if (esRef.current) {
        esRef.current.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, [projectId]);

  return { events, connectionStatus };
}
