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

    setConnectionStatus('reconnecting');
    let reconnectTimeout: any = null;

    function connect() {
      if (esRef.current) {
        esRef.current.close();
      }

      // EventSource url with last_id query fallback or header
      const url = `/api/projects/${projectId}/events`;
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
