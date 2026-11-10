import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketEvent } from '../types';

type MessageHandler = (event: WebSocketEvent) => void;

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastMessage, setLastMessage] = useState<WebSocketEvent | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef<Set<MessageHandler>>(new Set());
  const reconnectTimerRef = useRef<any>(null);

  const subscribe = useCallback((handler: MessageHandler) => {
    handlersRef.current.add(handler);
    return () => {
      handlersRef.current.delete(handler);
    };
  }, []);

  const connect = useCallback(() => {
    if (socketRef.current && (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws`;

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('[WebSocket] 已连接至工厂物联网流计算总线:', wsUrl);
        if (reconnectTimerRef.current) {
          clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          if (event.data === 'pong') return;
          const parsed: WebSocketEvent = JSON.parse(event.data);
          setLastMessage(parsed);
          handlersRef.current.forEach((handler) => handler(parsed));
        } catch (e) {
          // ignore plain text ping/pong
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        socketRef.current = null;
        console.log('[WebSocket] 链路断开，3秒后自动尝试重连...');
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      ws.onerror = (err) => {
        console.warn('[WebSocket] 连接异常:', err);
        ws.close();
      };
    } catch (e) {
      console.error('[WebSocket] 初始化异常:', e);
    }
  }, []);

  useEffect(() => {
    connect();

    // 心跳保活
    const heartbeat = setInterval(() => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send('ping');
      }
    }, 15000);

    return () => {
      clearInterval(heartbeat);
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  return { isConnected, lastMessage, subscribe };
};
