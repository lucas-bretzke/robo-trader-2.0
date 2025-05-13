import logging
import sys

def setup_logging():
    """Configure o sistema de logging com detalhes para o WebSocket"""
    logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configurar o logger principal
    logging.basicConfig(
        level=logging.DEBUG,
        format=logging_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("robo-trader.log")
        ]
    )
    
    # Configurar loggers específicos
    websocket_logger = logging.getLogger("websocket")
    websocket_logger.setLevel(logging.DEBUG)
    
    # Garantir que todos os erros relacionados ao WebSocket sejam capturados
    websocket_handler = logging.FileHandler("websocket.log")
    websocket_handler.setFormatter(logging.Formatter(logging_format))
    websocket_logger.addHandler(websocket_handler)
    
    return logging.getLogger("robo-trader")

# Certifique-se de chamar esta função no início da sua aplicação
