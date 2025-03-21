import asyncio
from fastapi import WebSocket, WebSocketDisconnect
import random
from together import Together
client = Together()

async def handle_websocket(websocket: WebSocket):
    await websocket.accept()

    # Flag to control response streaming
    stop_streaming = False
    
    try:
        while True:
            # Wait for the message from client
            data = await websocket.receive_json()
            # Check if the client wants to stop the response
            if data['type'] == "stop":
                stop_streaming = True 
                await websocket.send_json({"type": "info", "content": {"message": "Response stopped"}})
                continue

            elif data['type'] == "user_message":
                # Reset the flag for new messages
                stop_streaming = False
                
                # Get streaming responses from the bot
                await websocket.send_json({"type": "thinking", "content": {"message": "The bot is thinking..."}})
                
                stream = client.chat.completions.create(
                    model="meta-llama/Llama-3-8b-chat-hf",
                    messages=data['context'],
                    stream=True,
                    max_tokens=1000,
                )

                await websocket.send_json({"type": "start", "content": {"message": "start"}})

                for chunk in stream:
                    if stop_streaming:
                        break
                    
                    await websocket.send_json({"type": "data", "content": {"message": chunk.choices[0].delta.content or ""}})
                    
                    # Check for any new messages that might be "stop"
                    try:
                        # Use receive_json with a very short timeout to check for new messages
                        message = await asyncio.wait_for(websocket.receive_json(), timeout=0.001)
                        if message['type'] == "stop":
                            stop_streaming = True
                            await websocket.send_json({"type": "info", "content": {"message": "Response stopped"}})
                            break
                    except asyncio.TimeoutError:
                        # No message received within timeout, continue streaming
                        pass
                
                # Only send completion message if we weren't stopped
                if not stop_streaming:
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