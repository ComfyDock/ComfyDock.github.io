from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from .dependencies import get_connection_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):
    connection_manager = websocket.app.state.connection_manager
    await connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
