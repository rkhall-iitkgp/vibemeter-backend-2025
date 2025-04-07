from typing import List

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Associate the websocket with the user_id."""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a user."""
        self.active_connections.pop(user_id, None)

    async def notify_meeting_update(self, message: str, user_id: str):
        """Send a personal message to a specific user."""
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json({"event": "meeting_update", "message": message})

    async def send_message(self, message: str, user_id: str):
        """Send a message to a specific user."""
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json({"event": "ai_message", "message": message})

    async def broadcast(self, message: str):
        """Broadcast a message to all connected users."""
        for websocket in self.active_connections.values():
            await websocket.send_text(message)


# Create an instance of the manager
manager = WebSocketManager()
