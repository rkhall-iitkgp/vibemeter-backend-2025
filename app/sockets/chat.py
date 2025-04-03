from fastapi import WebSocket


async def handle_websocket(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # Process the message (e.g., run ML analysis on input text)
        response = f"Message received: {data}"
        await websocket.send_text(response)
