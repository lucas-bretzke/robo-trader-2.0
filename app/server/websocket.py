import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# Verifique se há um mecanismo de keep-alive
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Adicione um log para indicar o início da conexão
        logging.info("WebSocket connection established")
        
        while True:
            # Aguarde dados do cliente com um timeout
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Processe os dados recebidos
                # ...
                
                # Responda ao cliente para manter a conexão viva
                await websocket.send_text(json.dumps({"status": "ok"}))
            except asyncio.TimeoutError:
                # Envie uma mensagem de ping para manter a conexão ativa
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        logging.info("WebSocket connection closed by client")
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
    finally:
        # Log mais detalhado sobre o fechamento da conexão
        logging.info("WebSocket connection closed with details")