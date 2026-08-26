"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type MutableRefObject,
} from "react";

import type { AdvisorRecommendationRecord } from "@/types/advisor";
import type { TelemetryFrame } from "@/types/telemetry";
import { parseWsMessage } from "@/lib/wsEnvelope";

export type ConnectionStatus = "connecting" | "open" | "closed" | "error";

export interface TelemetryStreamState {
  connectionStatus: ConnectionStatus;
  latestFrame: TelemetryFrame | null;
  recommendations: AdvisorRecommendationRecord[];
  frameRef: MutableRefObject<TelemetryFrame | null>;
}

const DEFAULT_WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws/telemetry";

const WIDGET_MIN_INTERVAL_MS = 33;
const MAX_RECOMMENDATIONS = 20;
const BACKOFF_CAP_MS = 10_000;

/**
 * Stream WebSocket resiliente.
 * - Canvas 3D: lee `frameRef` a ~60 FPS sin re-render React.
 * - Widgets: `latestFrame` throttled ~30 Hz (A-007).
 */
export function useTelemetryStream(url: string = DEFAULT_WS_URL): TelemetryStreamState {
  const frameRef = useRef<TelemetryFrame | null>(null);
  const [latestFrame, setLatestFrame] = useState<TelemetryFrame | null>(null);
  const [recommendations, setRecommendations] = useState<
    AdvisorRecommendationRecord[]
  >([]);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("connecting");

  const lastWidgetPushMs = useRef(0);
  const backoffMs = useRef(500);
  const intentionalClose = useRef(false);

  const pushFrameThrottled = useCallback((frame: TelemetryFrame) => {
    frameRef.current = frame;
    const now = performance.now();
    if (now - lastWidgetPushMs.current >= WIDGET_MIN_INTERVAL_MS) {
      lastWidgetPushMs.current = now;
      setLatestFrame(frame);
    }
  }, []);

  useEffect(() => {
    intentionalClose.current = false;
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      setConnectionStatus("connecting");
      socket = new WebSocket(url);

      socket.onopen = () => {
        backoffMs.current = 500;
        setConnectionStatus("open");
      };

      socket.onmessage = (event: MessageEvent<string>) => {
        const envelope = parseWsMessage(event.data);
        if (!envelope) return;
        if (envelope.type === "telemetry_frame") {
          pushFrameThrottled(envelope.data);
          return;
        }
        setRecommendations((prev) =>
          [envelope.data, ...prev].slice(0, MAX_RECOMMENDATIONS),
        );
      };

      socket.onerror = () => {
        setConnectionStatus("error");
      };

      socket.onclose = () => {
        setConnectionStatus("closed");
        if (intentionalClose.current) return;
        const delay = backoffMs.current;
        backoffMs.current = Math.min(backoffMs.current * 2, BACKOFF_CAP_MS);
        reconnectTimer = setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      intentionalClose.current = true;
      if (reconnectTimer !== null) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [url, pushFrameThrottled]);

  return {
    connectionStatus,
    latestFrame,
    recommendations,
    frameRef,
  };
}
