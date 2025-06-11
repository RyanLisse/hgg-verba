import { getWebSocketApiHost } from "@/app/util";

export interface WebSocketConfig {
  maxRetries?: number;
  initialRetryDelay?: number;
  maxRetryDelay?: number;
  heartbeatInterval?: number;
  reconnectOnError?: boolean;
  messageQueueSize?: number;
}

export type ConnectionState = "CONNECTING" | "CONNECTED" | "DISCONNECTED" | "RECONNECTING" | "ERROR";

export interface WebSocketMessage {
  id: string;
  data: any;
  timestamp: number;
  retries: number;
}

export class ReconnectingWebSocket {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private retryCount = 0;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private messageQueue: WebSocketMessage[] = [];
  private isDestroyed = false;
  private connectionState: ConnectionState = "DISCONNECTED";
  private listeners: Map<string, Set<Function>> = new Map();
  private endpoint: string;

  constructor(endpoint: string, config: WebSocketConfig = {}) {
    this.endpoint = endpoint;
    this.config = {
      maxRetries: config.maxRetries ?? 5,
      initialRetryDelay: config.initialRetryDelay ?? 1000,
      maxRetryDelay: config.maxRetryDelay ?? 30000,
      heartbeatInterval: config.heartbeatInterval ?? 30000,
      reconnectOnError: config.reconnectOnError ?? true,
      messageQueueSize: config.messageQueueSize ?? 100,
    };
  }

  // Event handling
  public on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  public off(event: string, callback: Function): void {
    this.listeners.get(event)?.delete(callback);
  }

  private emit(event: string, ...args: any[]): void {
    this.listeners.get(event)?.forEach(callback => {
      try {
        callback(...args);
      } catch (error) {
        console.error(`Error in ${event} handler:`, error);
      }
    });
  }

  // Connection management
  public connect(): void {
    if (this.isDestroyed) return;
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.updateState("CONNECTING");
    
    try {
      const socketHost = getWebSocketApiHost();
      const fullUrl = `${socketHost}${this.endpoint}`;
      this.ws = new WebSocket(fullUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      this.handleReconnect();
    }
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log(`WebSocket connected to ${this.endpoint}`);
      this.updateState("CONNECTED");
      this.retryCount = 0;
      this.startHeartbeat();
      this.flushMessageQueue();
      this.emit("open");
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle pong messages
        if (data.type === "pong") {
          this.emit("pong");
          return;
        }

        this.emit("message", data);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
        this.emit("error", error);
      }
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      this.updateState("ERROR");
      this.emit("error", error);
    };

    this.ws.onclose = (event) => {
      console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
      this.stopHeartbeat();
      
      if (event.wasClean || this.isDestroyed) {
        this.updateState("DISCONNECTED");
        this.emit("close", event);
        return;
      }

      // Handle unexpected closure
      if (this.config.reconnectOnError && this.retryCount < this.config.maxRetries) {
        this.handleReconnect();
      } else {
        this.updateState("DISCONNECTED");
        this.emit("close", event);
      }
    };
  }

  private handleReconnect(): void {
    if (this.isDestroyed || this.reconnectTimer) return;

    this.updateState("RECONNECTING");
    this.retryCount++;

    // Calculate backoff delay with jitter
    const baseDelay = Math.min(
      this.config.initialRetryDelay * Math.pow(2, this.retryCount - 1),
      this.config.maxRetryDelay
    );
    const jitter = Math.random() * 0.3 * baseDelay; // 30% jitter
    const delay = baseDelay + jitter;

    console.log(`Reconnecting in ${Math.round(delay)}ms (attempt ${this.retryCount}/${this.config.maxRetries})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  // Message handling
  public send(data: any): void {
    const message: WebSocketMessage = {
      id: crypto.randomUUID(),
      data,
      timestamp: Date.now(),
      retries: 0,
    };

    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(data));
        this.emit("sent", message);
      } catch (error) {
        console.error("Failed to send message:", error);
        this.queueMessage(message);
      }
    } else {
      this.queueMessage(message);
    }
  }

  private queueMessage(message: WebSocketMessage): void {
    // Add to queue with size limit
    this.messageQueue.push(message);
    if (this.messageQueue.length > this.config.messageQueueSize) {
      const dropped = this.messageQueue.shift();
      this.emit("messageDropped", dropped);
    }
    this.emit("messageQueued", message);
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift()!;
      try {
        this.ws.send(JSON.stringify(message.data));
        this.emit("sent", message);
      } catch (error) {
        console.error("Failed to send queued message:", error);
        message.retries++;
        if (message.retries < 3) {
          this.messageQueue.unshift(message); // Put it back at the front
        } else {
          this.emit("messageDropped", message);
        }
        break;
      }
    }
  }

  // Heartbeat management
  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: "ping" });
      }
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  // State management
  private updateState(state: ConnectionState): void {
    if (this.connectionState !== state) {
      const oldState = this.connectionState;
      this.connectionState = state;
      this.emit("stateChange", state, oldState);
    }
  }

  public getState(): ConnectionState {
    return this.connectionState;
  }

  public isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // Cleanup
  public disconnect(): void {
    this.isDestroyed = true;
    this.stopHeartbeat();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }

    this.messageQueue = [];
    this.listeners.clear();
    this.updateState("DISCONNECTED");
  }

  // Utility methods
  public getQueueSize(): number {
    return this.messageQueue.length;
  }

  public clearQueue(): void {
    this.messageQueue = [];
    this.emit("queueCleared");
  }

  public reconnect(): void {
    this.retryCount = 0;
    if (this.ws) {
      this.ws.close();
    }
    this.connect();
  }
}