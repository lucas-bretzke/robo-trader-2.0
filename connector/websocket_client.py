import logging
import websocket
import time
import threading

class WebSocketClient:
    def __init__(self, url, on_message=None, on_error=None, on_close=None, on_open=None):
        self.url = url
        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.on_open = on_open
        self.ws = None
        self.is_connected = False
        self.logger = logging.getLogger("robo-trader.websocket")
        self.keep_alive_interval = 30  # seconds
        self.reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        self._ping_thread = None
        self._running = False

    def connect(self):
        def on_message(ws, message):
            if self.on_message:
                self.on_message(message)

        def on_error(ws, error):
            self.is_connected = False
            if self.on_error:
                self.on_error(error)

        def on_close(ws, close_status_code, close_msg):
            self.is_connected = False
            if self.on_close:
                self.on_close(close_status_code, close_msg)

        def on_open(ws):
            self.is_connected = True
            if self.on_open:
                self.on_open()

        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )

        self._running = True
        self._start_ping_thread()

        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.daemon = True
        self.thread.start()

    def _start_ping_thread(self):
        """Start a thread to send ping messages periodically"""
        if self._ping_thread is not None and self._ping_thread.is_alive():
            return
            
        self._ping_thread = threading.Thread(target=self._ping_task)
        self._ping_thread.daemon = True
        self._ping_thread.start()
        
    def _ping_task(self):
        """Send ping messages to keep the connection alive"""
        while self._running and self.is_connected:
            try:
                if self.ws and self.ws.sock:
                    self.ws.ping()
                    self.logger.debug("Ping sent to keep connection alive")
            except Exception as e:
                self.logger.warning(f"Error sending ping: {e}")
                if not self.is_connected:
                    self._attempt_reconnect()
                    
            time.sleep(self.keep_alive_interval)
    
    def _attempt_reconnect(self):
        """Attempt to reconnect if connection was lost"""
        for attempt in range(self.reconnect_attempts):
            self.logger.info(f"Attempting to reconnect (attempt {attempt+1}/{self.reconnect_attempts})...")
            try:
                self.ws.close()
                self.connect()
                if self.is_connected:
                    self.logger.info("Reconnection successful")
                    return True
            except Exception as e:
                self.logger.error(f"Reconnection attempt failed: {e}")
                
            time.sleep(self.reconnect_delay)
            
        self.logger.error(f"Failed to reconnect after {self.reconnect_attempts} attempts")
        return False
        
    def close(self):
        """Close the websocket connection"""
        self._running = False
        if self._ping_thread and self._ping_thread.is_alive():
            self._ping_thread.join(timeout=1.0)
        if self.ws:
            self.ws.close()
        self.is_connected = False