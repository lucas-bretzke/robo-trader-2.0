import numpy as np
import talib
import logging

logger = logging.getLogger(__name__)

class StochasticStrategy:
    def __init__(self):
        self.oversold_level = 10  # Level for CALL signals
        self.overbought_level = 90  # Level for PUT signals
        self.sma_period = 20  # Period for SMA trend analysis
    
    def calculate_stochastic(self, candles, k_period=14, d_period=3, slowing=3):
        """Calculate Stochastic Oscillator"""
        try:
            # Extract high, low, close from candles
            high = np.array([candle['max'] for candle in candles])
            low = np.array([candle['min'] for candle in candles])
            close = np.array([candle['close'] for candle in candles])
            
            # Calculate Stochastic Oscillator
            k, d = talib.STOCH(high, low, close, 
                              fastk_period=k_period, 
                              slowk_period=slowing, 
                              slowk_matype=0, 
                              slowd_period=d_period, 
                              slowd_matype=0)
            
            return k, d
        except Exception as e:
            logger.exception("Error calculating stochastic")
            return None, None
    
    def calculate_sma(self, candles, period=20):
        """Calculate Simple Moving Average"""
        try:
            # Extract close prices
            close = np.array([candle['close'] for candle in candles])
            
            # Calculate SMA
            sma = talib.SMA(close, timeperiod=period)
            
            return sma
        except Exception as e:
            logger.exception("Error calculating SMA")
            return None
    
    def determine_trend(self, candles):
        """Determine trend using SMA"""
        try:
            # Get SMA
            sma = self.calculate_sma(candles, self.sma_period)
            
            if sma is None or len(sma) < 2:
                return None
            
            # Get last valid SMA values
            current_sma = sma[-1]
            previous_sma = sma[-2]
            
            # Get last price
            current_price = candles[-1]['close']
            
            # Determine trend
            if current_sma > previous_sma and current_price > current_sma:
                return "uptrend"
            elif current_sma < previous_sma and current_price < current_sma:
                return "downtrend"
            else:
                return "sideways"
                
        except Exception as e:
            logger.exception("Error determining trend")
            return None
    
    def analyze(self, candles):
        """Analyze candles and determine trading signal"""
        try:
            # Calculate indicators
            k, d = self.calculate_stochastic(candles)
            trend = self.determine_trend(candles)
            
            if k is None or d is None or trend is None:
                return {"signal": None}
            
            # Get last values
            last_k = k[-1]
            last_d = d[-1]
            
            # Default signal
            signal = None
            
            # Stochastic in oversold zone - potential CALL
            if last_k < self.oversold_level and last_d < self.oversold_level:
                # Check trend confirmation
                if trend == "uptrend" or trend == "sideways":
                    signal = "call"
            
            # Stochastic in overbought zone - potential PUT
            elif last_k > self.overbought_level and last_d > self.overbought_level:
                # Check trend confirmation
                if trend == "downtrend" or trend == "sideways":
                    signal = "put"
            
            return {
                "signal": signal,
                "stochastic": {"k": float(last_k), "d": float(last_d)},
                "sma": float(self.calculate_sma(candles)[-1]) if self.calculate_sma(candles) is not None else None,
                "trend": trend
            }
            
        except Exception as e:
            logger.exception("Error analyzing candles")
            return {"signal": None}
