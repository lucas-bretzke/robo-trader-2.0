import logging
from fastapi import FastAPI
import atexit
import time

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Initialize connector (assuming it's defined elsewhere)
connector = None  # Replace with actual connector initialization

def run_trading_loop():
    global connector
    running = True  # Replace with actual condition to control the loop
    try:
        while running:
            try:
                # Check if connection is still active
                if not connector.api.check_connect():
                    logger.warning("Connection lost, attempting to reconnect...")
                    connector.connect()
                    if not connector.api.check_connect():
                        logger.error("Failed to reconnect, waiting before retry...")
                        time.sleep(30)  # Wait before retry
                        continue
                        
                # Trading logic goes here
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                # Don't exit the loop on error, just log and continue
                time.sleep(5)  # Wait a bit before continuing
                
    except KeyboardInterrupt:
        logger.info("Trading interrupted by user")
    finally:
        # Ensure proper disconnection
        if connector:
            logger.info("Disconnecting from IQ Option")
            connector.disconnect()

def main():
    # Application initialization and FastAPI setup
    global connector
    try:
        # Example connector initialization
        connector = Connector()  # Replace with actual connector class
        
        # Ensure we stop connection monitoring before exiting
        atexit.register(lambda: connector.disconnect())
        
        # Start your FastAPI app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        if 'connector' in locals():
            connector.disconnect()

if __name__ == "__main__":
    main()