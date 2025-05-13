import sqlite3
import os
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path="trading.db"):
        self.db_path = db_path
        self.initialize_db()
    
    def initialize_db(self):
        """Initialize database and create tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create operations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    amount REAL NOT NULL,
                    result REAL NOT NULL,
                    outcome TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized")
        except Exception as e:
            logger.exception("Database initialization error")
    
    def save_operation(self, operation):
        """Save operation to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO operations (asset, direction, amount, result, outcome, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                operation['asset'],
                operation['direction'],
                operation['amount'],
                operation['result'],
                operation['outcome'],
                operation['timestamp']
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Operation saved: {operation}")
            return True
        except Exception as e:
            logger.exception("Error saving operation")
            return False
    
    def get_operations(self, date_filter=None):
        """Get operations from database, optionally filtered by date"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if date_filter:
                # Filter by date
                query = '''
                    SELECT * FROM operations
                    WHERE date(timestamp) = ?
                    ORDER BY timestamp DESC
                '''
                cursor.execute(query, (date_filter,))
            else:
                # Get all operations
                query = '''
                    SELECT * FROM operations
                    ORDER BY timestamp DESC
                '''
                cursor.execute(query)
            
            # Convert to list of dictionaries
            operations = []
            for row in cursor.fetchall():
                operations.append({
                    'asset': row['asset'],
                    'direction': row['direction'],
                    'amount': float(row['amount']),
                    'result': float(row['result']),
                    'outcome': row['outcome'],
                    'timestamp': row['timestamp']
                })
            
            conn.close()
            return operations
        except Exception as e:
            logger.exception("Error getting operations")
            return []
    
    def clear_operations(self):
        """Clear all operations from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM operations')
            
            conn.commit()
            conn.close()
            
            logger.info("Operations cleared")
            return True
        except Exception as e:
            logger.exception("Error clearing operations")
            return False
    
    def get_statistics(self, date_filter=None):
        """Get trading statistics"""
        try:
            operations = self.get_operations(date_filter)
            
            if not operations:
                return {
                    "operations_count": 0,
                    "wins": 0,
                    "losses": 0,
                    "profit": 0.0,
                    "win_rate": 0.0,
                    "max_profit": 0.0,
                    "max_loss": 0.0
                }
            
            # Calculate statistics
            wins = sum(1 for op in operations if op['outcome'].lower() == 'win')
            losses = sum(1 for op in operations if op['outcome'].lower() == 'loss')
            profit = sum(op['result'] for op in operations)
            win_rate = (wins / len(operations) * 100) if operations else 0
            
            max_profit = max([op['result'] for op in operations if op['outcome'].lower() == 'win'], default=0)
            max_loss = min([op['result'] for op in operations if op['outcome'].lower() == 'loss'], default=0)
            
            return {
                "operations_count": len(operations),
                "wins": wins,
                "losses": losses,
                "profit": profit,
                "win_rate": win_rate,
                "max_profit": max_profit,
                "max_loss": max_loss
            }
        except Exception as e:
            logger.exception("Error getting statistics")
            return {}
