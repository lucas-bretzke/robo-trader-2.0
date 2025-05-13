import logging
from iqoptionapi.stable_api import IQ_Option

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class IQOptionConnector:
    def __init__(self, email, password):
        self.api = IQ_Option(email, password)
        self.api.connect()
        self.api.change_balance("PRACTICE")  # Default to practice account

    def is_connected(self):
        return self.api.check_connect()

    def change_account(self, account_type):
        if account_type.lower() == "real":
            self.api.change_balance("REAL")
        elif account_type.lower() == "practice":
            self.api.change_balance("PRACTICE")
        else:
            logger.error("Invalid account type. Use 'real' or 'practice'.")

    def get_balance(self):
        return self.api.get_balance()

    def get_open_assets(self):
        return self.api.get_all_open_time()

    def place_order(self, asset, amount, direction, expiry, order_type="digital"):
        """
        Places an order on IQ Option platform
        
        Args:
            asset (str): Asset name
            amount (float): Order amount
            direction (str): 'call' or 'put'
            expiry (int): Expiration time in minutes
            order_type (str): 'digital' or 'binary'
            
        Returns:
            tuple: (success, order_id or error_message)
        """
        try:
            logger.info(f"Executing {direction.upper()} order on {asset} for {amount}$, expiry: {expiry}min ({order_type})")
            
            # Check if the API is connected
            if not self.api.check_connect():
                logger.error("API not connected")
                return False, "API not connected"
            
            # Check if asset exists and is available
            assets_list = self.api.get_all_open_time()
            
            # For digital options
            if order_type == "digital":
                is_available = False
                for market_type in ["turbo", "binary"]:
                    if asset in assets_list[market_type] and assets_list[market_type][asset]["open"]:
                        is_available = True
                        break
                        
                if not is_available:
                    logger.error(f"Asset {asset} is not available for trading")
                    return False, f"Asset {asset} is not available"
                
                # Get the digital asset ID for the specified expiration
                duration = expiry * 60  # Convert minutes to seconds
                
                # Check if the specified duration is valid for digital options
                valid_durations = [60, 120, 300, 600, 900, 1800, 3600]
                if duration not in valid_durations:
                    logger.error(f"Invalid duration for digital option: {expiry} minutes")
                    return False, f"Invalid duration: {expiry} minutes"
                
                # Place digital option
                action = "call" if direction.lower() == "call" else "put"
                order_id = self.api.buy_digital_spot(asset, amount, action, duration)
                
                # Check if order was placed successfully
                if isinstance(order_id, (int, float)) and order_id > 0:
                    logger.info(f"Digital order placed successfully. ID: {order_id}")
                    return True, order_id
                else:
                    logger.error(f"Failed to place digital order: {order_id}")
                    return False, str(order_id)
                    
            # For binary options
            elif order_type == "binary":
                if asset not in assets_list["turbo"] or not assets_list["turbo"][asset]["open"]:
                    logger.error(f"Asset {asset} is not available for binary trading")
                    return False, f"Asset {asset} is not available"
                
                action = "call" if direction.lower() == "call" else "put"
                order_id = self.api.buy(amount, asset, action, expiry)
                
                # Check if order was placed successfully
                if isinstance(order_id, (int, float)) and order_id > 0:
                    logger.info(f"Binary order placed successfully. ID: {order_id}")
                    return True, order_id
                else:
                    logger.error(f"Failed to place binary order: {order_id}")
                    return False, str(order_id)
            else:
                logger.error(f"Invalid order type: {order_type}")
                return False, f"Invalid order type: {order_type}"
                
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return False, str(e)