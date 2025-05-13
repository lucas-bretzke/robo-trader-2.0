import logging
from iqoptionapi.stable_api import IQ_Option
import time
import threading

logger = logging.getLogger('robo-trader.connector')

class IQOptionConnector:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.api = IQ_Option(email, password)
        self.is_connected = False
        self._connection_monitor_thread = None
        self._stop_monitor = False

    def connect(self):
        try:
            logger.info("Connecting to IQ Option...")
            status, reason = self.api.connect()
            
            if status:
                self.is_connected = True
                logger.info("Connected successfully!")
                self.api.change_balance('PRACTICE')
                balance = self.api.get_balance()
                logger.info(f"Selected PRACTICE account. Balance: {balance}")
                
                # Start connection monitoring
                self._start_connection_monitor()
                
                return True
            else:
                logger.error(f"Connection failed: {reason}")
                return False
        except Exception as e:
            logger.error(f"Error during connection: {str(e)}")
            return False
    
    def _start_connection_monitor(self):
        """Start a thread to monitor the connection status"""
        if self._connection_monitor_thread is None or not self._connection_monitor_thread.is_alive():
            self._stop_monitor = False
            self._connection_monitor_thread = threading.Thread(target=self._monitor_connection)
            self._connection_monitor_thread.daemon = True
            self._connection_monitor_thread.start()
            logger.info("Connection monitoring started")
    
    def _monitor_connection(self):
        """Monitor the connection and reconnect if needed"""
        check_interval = 30  # seconds
        while not self._stop_monitor:
            if self.is_connected and not self.api.check_connect():
                logger.warning("Connection lost! Attempting to reconnect...")
                self._reconnect()
            time.sleep(check_interval)
    
    def _reconnect(self, max_attempts=5):
        """Attempt to reconnect to IQ Option"""
        self.is_connected = False
        attempt = 0
        
        while attempt < max_attempts and not self.is_connected:
            attempt += 1
            logger.info(f"Reconnection attempt {attempt}/{max_attempts}...")
            
            try:
                status, reason = self.api.connect()
                if status:
                    self.is_connected = True
                    logger.info("Reconnected successfully!")
                    self.api.change_balance('PRACTICE')
                    return True
                else:
                    logger.error(f"Reconnection failed: {reason}")
                    time.sleep(5)  # Wait before retrying
            except Exception as e:
                logger.error(f"Error during reconnection: {str(e)}")
                time.sleep(5)  # Wait before retrying
        
        if not self.is_connected:
            logger.error("Failed to reconnect after multiple attempts")
            return False
    
    def disconnect(self):
        """Properly disconnect and stop connection monitoring"""
        self._stop_monitor = True
        if self._connection_monitor_thread and self._connection_monitor_thread.is_alive():
            self._connection_monitor_thread.join(timeout=1.0)
        self.is_connected = False
        logger.info("Disconnected from IQ Option")