import time
import threading
import logging
from typing import Callable

logger = logging.getLogger('robo-trader.connection_manager')

class ConnectionManager:
    """
    Manages the connection to IQ Option, handling reconnection and keep-alive.
    """
    
    def __init__(self, connector, reconnect_interval=30, max_retries=5):
        """
        Initialize the connection manager.
        
        Args:
            connector: The IQ Option connector instance
            reconnect_interval: Seconds to wait between reconnection attempts
            max_retries: Maximum number of reconnection attempts before giving up
        """
        self.connector = connector
        self.reconnect_interval = reconnect_interval
        self.max_retries = max_retries
        self._stop_event = threading.Event()
        self._connection_thread = None
        self._heartbeat_thread = None
        self._last_heartbeat = time.time()
        
    def start_monitoring(self):
        """Start monitoring the connection."""
        if self._connection_thread is not None and self._connection_thread.is_alive():
            logger.warning("Connection monitoring already active")
            return
            
        self._stop_event.clear()
        self._connection_thread = threading.Thread(
            target=self._monitor_connection,
            daemon=True
        )
        self._connection_thread.start()
        
        # Start heartbeat thread
        self._heartbeat_thread = threading.Thread(
            target=self._send_heartbeats,
            daemon=True
        )
        self._heartbeat_thread.start()
        
        logger.info("Connection monitoring started")
        
    def stop_monitoring(self):
        """Stop monitoring the connection."""
        self._stop_event.set()
        if self._connection_thread:
            self._connection_thread.join(timeout=2.0)
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2.0)
        logger.info("Connection monitoring stopped")
        
    def _monitor_connection(self):
        """Monitor the connection status and reconnect if needed."""
        while not self._stop_event.is_set():
            if not self.connector.check_connect():
                logger.warning("Connection lost, attempting to reconnect...")
                self._reconnect()
            time.sleep(10)  # Check connection every 10 seconds
            
    def _reconnect(self):
        """Attempt to reconnect to IQ Option."""
        retries = 0
        while not self._stop_event.is_set() and retries < self.max_retries:
            try:
                logger.info(f"Reconnection attempt {retries + 1}/{self.max_retries}")
                success = self.connector.connect()
                
                if success:
                    logger.info("Reconnected successfully!")
                    return True
                    
            except Exception as e:
                logger.error(f"Error during reconnection: {e}")
                
            retries += 1
            time.sleep(self.reconnect_interval)
            
        if retries >= self.max_retries:
            logger.error("Max reconnection attempts reached. Could not reconnect.")
        return False
        
    def _send_heartbeats(self):
        """Send periodic heartbeats to keep the connection alive."""
        while not self._stop_event.is_set():
            try:
                if self.connector.check_connect():
                    # The specific heartbeat method will depend on your IQ Option API
                    # Here we're using a ping method, adjust as needed
                    self.connector.api.ping()
                    self._last_heartbeat = time.time()
                    logger.debug("Heartbeat sent successfully")
            except Exception as e:
                logger.warning(f"Failed to send heartbeat: {e}")
                
            time.sleep(30)  # Send heartbeat every 30 seconds
