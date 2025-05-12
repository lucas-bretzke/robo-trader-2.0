import logging
import sys
import os
import json
import time
from datetime import datetime

# Configuração de logs
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'bot_debug.log')

# Garantir que a pasta logs existe
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def setup_logging():
    """Configura o sistema de logging para debug"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('robo_trader')
    return logger

def log_api_response(response, operation_type="unknown"):
    """Registra a resposta da API IQOption para debug"""
    logger = logging.getLogger('robo_trader')
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', f'api_responses_{datetime.now().strftime("%Y%m%d")}.log')
    
    try:
        if isinstance(response, dict):
            response_str = json.dumps(response, indent=2)
        else:
            response_str = str(response)
            
        with open(log_file, 'a') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"OPERATION: {operation_type}\n")
            f.write(f"RESPONSE:\n{response_str}\n")
            f.write(f"{'='*50}\n")
            
        logger.debug(f"API Response for {operation_type} logged to {log_file}")
    except Exception as e:
        logger.error(f"Failed to log API response: {str(e)}")

def log_trade_attempt(pair, direction, amount, expiration):
    """Registra tentativas de operação para debug"""
    logger = logging.getLogger('robo_trader')
    logger.info(f"TRADE ATTEMPT: Pair={pair}, Direction={direction}, Amount={amount}, Expiration={expiration}")
