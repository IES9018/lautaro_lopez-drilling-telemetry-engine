"""Router WebSocket ``/ws/telemetry``."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.pipeline.api.connection_manager import ConnectionManager

router = APIRouter(tags=["telemetry-ws"])


def get_connection_manager(websocket: WebSocket) -> ConnectionManager:
    """Resuelve el ``ConnectionManager`` desde ``app.state``."""
    return websocket.app.state.connections  # type: ignore[no-any-return]


@router.websocket("/ws/telemetry")
async def telemetry_websocket(websocket: WebSocket) -> None:
    """Stream consolidado a ~60 FPS; el loop solo detecta cierre del cliente."""
    manager = get_connection_manager(websocket)
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        pass
    except RuntimeError:
        # Starlette raises if receive() is called again after disconnect.
        pass
    finally:
        manager.disconnect(websocket)
