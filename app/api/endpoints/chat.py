from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

from app.socket import manager

router = APIRouter()


@router.websocket("/{user_id}")
async def chat(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
            await manager.send_message("Heyyy, how's it going?", user_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"User {user_id} disconnected")
