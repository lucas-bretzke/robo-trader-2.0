from iqoptionapi.stable_api import IQ_Option
import time
import logging
import pandas as pd
from datetime import datetime, timedelta
import json

logger = logging.getLogger("robo-trader.connector")

class IQOptionConnector:
    def __init__(self, email, password):
        """Initialize the IQ Option connector"""
        self.email = email
        self.password = password
        self.api = IQ_Option(email, password)
        self.account_type = "PRACTICE"  # Default to practice account
        self.last_error = None
        
    def connect(self):
        """Connect to IQ Option platform"""
        logger.info("Connecting to IQ Option...")
        
        try:
            check, reason = self.api.connect()
            
            if check:
                logger.info("Connected successfully!")
                return True
            else:
                # Parse the error message
                error_msg = "Unknown connection error"
                
                if isinstance(reason, str):
                    try:
                        # Try to parse as JSON
                        reason_json = json.loads(reason)
                        if "message" in reason_json:
                            error_msg = reason_json["message"]
                        elif "error" in reason_json:
                            error_msg = reason_json["error"]
                    except json.JSONDecodeError:
                        # If not JSON, use as is
                        error_msg = reason
                        
                        # Check for common error patterns
                        if "invalid_credentials" in reason:
                            error_msg = "You entered the wrong credentials. Please ensure that your login/password is correct."
                elif reason is not None:
                    error_msg = str(reason)
                
                logger.error(f"Connection error: {error_msg}")
                self.last_error = error_msg
                return False
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection error: {error_msg}")
            self.last_error = error_msg
            return False
    
    def get_last_error(self):
        """Return the last error message"""
        return self.last_error or "Unknown error"
            
    def select_account(self, account_type):
        """Select account type (PRACTICE or REAL)"""
        if account_type.upper() in ["PRACTICE", "REAL"]:
            self.account_type = account_type.upper()
            self.api.change_balance(self.account_type)
            balance = self.api.get_balance()
            logger.info(f"Selected {self.account_type} account. Balance: {balance}")
            return True
        else:
            logger.error(f"Invalid account type: {account_type}")
            return False
            
    def get_balance(self):
        """Get current account balance"""
        return self.api.get_balance()
        
    def check_asset_availability(self, asset, option_type):
        """Check if asset is available for trading"""
        all_assets = self.api.get_all_open_time()
        
        if option_type == "digital":
            if asset in all_assets['digital']:
                return all_assets['digital'][asset]['open']
            else:
                return False
        elif option_type == "binary":
            if asset in all_assets['turbo'] or asset in all_assets['binary']:
                return (all_assets['turbo'].get(asset, {}).get('open', False) or 
                        all_assets['binary'].get(asset, {}).get('open', False))
            else:
                return False
        else:
            logger.error(f"Invalid option type: {option_type}")
            return False
            
    def get_available_assets(self, option_type):
        """Get list of available assets for trading"""
        all_assets = self.api.get_all_open_time()
        available_assets = []
        
        if option_type == "digital":
            for asset in all_assets['digital']:
                if all_assets['digital'][asset]['open']:
                    available_assets.append(asset)
        elif option_type == "binary":
            for asset in all_assets['turbo']:
                if all_assets['turbo'][asset]['open']:
                    available_assets.append(asset)
            for asset in all_assets['binary']:
                if all_assets['binary'][asset]['open'] and asset not in available_assets:
                    available_assets.append(asset)
        
        return available_assets
        
    def get_candles(self, asset, timeframe, count):
        """Get historical candles for an asset
        
        Args:
            asset: Asset symbol (e.g., "EURUSD")
            timeframe: Candle timeframe in seconds (e.g., 60 for 1 minute)
            count: Number of candles to retrieve
            
        Returns:
            List of candle dictionaries with open, close, high, low values
        """
        try:
            logger.debug(f"Getting {count} candles for {asset} with timeframe {timeframe}s")
            
            # Get candles from IQ Option API
            candles = self.api.get_candles(asset, timeframe, count, time.time())
            
            if not candles or len(candles) == 0:
                logger.warning(f"No candles returned for {asset}")
                return []
                
            # Process candles into a standard format
            processed_candles = []
            for candle in candles:
                processed_candles.append({
                    'open': candle['open'],
                    'high': candle['max'],
                    'low': candle['min'],
                    'close': candle['close'],
                    'volume': candle['volume'],
                    'timestamp': candle['from']
                })
                
            return processed_candles
            
        except Exception as e:
            logger.error(f"Error retrieving candles for {asset}: {str(e)}")
            return []
            
    def execute_trade(self, asset, amount, direction, expiration, option_type="digital"):
        """Execute a trade on IQ Option
        
        Args:
            asset: Asset to trade
            amount: Trade amount
            direction: 'call' or 'put'
            expiration: Expiration time in minutes
            option_type: 'digital' or 'binary'
            
        Returns:
            Dictionary with trade result information
        """
        try:
            # Validate inputs
            direction = direction.lower()
            if direction not in ["call", "put"]:
                logger.error(f"Invalid direction: {direction}")
                return {"success": False, "error": "Invalid direction"}
                
            # Check asset availability
            if not self.check_asset_availability(asset, option_type):
                logger.error(f"Asset {asset} is not available for {option_type} trading")
                return {"success": False, "error": "Asset not available"}
                
            # Execute the trade
            logger.info(f"Executing {direction.upper()} order on {asset} for {amount}$, expiry: {expiration}min ({option_type})")
            
            if option_type == "digital":
                check, order_id = self.api.buy_digital_spot_v2(asset, amount, direction, expiration)
            else:  # binary
                check, order_id = self.api.buy(amount, asset, direction, expiration)
                
            if not check:
                logger.error(f"Failed to execute trade: {order_id}")
                return {
                    "success": False,
                    "error": f"Failed to execute trade: {order_id}",
                    "profit_amount": -amount  # Consider it a loss
                }
                
            logger.info(f"Trade executed with ID: {order_id}")
            
            # Wait for the result
            waiting_time = 0
            max_wait = expiration * 60 + 30  # Wait expiration time plus a buffer
            
            while waiting_time < max_wait:
                if option_type == "digital":
                    status, result = self.api.check_win_digital_v2(order_id)
                else:
                    status, result = self.api.check_win_v4(order_id)
                    
                if status:
                    profit = result
                    outcome = "WIN" if profit > 0 else "LOSS"
                    logger.info(f"Trade result: {outcome}, profit: {profit}")
                    
                    return {
                        "success": True,
                        "order_id": order_id,
                        "profit_amount": profit,
                        "outcome": outcome
                    }
                    
                time.sleep(1)
                waiting_time += 1
                
            logger.warning(f"Timeout waiting for trade result. Order ID: {order_id}")
            return {
                "success": False,
                "error": "Timeout waiting for result",
                "profit_amount": -amount  # Consider it a loss if we can't determine the outcome
            }
                
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return {"success": False, "error": str(e), "profit_amount": -amount}
