import logging
from fastapi import FastAPI
import atexit

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Initialize connector (assuming it's defined elsewhere)
connector = None  # Replace with actual connector initialization

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