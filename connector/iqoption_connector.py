import logging
import time
import threading

class IQOptionConnector:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.api = None  # Replace with actual API initialization
        self.logger = logging.getLogger("robo-trader.connector")
        self.keep_alive_thread = None
        self.is_running = False
        self.ping_interval = 30  # Send ping every 30 seconds

    def connect(self):
        try:
            self.api.connect()
            self.is_running = True
            self.start_keep_alive()
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def start_keep_alive(self):
        """Start a thread to keep the connection alive"""
        if self.keep_alive_thread is not None and self.keep_alive_thread.is_alive():
            return

        self.keep_alive_thread = threading.Thread(target=self._keep_alive_task)
        self.keep_alive_thread.daemon = True
        self.keep_alive_thread.start()
        self.logger.info("Keep-alive mechanism started")

    def _keep_alive_task(self):
        """Task to periodically ping the server and check connection status"""
        while self.is_running:
            try:
                if not self.api.check_connect():
                    self.logger.warning("Connection lost, attempting to reconnect...")
                    self.api.reconnect()
                    if self.api.check_connect():
                        self.logger.info("Reconnection successful")
                    else:
                        self.logger.error("Reconnection failed")
                else:
                    self.api.ping()
            except Exception as e:
                self.logger.error(f"Error in keep-alive task: {e}")
            time.sleep(self.ping_interval)

    def disconnect(self):
        """Disconnect and stop keep-alive mechanism"""
        self.is_running = False
        if self.keep_alive_thread and self.keep_alive_thread.is_alive():
            self.keep_alive_thread.join(timeout=1.0)
        self.api.disconnect()