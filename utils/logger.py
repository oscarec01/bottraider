"""
Sistema de logging avanzado con soporte para UI.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


# Colores para consola
class LogColors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'


class ColoredFormatter(logging.Formatter):
    """Formatter con colores para consola"""
    
    COLORS = {
        'DEBUG': LogColors.CYAN,
        'INFO': LogColors.GREEN,
        'WARNING': LogColors.YELLOW,
        'ERROR': LogColors.RED,
        'CRITICAL': LogColors.MAGENTA
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, LogColors.RESET)
        record.levelname = f"{log_color}{record.levelname}{LogColors.RESET}"
        return super().format(record)


def setup_logger(name: str = 'TradingBot', log_file: str = 'trading_bot.log',
                 level: int = logging.INFO, max_bytes: int = 10485760,
                 backup_count: int = 5) -> logging.Logger:
    """
    Configura el sistema de logging.
    
    Args:
        name: Nombre del logger
        log_file: Archivo de log
        level: Nivel de logging
        max_bytes: Tamaño máximo del archivo (10MB por defecto)
        backup_count: Número de archivos de respaldo
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar duplicados
    if logger.handlers:
        return logger
    
    # Formato
    log_format = '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Handler para archivo (con rotación)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Handler para consola (con colores)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter(log_format, date_format))
    
    # Agregar handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger hijo.
    
    Args:
        name: Nombre del módulo
        
    Returns:
        Logger
    """
    return logging.getLogger(f'TradingBot.{name}')


# Logger por defecto
default_logger = setup_logger()
