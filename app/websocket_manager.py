import logging
import asyncio
from fastapi import WebSocket
from typing import Dict, List, Set

logger = logging.getLogger('robo-trader.websocket')

class WebSocketManager:
    def __init__(self, heartbeat_interval=30):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.heartbeat_interval = heartbeat_interval  # seconds
    
    async def connect(self, websocket: WebSocket, client_id: str = "default"):
        await websocket.accept()
        
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        
        self.active_connections[client_id].add(websocket)
        logger.info(f"WebSocket client {client_id} connected")
        
        # Start heartbeat for this connection
        asyncio.create_task(self._heartbeat(websocket, client_id))
    
    async def disconnect(self, websocket: WebSocket, client_id: str = "default"):
        if client_id in self.active_connections:
            try:
                self.active_connections[client_id].remove(websocket)
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]
                logger.info(f"WebSocket client {client_id} disconnected")
            except KeyError:
                pass  # Socket was already removed
    
    async def _heartbeat(self, websocket: WebSocket, client_id: str):
        """Send periodic heartbeats to keep the connection alive"""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Check if client is still in active connections
                if (client_id not in self.active_connections or 
                    websocket not in self.active_connections[client_id]):
                    break
                    
                try:
                    # Send a ping frame to keep the connection alive
                    await websocket.send_text('{"type": "heartbeat"}')
                    logger.debug(f"Heartbeat sent to client {client_id}")
                except Exception as e:
                    logger.warning(f"Failed to send heartbeat to client {client_id}: {str(e)}")
                    await self.disconnect(websocket, client_id)
                    break
        except Exception as e:
            logger.error(f"Heartbeat error for client {client_id}: {str(e)}")
            await self.disconnect(websocket, client_id)
    
    async def broadcast(self, message: dict, client_id: str = None):
        """
        Send a message to clients
        If client_id is provided, only send to that client group
        Otherwise send to all clients
        """
        disconnected = []
        
        if client_id is not None and client_id in self.active_connections:
            connections = list(self.active_connections[client_id])
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append((connection, client_id))
        else:
            for cid, connections in self.active_connections.items():
                for connection in list(connections):
                    try:
                        await connection.send_json(message)
                    except Exception:
                        disconnected.append((connection, cid))
        
        # Clean up any disconnected clients
        for conn, cid in disconnected:
            await self.disconnect(conn, cid)
