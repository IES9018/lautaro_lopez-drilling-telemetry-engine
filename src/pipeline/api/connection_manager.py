"""Gestor de conexiones WebSocket con backpressure por cliente."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Literal

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState

from src.pipeline.api.advisor_store import AdvisorRecommendationRecordDTO
from src.pipeline.api.schemas.broadcast import TelemetryStreamBroadcastDTO

logger = logging.getLogger(__name__)

EnvelopeType = Literal["telemetry_frame", "advisor_recommendation"]


@dataclass
class _ClientSlot:
    """Cola acotada + task de envío por cliente."""

    queue: asyncio.Queue[bytes]
    sender: asyncio.Task[None]


@dataclass
class ConnectionManager:
    """Registro de clientes WebSocket con política *drop-oldest*.

    Parameters
    ----------
    queue_maxsize : int
        Capacidad de la cola por cliente (default 2).
    """

    queue_maxsize: int = 2
    _clients: dict[WebSocket, _ClientSlot] = field(default_factory=dict, init=False)

    async def connect(self, websocket: WebSocket) -> None:
        """Acepta el handshake y registra el cliente con cola acotada."""
        await websocket.accept()
        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=self.queue_maxsize)
        sender = asyncio.create_task(self._sender_loop(websocket, queue))
        self._clients[websocket] = _ClientSlot(queue=queue, sender=sender)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remueve el cliente y cancela su task de envío (idempotente)."""
        slot = self._clients.pop(websocket, None)
        if slot is None:
            return
        slot.sender.cancel()

    async def broadcast(self, payload: TelemetryStreamBroadcastDTO) -> None:
        """Encola un envelope ``telemetry_frame``; drop-oldest si la cola está llena."""
        envelope = {
            "type": "telemetry_frame",
            "data": json.loads(payload.model_dump_json()),
        }
        await self._enqueue_bytes(json.dumps(envelope).encode("utf-8"))

    async def broadcast_advisor(
        self,
        record: AdvisorRecommendationRecordDTO,
    ) -> None:
        """Encola un envelope ``advisor_recommendation``."""
        envelope = {
            "type": "advisor_recommendation",
            "data": json.loads(record.model_dump_json()),
        }
        await self._enqueue_bytes(json.dumps(envelope).encode("utf-8"))

    async def _enqueue_bytes(self, data: bytes) -> None:
        dead: list[WebSocket] = []
        for websocket, slot in list(self._clients.items()):
            if websocket.client_state != WebSocketState.CONNECTED:
                dead.append(websocket)
                continue
            queue = slot.queue
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(data)
            except asyncio.QueueFull:
                pass
        for websocket in dead:
            self.disconnect(websocket)

    async def close_all(self) -> None:
        """Cierra todos los sockets activos (shutdown del lifespan)."""
        for websocket in list(self._clients.keys()):
            self.disconnect(websocket)
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.close()
            except Exception:  # noqa: BLE001 — best-effort en shutdown
                logger.debug("websocket close failed", exc_info=True)

    def __len__(self) -> int:
        """Número de clientes registrados."""
        return len(self._clients)

    async def _sender_loop(
        self,
        websocket: WebSocket,
        queue: asyncio.Queue[bytes],
    ) -> None:
        try:
            while True:
                data = await queue.get()
                await websocket.send_bytes(data)
        except (WebSocketDisconnect, asyncio.CancelledError):
            return
        except Exception:  # noqa: BLE001
            logger.debug("sender loop ended", exc_info=True)
            return
        finally:
            self.disconnect(websocket)


__all__ = ["ConnectionManager", "EnvelopeType"]
