/** Interceptores REST + WebSocket para E2E sin backend real. */

import type { Page } from "@playwright/test";

import type { OrchestratorStatus } from "../../src/types/telemetry";
import {
  advisorEnvelope,
  makeAdvisorRecord,
  makeStatus,
  makeTelemetryFrame,
  telemetryEnvelope,
} from "./fixtures";

const API_GLOB = "**/api/v1/simulation/**";

export interface MockApiOptions {
  /** Status inicial que devolverá GET /status y POSTs exitosos. */
  initialStatus?: OrchestratorStatus;
  /** Si true, POST /start responde 500. */
  failStart?: boolean;
  /** Frames a emitir al abrir el WS (default: uno normal). */
  initialFrames?: ReturnType<typeof telemetryEnvelope>[];
  /** Si true, emite también una recommendation al abrir. */
  emitAdvisorOnOpen?: boolean;
}

type BridgeMessage = { type: "telemetry" | "advisor"; payload: unknown };

/**
 * Mockea REST de simulación y reemplaza WebSocket en página con un bridge
 * controlable desde el test (más fiable que routeWebSocket para pushes).
 */
export async function installMocks(
  page: Page,
  options: MockApiOptions = {},
): Promise<{
  pushTelemetry: (envelope: unknown) => Promise<void>;
  pushAdvisor: (envelope: unknown) => Promise<void>;
  getLastPresetBody: () => unknown;
}> {
  let status = options.initialStatus ?? makeStatus();
  let lastPresetBody: unknown = null;

  const frames =
    options.initialFrames ?? [telemetryEnvelope(makeTelemetryFrame())];
  const bootstrap: BridgeMessage[] = frames.map((payload) => ({
    type: "telemetry" as const,
    payload,
  }));
  if (options.emitAdvisorOnOpen) {
    bootstrap.push({
      type: "advisor",
      payload: advisorEnvelope(makeAdvisorRecord()),
    });
  }

  await page.addInitScript(
    ({ boot }: { boot: BridgeMessage[] }) => {
      type Listener = (ev: MessageEvent<string>) => void;

      const state = {
        queue: [...boot],
        socket: null as MockWebSocket | null,
      };

      class MockWebSocket {
        static readonly CONNECTING = 0;
        static readonly OPEN = 1;
        static readonly CLOSING = 2;
        static readonly CLOSED = 3;

        readonly CONNECTING = 0;
        readonly OPEN = 1;
        readonly CLOSING = 2;
        readonly CLOSED = 3;

        readyState = MockWebSocket.CONNECTING;
        onopen: ((ev: Event) => void) | null = null;
        onclose: ((ev: CloseEvent) => void) | null = null;
        onerror: ((ev: Event) => void) | null = null;
        onmessage: Listener | null = null;
        readonly url: string;

        constructor(url: string | URL) {
          this.url = String(url);
          state.socket = this;
          queueMicrotask(() => {
            this.readyState = MockWebSocket.OPEN;
            this.onopen?.(new Event("open"));
            for (const msg of state.queue.splice(0)) {
              this._emit(JSON.stringify(msg.payload));
            }
          });
        }

        send(_data: string): void {
          /* ignore client → server */
        }

        close(): void {
          this.readyState = MockWebSocket.CLOSED;
          this.onclose?.(new CloseEvent("close"));
        }

        addEventListener(
          type: string,
          listener: EventListenerOrEventListenerObject,
        ): void {
          if (type === "open") this.onopen = listener as (ev: Event) => void;
          if (type === "message") this.onmessage = listener as Listener;
          if (type === "close") {
            this.onclose = listener as (ev: CloseEvent) => void;
          }
          if (type === "error") this.onerror = listener as (ev: Event) => void;
        }

        removeEventListener(): void {
          /* no-op for test mock */
        }

        _emit(data: string): void {
          this.onmessage?.({ data } as MessageEvent<string>);
        }
      }

      (
        window as unknown as {
          WebSocket: typeof MockWebSocket;
          __dtePushWs: (payload: unknown) => void;
        }
      ).WebSocket = MockWebSocket;

      (
        window as unknown as { __dtePushWs: (payload: unknown) => void }
      ).__dtePushWs = (payload: unknown) => {
        const sock = state.socket;
        if (sock && sock.readyState === MockWebSocket.OPEN) {
          sock._emit(JSON.stringify(payload));
        } else {
          state.queue.push({ type: "telemetry", payload });
        }
      };
    },
    { boot: bootstrap },
  );

  await page.route(API_GLOB, async (route) => {
    const request = route.request();
    const method = request.method();
    const url = request.url();

    if (method === "GET" && url.includes("/status")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(status),
      });
      return;
    }

    if (method === "POST" && url.includes("/start")) {
      if (options.failStart) {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "internal error" }),
        });
        return;
      }
      const body = request.postDataJSON() as { preset?: string } | null;
      if (body?.preset) {
        status = {
          ...status,
          running: true,
          preset: body.preset as OrchestratorStatus["preset"],
        };
      } else {
        status = { ...status, running: true };
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(status),
      });
      return;
    }

    if (method === "POST" && url.includes("/stop")) {
      status = { ...status, running: false };
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(status),
      });
      return;
    }

    if (method === "POST" && url.includes("/preset")) {
      lastPresetBody = request.postDataJSON();
      const body = lastPresetBody as { preset: OrchestratorStatus["preset"] };
      status = { ...status, preset: body.preset };
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(status),
      });
      return;
    }

    await route.continue();
  });

  return {
    pushTelemetry: async (envelope: unknown) => {
      await page.evaluate((payload) => {
        (
          window as unknown as { __dtePushWs: (p: unknown) => void }
        ).__dtePushWs(payload);
      }, envelope);
    },
    pushAdvisor: async (envelope: unknown) => {
      await page.evaluate((payload) => {
        (
          window as unknown as { __dtePushWs: (p: unknown) => void }
        ).__dtePushWs(payload);
      }, envelope);
    },
    getLastPresetBody: () => lastPresetBody,
  };
}

export {
  advisorEnvelope,
  makeAdvisorRecord,
  makeStatus,
  makeTelemetryFrame,
  telemetryEnvelope,
};
export { makeCriticalFrame } from "./fixtures";
