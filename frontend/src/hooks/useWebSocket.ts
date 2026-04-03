import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
    type: string;
    [key: string]: any;
}

export const useWebSocket = (sessionId: string | null, onMessage?: (data: WebSocketMessage) => void) => {
    const [status, setStatus] = useState<'connecting' | 'open' | 'closed'>('closed');
    const ws = useRef<WebSocket | null>(null);
    const reconnectTimeout = useRef<any>(null);
    const reconnectAttempts = useRef(0);

    const connect = useCallback(() => {
        if (!sessionId) return;

        // Determine WebSocket URL from API URL
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const wsProtocol = apiUrl.startsWith('https') ? 'wss:' : 'ws:';
        const wsHost = apiUrl.replace(/^https?:\/\//, '');
        const apiPrefix = '/api/v1/ws'; 
        const url = `${wsProtocol}//${wsHost}${apiPrefix}/${sessionId}`;

        console.log(`Connecting to WebSocket: ${url}`);
        setStatus('connecting');

        try {
            ws.current = new WebSocket(url);

            ws.current.onopen = () => {
                console.log('WebSocket connected');
                setStatus('open');
                reconnectAttempts.current = 0;
            };

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (onMessage) {
                        onMessage(data);
                    }
                } catch (err) {
                    console.error('Failed to parse WebSocket message', err);
                }
            };

            ws.current.onclose = (event) => {
                console.log(`WebSocket closed: ${event.reason}`);
                setStatus('closed');
                
                // Don't reconnect if it was a clean close or if session changed
                if (!event.wasClean && sessionId) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
                    console.log(`Reconnecting in ${delay}ms...`);
                    reconnectTimeout.current = setTimeout(() => {
                        reconnectAttempts.current += 1;
                        connect();
                    }, delay);
                }
            };

            ws.current.onerror = (err) => {
                console.error('WebSocket error', err);
                ws.current?.close();
            };
        } catch (err) {
            console.error('Failed to create WebSocket connection', err);
            setStatus('closed');
        }
    }, [sessionId, onMessage]);

    useEffect(() => {
        connect();

        return () => {
            if (ws.current) {
                ws.current.close(1000, 'Component unmounted');
            }
            if (reconnectTimeout.current) {
                clearTimeout(reconnectTimeout.current);
            }
        };
    }, [connect]);

    return { status };
};
