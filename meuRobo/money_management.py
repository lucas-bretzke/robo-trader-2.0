import logging
from typing import List, Dict, Any

logger = logging.getLogger("robo-trader.money_management")

class MoneyManager:
    """
    Money management class implementing different strategies:
    - Flat: Always use the same amount
    - Martingale: Double the amount after a loss
    - Soros: Increase amount after a win
    
    Also implements stop gain and stop loss.
    """
    
    def __init__(self, strategy: str = "flat", base_amount: float = 2.0, 
                stop_gain: float = 50.0, stop_loss: float = 30.0):
        """
        Initialize money manager with strategy and parameters
        
        Args:
            strategy: 'flat', 'martingale', or 'soros'
            base_amount: Base entry amount
            stop_gain: Stop gain amount
            stop_loss: Stop loss amount
        """
        self.strategy = strategy.lower()
        self.base_amount = base_amount
        self.stop_gain = stop_gain
        self.stop_loss = stop_loss
        
        # Validate strategy
        if self.strategy not in ["flat", "martingale", "soros"]:
            logger.warning(f"Invalid strategy: {self.strategy}. Using 'flat' as default.")
            self.strategy = "flat"
            
        logger.info(f"Money manager initialized with strategy: {self.strategy}, "
                   f"base amount: {self.base_amount}, stop gain: {self.stop_gain}, "
                   f"stop loss: {self.stop_loss}")
    
    def get_last_operations(self, history: List[Dict[str, Any]], count: int = 3) -> List[Dict[str, Any]]:
        """Get the last N operations from history"""
        return history[-count:] if len(history) >= count else history
    
    def calculate_entry_amount(self, history: List[Dict[str, Any]], current_profit_loss: float) -> float:
        """
        Calculate the next entry amount based on the money management strategy
        
        Args:
            history: List of previous operations
            current_profit_loss: Current profit/loss for the day
            
        Returns:
            Next entry amount
        """
        # Check if stop gain or stop loss was reached
        if current_profit_loss >= self.stop_gain or current_profit_loss <= -self.stop_loss:
            logger.info(f"Stop condition reached. Profit/Loss: {current_profit_loss}")
            return 0.0
            
        # If there's no history or using flat strategy, return base amount
        if not history or self.strategy == "flat":
            return self.base_amount
            
        # Get last operation
        last_op = history[-1]
        last_amount = last_op["amount"]
        last_result = last_op["result"]
        
        if self.strategy == "martingale":
            # If last operation was a loss, double the amount (up to a reasonable limit)
            if last_result < 0:
                new_amount = last_amount * 2
                
                # Cap the maximum amount at 10x the base amount for safety
                max_amount = self.base_amount * 10
                if new_amount > max_amount:
                    logger.warning(f"Martingale amount {new_amount} exceeds safety limit {max_amount}")
                    new_amount = max_amount
                    
                logger.info(f"Martingale: Last trade was a loss. "
                           f"Increasing amount from {last_amount} to {new_amount}")
                return new_amount
            else:
                # If last operation was a win, revert to base amount
                return self.base_amount
                
        elif self.strategy == "soros":
            # If last operation was a win, add the profit to the next trade
            if last_result > 0:
                new_amount = last_amount + last_result
                
                # Cap the maximum amount at 10x the base amount for safety
                max_amount = self.base_amount * 10
                if new_amount > max_amount:
                    logger.warning(f"Soros amount {new_amount} exceeds safety limit {max_amount}")
                    new_amount = max_amount
                    
                logger.info(f"Soros: Last trade was a win. "
                           f"Increasing amount from {last_amount} to {new_amount}")
                return new_amount
            else:
                # If last operation was a loss, revert to base amount
                return self.base_amount
        
        # Default fallback
        return self.base_amount
        
    def should_stop(self, current_profit_loss: float) -> bool:
        """Check if trading should stop based on profit/loss limits"""
        if current_profit_loss >= self.stop_gain:
            logger.info(f"Stop Gain reached: {current_profit_loss} >= {self.stop_gain}")
            return True
        
        if current_profit_loss <= -self.stop_loss:
            logger.info(f"Stop Loss reached: {current_profit_loss} <= -{self.stop_loss}")
            return True
            
        return False
