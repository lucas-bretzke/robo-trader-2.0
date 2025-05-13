from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
import json
import logging
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
import pathlib

# Import custom modules
from meuRobo.iq_option_connector import IQOptionConnector
from meuRobo.strategy import StochasticStrategy
from meuRobo.money_management import MoneyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("robo-trader")

# Initialize FastAPI app
app = FastAPI(title="IQ Option Robot")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")

# Global state
iq_connector = None
active_bot = False
operation_history = []
current_config = {
    "assets": [],
    "account_type": "PRACTICE",
    "candle_time": 60,  # seconds
    "expiration_time": 5,  # minutes
    "money_management": "flat",
    "entry_amount": 2,
    "stop_gain": 50,
    "stop_loss": 30,
}
daily_result = {
    "total_operations": 0,
    "wins": 0,
    "losses": 0,
    "win_rate": 0,
    "profit_loss": 0,
    "max_profit": 0,
    "max_loss": 0,
    "max_amount": 0,
    "min_amount": float('inf'),
    "current_balance": 0,
    "is_running": False
}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
            
    async def broadcast_json(self, data: Dict):
        for connection in self.active_connections:
            await connection.send_json(data)

manager = ConnectionManager()

# Data models
class LoginRequest(BaseModel):
    account_type: str
    email: str
    password: str

class ConfigRequest(BaseModel):
    assets: List[str]
    candle_time: int
    expiration_time: int
    money_management: str
    entry_amount: float
    stop_gain: float
    stop_loss: float

class TestEntryRequest(BaseModel):
    direction: Optional[str] = None  # When null, randomly choose

# Root route to serve the HTML file
@app.get("/", response_class=HTMLResponse)
async def get_index():
    return FileResponse('index.html')

# API Routes
@app.post("/api/login")
async def login(req: LoginRequest):
    global iq_connector, daily_result
    
    try:
        # Use credentials from request instead of prompting
        email = req.email
        password = req.password
        
        if not email or not password:
            return JSONResponse(status_code=400, content={"message": "Email and password are required"})
        
        # Initialize connector
        iq_connector = IQOptionConnector(email, password)
        connected = iq_connector.connect()
        
        if not connected:
            error_message = iq_connector.get_last_error()
            logger.error(f"Login failed: {error_message}")
            return JSONResponse(status_code=401, content={"message": error_message})
        
        # Set account type
        iq_connector.select_account(req.account_type)
        current_config["account_type"] = req.account_type
        
        # Get initial balance
        balance = iq_connector.get_balance()
        daily_result["current_balance"] = balance
        
        return {"message": "Login successful", "balance": balance}
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JSONResponse(status_code=500, content={"message": f"Error: {str(e)}"})

@app.post("/api/config")
async def set_config(config: ConfigRequest):
    global current_config
    
    if not iq_connector:
        return JSONResponse(status_code=401, content={"message": "Not logged in"})
    
    current_config.update({
        "assets": config.assets,
        "candle_time": config.candle_time,
        "expiration_time": config.expiration_time,
        "money_management": config.money_management,
        "entry_amount": config.entry_amount,
        "stop_gain": config.stop_gain,
        "stop_loss": config.stop_loss
    })
    
    return {"message": "Configuration updated"}

@app.get("/api/assets")
async def get_assets():
    if not iq_connector:
        return JSONResponse(status_code=401, content={"message": "Not logged in"})
    
    digital_assets = iq_connector.get_available_assets("digital")
    binary_assets = iq_connector.get_available_assets("binary")
    
    return {
        "digital": digital_assets,
        "binary": binary_assets
    }

@app.post("/api/start")
async def start_bot():
    global active_bot
    
    if not iq_connector:
        return JSONResponse(status_code=401, content={"message": "Not logged in"})
    
    if not current_config["assets"]:
        return JSONResponse(status_code=400, content={"message": "No assets selected"})
    
    active_bot = True
    daily_result["is_running"] = True
    
    # Start the trading loop in a background task
    asyncio.create_task(trading_loop())
    
    return {"message": "Bot started"}

@app.post("/api/stop")
async def stop_bot():
    global active_bot
    
    active_bot = False
    daily_result["is_running"] = False
    
    return {"message": "Bot stopped"}

@app.post("/api/test-entry")
async def test_entry(req: TestEntryRequest):
    if not iq_connector:
        return JSONResponse(status_code=401, content={"message": "Not logged in"})
    
    try:
        # Get available assets
        available_assets = iq_connector.get_available_assets("digital")
        
        if not available_assets:
            return JSONResponse(status_code=400, content={"message": "No assets available"})
        
        # Pick random asset
        asset = random.choice(available_assets)
        
        # Determine direction (random if not specified)
        direction = req.direction
        if not direction:
            direction = random.choice(["call", "put"])
        
        # Execute trade with fixed amount ($2)
        result = await execute_trade(asset, 2, direction, current_config["expiration_time"])
        
        return {
            "message": "Test entry executed",
            "asset": asset,
            "direction": direction,
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Test entry error: {str(e)}")
        return JSONResponse(status_code=500, content={"message": f"Error: {str(e)}"})

@app.get("/api/history")
async def get_history():
    return {"history": operation_history}

@app.post("/api/clear-history")
async def clear_history():
    global operation_history
    operation_history = []
    return {"message": "History cleared"}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Just keep connection alive
            await websocket.receive_text()
            # Send current state
            await websocket.send_json({
                "daily_result": daily_result,
                "is_running": active_bot
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Trading logic functions
async def trading_loop():
    logger.info("Starting trading loop")
    global active_bot
    
    strategy = StochasticStrategy(k_period=14, d_period=3, slowing=3, 
                                 upper_threshold=90, lower_threshold=10, 
                                 sma_period=20)
    
    money_manager = MoneyManager(
        strategy=current_config["money_management"],
        base_amount=current_config["entry_amount"],
        stop_gain=current_config["stop_gain"],
        stop_loss=current_config["stop_loss"]
    )
    
    while active_bot:
        try:
            # Check if stop gain or stop loss was reached
            if (daily_result["profit_loss"] >= current_config["stop_gain"] or 
                daily_result["profit_loss"] <= -current_config["stop_loss"]):
                logger.info(f"Stop condition reached: Profit/Loss = {daily_result['profit_loss']}")
                await manager.broadcast_json({
                    "type": "alert",
                    "message": f"Bot stopped: {'Stop gain' if daily_result['profit_loss'] >= 0 else 'Stop loss'} reached"
                })
                active_bot = False
                daily_result["is_running"] = False
                break
            
            # Update balance
            balance = iq_connector.get_balance()
            daily_result["current_balance"] = balance
            
            # Process each selected asset
            for asset in current_config["assets"]:
                try:
                    if not iq_connector.check_asset_availability(asset, "digital"):
                        logger.info(f"Asset {asset} not available, skipping")
                        continue
                    
                    # Get candles data
                    candles = iq_connector.get_candles(asset, current_config["candle_time"], 100)
                    
                    if not candles or len(candles) < 50:  # Need enough data for indicators
                        logger.info(f"Not enough candle data for {asset}, skipping")
                        continue
                    
                    # Analyze with strategy
                    df = pd.DataFrame(candles)
                    signal, direction, indicator_values = strategy.analyze(df)
                    
                    # Send analysis update to frontend
                    await manager.broadcast_json({
                        "type": "analysis",
                        "asset": asset,
                        "time": datetime.now().isoformat(),
                        "indicators": indicator_values,
                        "signal": signal,
                        "direction": direction
                    })
                    
                    # If we have a signal, execute trade
                    if signal:
                        logger.info(f"Signal detected for {asset}: {direction}")
                        
                        # Calculate entry amount using money management
                        entry_amount = money_manager.calculate_entry_amount(
                            operation_history, daily_result["profit_loss"])
                        
                        # Execute trade
                        result = await execute_trade(asset, entry_amount, direction, 
                                                   current_config["expiration_time"])
                        
                        # Update statistics
                        update_stats(asset, entry_amount, direction, result)
                        
                        # Broadcast update
                        await manager.broadcast_json({
                            "type": "operation",
                            "data": operation_history[-1] if operation_history else {},
                            "daily_result": daily_result
                        })
                
                except Exception as e:
                    logger.error(f"Error processing asset {asset}: {str(e)}")
            
            # Broadcast current state
            await manager.broadcast_json({
                "type": "update",
                "daily_result": daily_result,
                "is_running": active_bot
            })
            
            # Sleep before next cycle
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in trading loop: {str(e)}")
            await asyncio.sleep(5)  # Wait a bit before retrying

async def execute_trade(asset, amount, direction, expiration):
    logger.info(f"Executing trade: {asset} {direction} {amount}$ exp:{expiration}min")
    
    # Execute the trade
    result = iq_connector.execute_trade(asset, amount, direction, expiration, "digital")
    
    # Log trade result
    log_entry = {
        "time": datetime.now().isoformat(),
        "asset": asset,
        "direction": direction,
        "amount": amount,
        "expiration": expiration,
        "result": result
    }
    
    logger.info(f"Trade result: {log_entry}")
    
    return result

def update_stats(asset, amount, direction, result):
    global operation_history, daily_result
    
    # Create operation record
    operation = {
        "id": len(operation_history) + 1,
        "time": datetime.now().isoformat(),
        "asset": asset,
        "direction": direction,
        "amount": amount,
        "result": result["profit_amount"],
        "status": "win" if result["profit_amount"] > 0 else "loss"
    }
    
    # Add to history
    operation_history.append(operation)
    
    # Update daily stats
    daily_result["total_operations"] += 1
    profit = result["profit_amount"]
    
    if profit > 0:
        daily_result["wins"] += 1
        daily_result["max_profit"] = max(daily_result["max_profit"], profit)
    else:
        daily_result["losses"] += 1
        daily_result["max_loss"] = min(daily_result["max_loss"], profit)
    
    daily_result["win_rate"] = (daily_result["wins"] / daily_result["total_operations"]) * 100
    daily_result["profit_loss"] += profit
    daily_result["max_amount"] = max(daily_result["max_amount"], amount)
    daily_result["min_amount"] = min(daily_result["min_amount"], amount)

# Run the FastAPI app with Uvicorn when this script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
