from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from app.websocket_manager import WebSocketManager
import logging

app = FastAPI()

# Initialize WebSocket manager
websocket_manager = WebSocketManager(heartbeat_interval=15)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    client_id = client_id or "default"
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            # Process the incoming message
            # For example, you could parse it as JSON and handle different message types
            
            # Echo back to the client (example)
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        logging.info(f"Client {client_id} disconnected")
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
    finally:
        # Always ensure we disconnect properly
        await websocket_manager.disconnect(websocket, client_id)

# Add a shutdown event handler to clean up connections
@app.on_event("shutdown")
async def shutdown_event():
    # Custom cleanup logic, e.g. disconnecting from IQ Option
    logging.info("Shutting down application...")
    # If your connector is in a global variable or accessible here
    # connector.disconnect()