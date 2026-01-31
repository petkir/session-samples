import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketOptions {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: string) => void;
}

export function useWebSocket(url: string, options?: UseWebSocketOptions) {
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const optionsRef = useRef(options);

  // Update options ref without triggering reconnect
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const sendMessage = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    }
  }, []);

  useEffect(() => {
    const wsUrl = url.startsWith('ws://') || url.startsWith('wss://') 
      ? url 
      : `ws://localhost:8765${url}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setReadyState(WebSocket.OPEN);
      optionsRef.current?.onOpen?.();
    };

    ws.onclose = () => {
      setReadyState(WebSocket.CLOSED);
      optionsRef.current?.onClose?.();
    };

    ws.onerror = () => {
      optionsRef.current?.onError?.('WebSocket error');
    };

    ws.onmessage = (event) => {
      setLastMessage(event.data);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [url]); // Only reconnect when URL changes

  return { sendMessage, lastMessage, readyState };
}
