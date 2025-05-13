import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger("robo-trader.strategy")

class StochasticStrategy:
    """
    Trading strategy using Stochastic Oscillator and Simple Moving Average (SMA).
    
    Entry conditions:
    - Stochastic overbought (K > upper_threshold) -> PUT signal
    - Stochastic oversold (K < lower_threshold) -> CALL signal
    - Signal is confirmed only if SMA trend agrees with the direction
    """
    
    def __init__(self, k_period: int = 14, d_period: int = 3, slowing: int = 3, 
                upper_threshold: int = 90, lower_threshold: int = 10, sma_period: int = 20):
        """
        Initialize the strategy with parameters.
        
        Args:
            k_period: %K line period
            d_period: %D line period
            slowing: Smoothing factor
            upper_threshold: Overbought threshold (typically 80-90)
            lower_threshold: Oversold threshold (typically 10-20)
            sma_period: Simple Moving Average period
        """
        self.k_period = k_period
        self.d_period = d_period
        self.slowing = slowing
        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold
        self.sma_period = sma_period
        
        logger.info(f"Stochastic strategy initialized with parameters: "
                   f"K={k_period}, D={d_period}, Slowing={slowing}, "
                   f"Upper={upper_threshold}, Lower={lower_threshold}, SMA={sma_period}")
    
    def calculate_stochastic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Stochastic Oscillator values"""
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Calculate %K
        df['highest_high'] = df['high'].rolling(window=self.k_period).max()
        df['lowest_low'] = df['low'].rolling(window=self.k_period).min()
        df['%K'] = 100 * ((df['close'] - df['lowest_low']) / 
                          (df['highest_high'] - df['lowest_low']))
        
        # Apply slowing if specified
        if self.slowing > 1:
            df['%K'] = df['%K'].rolling(window=self.slowing).mean()
        
        # Calculate %D (signal line)
        df['%D'] = df['%K'].rolling(window=self.d_period).mean()
        
        return df
    
    def calculate_sma(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Simple Moving Average"""
        df = df.copy()
        df['SMA'] = df['close'].rolling(window=self.sma_period).mean()
        return df
    
    def determine_trend(self, df: pd.DataFrame) -> str:
        """Determine trend direction based on price relative to SMA"""
        # Get the last two candles
        last_candles = df.iloc[-3:].copy()
        
        # If price is above SMA, trend is up
        if last_candles['close'].iloc[-1] > last_candles['SMA'].iloc[-1]:
            return "up"
        else:
            return "down"
    
    def analyze(self, df: pd.DataFrame) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Analyze price data to generate trading signals.
        
        Args:
            df: DataFrame with OHLCV candlestick data
        
        Returns:
            Tuple with (signal_generated, signal_direction, indicator_values)
        """
        try:
            # Ensure we have the required columns
            required_cols = ['open', 'high', 'low', 'close']
            for col in required_cols:
                if col not in df.columns:
                    logger.error(f"Required column '{col}' missing from dataframe")
                    return False, "", {}
            
            # Calculate indicators
            df = self.calculate_stochastic(df)
            df = self.calculate_sma(df)
            
            # Get the last values
            last_k = df['%K'].iloc[-1]
            last_d = df['%D'].iloc[-1]
            prev_k = df['%K'].iloc[-2]
            trend = self.determine_trend(df)
            
            # Log the indicator values
            logger.debug(f"Stochastic %K: {last_k:.2f}, %D: {last_d:.2f}, Trend: {trend}")
            
            # Store indicator values for UI display
            indicator_values = {
                "stochastic_k": last_k,
                "stochastic_d": last_d,
                "sma": df['SMA'].iloc[-1],
                "trend": trend,
                "price": df['close'].iloc[-1]
            }
            
            # Generate signals based on conditions
            signal = False
            direction = ""
            
            # Oversold condition (potential CALL)
            if last_k < self.lower_threshold and prev_k < self.lower_threshold and last_k > prev_k:
                if trend == "up":  # Confirm with trend
                    signal = True
                    direction = "call"
                    logger.info(f"CALL signal generated: Stochastic oversold (%K={last_k:.2f}) with uptrend")
            
            # Overbought condition (potential PUT)
            elif last_k > self.upper_threshold and prev_k > self.upper_threshold and last_k < prev_k:
                if trend == "down":  # Confirm with trend
                    signal = True
                    direction = "put"
                    logger.info(f"PUT signal generated: Stochastic overbought (%K={last_k:.2f}) with downtrend")
            
            return signal, direction, indicator_values
            
        except Exception as e:
            logger.error(f"Error in strategy analysis: {str(e)}")
            return False, "", {}
