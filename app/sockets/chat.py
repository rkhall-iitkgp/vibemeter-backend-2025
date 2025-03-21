import asyncio
from fastapi import WebSocket, WebSocketDisconnect

async def handle_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        # Wait for the first message from client
        data = await websocket.receive_text()
        
        # Get streaming responses from the bot
        await websocket.send_json({"type": "thinking", "content": {"message": "The bot is thinking..."}})
        await asyncio.sleep(4)

        await websocket.send_json({"type": "start", "content": {"message": "start"}})
        await asyncio.sleep(0.2)
        
        responses = ["apple "] * 50
        
        # Stream each response with a small delay
        for response in responses:
            await websocket.send_json({"type": "data", "content": {"message": response}})
            # Add a small delay to demonstrate streaming behavior
            await asyncio.sleep(0.02)
        
        # Final completion message
        await websocket.send_json({"type": "end", "content": {"message": "Goodbye"}})
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error in WebSocket: {str(e)}")
    finally:
        try:
            await websocket.close()
        except:
            pass  # Socket might already be closed