const normalizeWsBaseUrl = (value: string | undefined): string => {
  if (!value) {
    return 'ws://localhost:8000';
  }

  const trimmed = value.replace(/\/+$/, '');
  if (trimmed.startsWith('ws://') || trimmed.startsWith('wss://')) {
    return trimmed;
  }
  if (trimmed.startsWith('http://')) {
    return `ws://${trimmed.slice('http://'.length)}`;
  }
  if (trimmed.startsWith('https://')) {
    return `wss://${trimmed.slice('https://'.length)}`;
  }
  return trimmed;
};

const WS_BASE = normalizeWsBaseUrl(import.meta.env.VITE_WS_URL);

type EventHandler = (data: unknown) => void;

export class WsClient {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: Map<string, Set<EventHandler>> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 2000;
  private shouldReconnect = true;

  constructor(path: string) {
    this.url = `${WS_BASE}${path}`;
  }

  connect() {
    this.shouldReconnect = true;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log(`[WS] Connected: ${this.url}`);
      this.reconnectDelay = 2000;
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const { type, data } = msg;
        this.handlers.get(type)?.forEach((fn) => fn(data));
        this.handlers.get('*')?.forEach((fn) => fn(msg));
      } catch {
        console.warn('[WS] Failed to parse message', event.data);
      }
    };

    this.ws.onclose = () => {
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => {
          this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 30000);
          this.connect();
        }, this.reconnectDelay);
      }
    };

    this.ws.onerror = (err) => console.error('[WS] Error', err);
  }

  on(event: string, handler: EventHandler) {
    if (!this.handlers.has(event)) this.handlers.set(event, new Set());
    this.handlers.get(event)!.add(handler);
    return () => this.handlers.get(event)?.delete(handler); // unsubscribe fn
  }

  send(type: string, data: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    }
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }
}
