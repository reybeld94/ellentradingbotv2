from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..websockets import ws_manager

router = APIRouter()

@router.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
