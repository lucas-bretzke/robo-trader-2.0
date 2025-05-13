from iqoptionapi.stable_api import IQ_Option
import time
import random
import logging
import numpy as np
from datetime import datetime, timedelta
from .strategy import StochasticStrategy

logger = logging.getLogger(__name__)

class IQRobot:
    def __init__(self, email, password, account_type="PRACTICE", database=None):
        self.email = email
        self.password = password
        self.account_type = account_type
        self.api = None
        self.connected = False
        self.database = database
        self.config = {
            "candle_time": 60,  # seconds
            "operation_time": 1,  # minutes
            "selected_assets": [],
            "money_management": "fixed",
            "entry_amount": 2.0,
            "martingale_factor": 2.0,
            "stop_loss": 50.0,
            "stop_gain": 100.0,
            "allowed_hours": {"start": "09:00", "end": "18:00"}
        }
        self.strategy = StochasticStrategy()
        self.last_amount = self.config["entry_amount"]
        self.daily_profit = 0.0
        self.daily_loss = 0.0
        self.last_operation_result = None
        
    def connect(self):
        """Connect to IQ Option API"""
        logger.info(f"Connecting to IQ Option with email: {self.email}")
        
        try:
            self.api = IQ_Option(self.email, self.password)
            check, reason = self.api.connect()
            
            if check:
                logger.info("Successfully connected to IQ Option")
                self.api.change_balance(self.account_type)
                self.connected = True
                return True
            else:
                logger.error(f"Connection failed: {reason}")
                return False
        except Exception as e:
            logger.exception("Error connecting to IQ Option API")
            self.connected = False
            return False
    
    def is_connected(self):
        """Check if connected to API"""
        if not self.api:
            return False
        return self.connected and self.api.check_connect()
    
    def get_balance(self):
        """Get account balance"""
        if not self.is_connected():
            raise Exception("Not connected to IQ Option")
        
        return self.api.get_balance()
    
    def get_available_assets(self, asset_type="digital"):
        """Get list of available assets"""
        if not self.is_connected():
            raise Exception("Not connected to IQ Option")
        
        all_assets = self.api.get_all_open_time()
        available_assets = []
        
        if asset_type == "digital":
            for asset in all_assets['digital']:
                if all_assets['digital'][asset]['open']:
                    available_assets.append(asset)
        else:  # Binary options
            for asset in all_assets['turbo']:
                if all_assets['turbo'][asset]['open']:
                    available_assets.append(asset)
            for asset in all_assets['binary']:
                if all_assets['binary'][asset]['open'] and asset not in available_assets:
                    available_assets.append(asset)
        
        return available_assets
    
    def configure(self, config):
        """Configure robot parameters"""
        for key, value in config.items():
            if key in self.config:
                self.config[key] = value
        
        logger.info(f"Robot configured with: {self.config}")
        
        # Reset daily profit/loss when configuration changes
        self.daily_profit = 0.0
        self.daily_loss = 0.0
        self.last_amount = self.config["entry_amount"]
    
    def is_trading_allowed(self):
        """Check if current time is within allowed trading hours"""
        now = datetime.now().time()
        start_time = datetime.strptime(self.config["allowed_hours"]["start"], "%H:%M").time()
        end_time = datetime.strptime(self.config["allowed_hours"]["end"], "%H:%M").time()
        
        return start_time <= now <= end_time
    
    def should_stop(self):
        """Check if stop conditions are met"""
        if self.daily_profit >= self.config["stop_gain"]:
            logger.info(f"Stop gain reached: ${self.daily_profit} >= ${self.config['stop_gain']}")
            return True
        
        if abs(self.daily_loss) >= self.config["stop_loss"]:
            logger.info(f"Stop loss reached: ${abs(self.daily_loss)} >= ${self.config['stop_loss']}")
            return True
        
        return False
    
    def calculate_next_amount(self, last_result):
        """Calculate next entry amount based on money management"""
        if not last_result:
            return self.config["entry_amount"]
        
        amount = self.config["entry_amount"]
        
        if self.config["money_management"] == "martingale":
            if last_result["outcome"].lower() == "loss":
                # Increase amount after loss
                amount = last_result["amount"] * self.config["martingale_factor"]
            else:
                # Reset after win
                amount = self.config["entry_amount"]
                
        elif self.config["money_management"] == "soros":
            if last_result["outcome"].lower() == "win":
                # Use profit for next trade
                amount = last_result["amount"] + last_result["result"]
            else:
                # Reset after loss
                amount = self.config["entry_amount"]
        
        return amount
    
    def get_candles(self, asset, count=30):
        """Get candle data for an asset"""
        if not self.is_connected():
            raise Exception("Not connected to IQ Option")
        
        candles = self.api.get_candles(asset, self.config["candle_time"], count, time.time())
        return candles
    
    def check_asset_availability(self, asset):
        """Check if asset is available for trading"""
        if not self.is_connected():
            raise Exception("Not connected to IQ Option")
        
        all_assets = self.api.get_all_open_time()
        if asset in all_assets['digital']:
            return all_assets['digital'][asset]['open']
        return False
    
    def execute_trade(self, asset, amount, direction):
        """Execute a digital option trade"""
        if not self.is_connected():
            raise Exception("Not connected to IQ Option")
        
        if not self.check_asset_availability(asset):
            logger.warning(f"Asset {asset} is not available for trading")
            return {"error": f"Asset {asset} is not available for trading"}
        
        try:
            expiration = self.config["operation_time"]
            logger.info(f"Executing {direction} on {asset} for ${amount}, expiration: {expiration} minutes")
            
            # Execute trade
            check, id = self.api.buy_digital_spot_v2(asset, amount, direction, expiration)
            
            if not check:
                logger.error(f"Trade execution failed: {id}")
                return {"error": f"Trade execution failed: {id}"}
            
            logger.info(f"Trade executed with ID: {id}")
            
            # Wait for result
            max_waiting_time = expiration * 60 + 10  # Add buffer
            start_time = time.time()
            
            while time.time() - start_time < max_waiting_time:
                time.sleep(1)
                # Check result
                status, result = self.api.check_win_digital_v2(id)
                
                if status:
                    # Record profit/loss
                    if result > 0:
                        self.daily_profit += result
                        outcome = "WIN"
                    else:
                        self.daily_loss += result
                        outcome = "LOSS"
                    
                    # Create operation record
                    operation = {
                        "asset": asset,
                        "direction": direction,
                        "amount": amount,
                        "result": result,
                        "outcome": outcome,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Update last operation
                    self.last_operation_result = operation
                    
                    logger.info(f"Trade result: {outcome}, Profit/Loss: ${result}")
                    return {"operation": operation}
            
            logger.warning(f"Trade result timeout for ID: {id}")
            return {"error": "Trade result timeout"}
            
        except Exception as e:
            logger.exception(f"Error executing trade on {asset}")
            return {"error": str(e)}
    
    def analyze_asset(self, asset):
        """Analyze an asset using the strategy"""
        try:
            # Get candle data
            candles = self.get_candles(asset)
            
            if not candles or len(candles) < 15:
                return None
            
            # Analyze using strategy
            result = self.strategy.analyze(candles)
            
            return {
                "asset": asset,
                "signal": result.get("signal"),
                "stochastic": result.get("stochastic"),
                "sma": result.get("sma"),
                "trend": result.get("trend")
            }
        except Exception as e:
            logger.exception(f"Error analyzing asset {asset}")
            return None
    
    def check_and_trade(self):
        """Check conditions and execute trades if signals are found"""
        # Check if trading is allowed in current hours
        if not self.is_trading_allowed():
            logger.info("Trading not allowed at current time")
            return {"message": "Trading not allowed at current time"}
        
        # Check stop conditions
        if self.should_stop():
            logger.info("Stop conditions reached")
            return {"message": "Stop conditions reached"}
        
        # Update available assets
        available_assets = self.get_available_assets("digital")
        trading_assets = [a for a in self.config["selected_assets"] if a in available_assets]
        
        if not trading_assets:
            logger.warning("No selected assets are available for trading")
            return {"message": "No selected assets available"}
        
        # Calculate next amount
        self.last_amount = self.calculate_next_amount(self.last_operation_result)
        
        # Analyze each asset
        for asset in trading_assets:
            analysis = self.analyze_asset(asset)
            
            if not analysis:
                continue
            
            # If we have a trade signal
            if analysis["signal"]:
                logger.info(f"Trade signal for {asset}: {analysis['signal']}")
                
                # Execute trade
                result = self.execute_trade(asset, self.last_amount, analysis["signal"])
                
                # Log analytics
                logger.info(f"Analysis: Stochastic: {analysis['stochastic']}, SMA Trend: {analysis['trend']}")
                
                return result
        
        return {"message": "No trading signals found"}
    
    def test_entry(self):
        """Execute a test trade with fixed amount"""
        try:
            # Get available assets
            available_assets = self.get_available_assets("digital")
            
            if not available_assets:
                return {"error": "No assets available for testing"}
            
            # Select random asset
            asset = random.choice(available_assets)
            
            # Select random direction
            direction = random.choice(["call", "put"])
            
            # Fixed test amount
            amount = 2.0
            
            logger.info(f"Executing test trade: {direction} on {asset} for ${amount}")
            
            # Execute trade
            return self.execute_trade(asset, amount, direction)
            
        except Exception as e:
            logger.exception("Error executing test trade")
            return {"error": str(e)}
