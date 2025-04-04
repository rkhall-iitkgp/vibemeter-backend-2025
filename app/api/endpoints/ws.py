from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.socket import manager

router = APIRouter()


@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Allow users to connect via WebSocket and listen for events."""
    print(user_id)
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()  # Receive messages (optional)
            print(f"Message received from {user_id}: {data}")
            await websocket.send_text(
                f"Message from {user_id}: {data}"
            )  # Echo message (optional)
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"User {user_id} disconnected")
