from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from trading.robot import IQRobot
from trading.strategy import StochasticStrategy
from trading.database import Database

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.FileHandler("robot.log"),
                       logging.StreamHandler()
                   ])

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "success", "message": "Robo Trader API está funcionando!"})

# Global variables
robot = None
robot_thread = None
robot_running = False
robot_status = {
    "status": "inactive",
    "operations_count": 0,
    "wins": 0,
    "losses": 0,
    "profit": 0.0,
    "last_operation": None,
    "errors": []
}

# Database initialization
db = Database()

def create_log_dirs():
    """Ensure log directories exist"""
    Path("logs").mkdir(exist_ok=True)
    Path("logs/operations").mkdir(exist_ok=True)
    Path("logs/errors").mkdir(exist_ok=True)

def robot_task():
    """Main robot task to be run in a separate thread"""
    global robot_running, robot_status
    
    logger.info("Robot thread started")
    
    try:
        while robot_running:
            if robot and robot.is_connected():
                # Update robot status
                robot_status["status"] = "active"
                
                # Perform trading operations
                result = robot.check_and_trade()
                
                if result:
                    operation = result.get('operation')
                    if operation:
                        # Update status with operation result
                        robot_status["operations_count"] += 1
                        robot_status["last_operation"] = operation
                        
                        if operation["outcome"].lower() == "win":
                            robot_status["wins"] += 1
                            robot_status["profit"] += float(operation["result"])
                        elif operation["outcome"].lower() == "loss":
                            robot_status["losses"] += 1
                            robot_status["profit"] += float(operation["result"])
                        
                        # Save operation to database
                        db.save_operation(operation)
                    
                    # Check if any error occurred
                    if "error" in result:
                        robot_status["errors"].append(result["error"])
                        logger.error(f"Trading error: {result['error']}")
                    
                    # Check stop conditions
                    if robot.should_stop():
                        logger.info("Stop conditions reached. Stopping robot.")
                        robot_running = False
                        robot_status["status"] = "inactive"
                        break
                
            # Wait before next check
            time.sleep(5)
    except Exception as e:
        logger.exception("Error in robot thread")
        robot_status["errors"].append(str(e))
        robot_running = False
        robot_status["status"] = "inactive"
    
    logger.info("Robot thread finished")

@app.route('/api/connect', methods=['POST'])
def connect():
    """Connect to IQ Option API"""
    global robot
    
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        account_type = data.get('accountType', 'PRACTICE')
        
        if not email or not password:
            return jsonify({"success": False, "message": "Email and password are required"})
        
        # Create robot instance
        robot = IQRobot(email, password, account_type, db)
        
        # Try to connect
        connected = robot.connect()
        
        if connected:
            balance = robot.get_balance()
            return jsonify({
                "success": True, 
                "message": "Connected successfully",
                "balance": balance,
                "account_type": account_type
            })
        else:
            return jsonify({"success": False, "message": "Failed to connect to IQ Option"})
    except Exception as e:
        logger.exception("Connection error")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/balance', methods=['GET'])
def get_balance():
    """Get account balance"""
    if not robot or not robot.is_connected():
        return jsonify({"success": False, "message": "Not connected to IQ Option"})
    
    try:
        balance = robot.get_balance()
        return jsonify({"success": True, "balance": balance})
    except Exception as e:
        logger.exception("Error getting balance")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/assets', methods=['GET'])
def get_assets():
    """Get available assets"""
    if not robot or not robot.is_connected():
        return jsonify({"success": False, "message": "Not connected to IQ Option"})
    
    try:
        asset_type = request.args.get('type', 'digital')
        assets = robot.get_available_assets(asset_type)
        return jsonify({"success": True, "assets": assets})
    except Exception as e:
        logger.exception("Error getting assets")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/start', methods=['POST'])
def start_robot():
    """Start the trading robot"""
    global robot, robot_thread, robot_running, robot_status
    
    if not robot or not robot.is_connected():
        return jsonify({"success": False, "message": "Not connected to IQ Option"})
    
    if robot_running:
        return jsonify({"success": False, "message": "Robot is already running"})
    
    try:
        data = request.json
        
        # Configure robot
        robot.configure({
            "candle_time": int(data.get('candle_time', 60)),
            "operation_time": int(data.get('operation_time', 1)),
            "selected_assets": data.get('selected_assets', []),
            "money_management": data.get('money_management', 'fixed'),
            "entry_amount": float(data.get('entry_amount', 2)),
            "martingale_factor": float(data.get('martingale_factor', 2.0)),
            "stop_loss": float(data.get('stop_loss', 50)),
            "stop_gain": float(data.get('stop_gain', 100)),
            "allowed_hours": data.get('allowed_hours', {"start": "09:00", "end": "18:00"})
        })
        
        # Reset status
        robot_status = {
            "status": "active",
            "operations_count": 0,
            "wins": 0,
            "losses": 0,
            "profit": 0.0,
            "last_operation": None,
            "errors": []
        }
        
        # Start robot thread
        robot_running = True
        robot_thread = threading.Thread(target=robot_task)
        robot_thread.daemon = True
        robot_thread.start()
        
        return jsonify({"success": True, "message": "Robot started successfully"})
    except Exception as e:
        logger.exception("Error starting robot")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/stop', methods=['POST'])
def stop_robot():
    """Stop the trading robot"""
    global robot_running, robot_status
    
    if not robot_running:
        return jsonify({"success": False, "message": "Robot is not running"})
    
    try:
        robot_running = False
        robot_status["status"] = "inactive"
        
        # Wait for thread to finish
        if robot_thread and robot_thread.is_alive():
            robot_thread.join(timeout=5)
        
        return jsonify({"success": True, "message": "Robot stopped successfully"})
    except Exception as e:
        logger.exception("Error stopping robot")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current robot status"""
    return jsonify({"success": True, "status": robot_status})

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get operation history"""
    try:
        date_filter = request.args.get('date')
        
        # Get operations from database
        operations = db.get_operations(date_filter)
        
        return jsonify({"success": True, "history": operations})
    except Exception as e:
        logger.exception("Error getting history")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear operation history"""
    try:
        db.clear_operations()
        return jsonify({"success": True, "message": "History cleared successfully"})
    except Exception as e:
        logger.exception("Error clearing history")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/test-entry', methods=['POST'])
def test_entry():
    """Test a trade entry with fixed amount"""
    if not robot or not robot.is_connected():
        return jsonify({"success": False, "message": "Not connected to IQ Option"})
    
    try:
        # Execute test entry with $2
        result = robot.test_entry()
        
        if result and "operation" in result:
            # Save operation to database
            db.save_operation(result["operation"])
            
            return jsonify({
                "success": True,
                "message": "Test entry executed",
                "operation": result["operation"]
            })
        else:
            error_msg = result.get("error", "Unknown error during test entry")
            return jsonify({"success": False, "message": error_msg})
    except Exception as e:
        logger.exception("Error executing test entry")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({"success": True, "message": "API is running", "connected": robot and robot.is_connected()})

if __name__ == '__main__':
    create_log_dirs()
    app.run(debug=True, port=5000)
