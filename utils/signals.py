"""
Señales Qt personalizadas para comunicación thread-safe.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Any


class TradingSignals(QObject):
    """Señales personalizadas para el sistema de trading"""
    
    # Señales de análisis
    analysis_started = pyqtSignal(str)  # symbol
    analysis_complete = pyqtSignal(str, dict)  # symbol, result
    analysis_error = pyqtSignal(str, str)  # symbol, error_message
    
    # Señales de ejecución
    trade_opened = pyqtSignal(str, dict)  # symbol, trade_data
    trade_closed = pyqtSignal(str, dict)  # symbol, close_data
    trade_error = pyqtSignal(str, str)  # symbol, error_message
    
    # Señales de estado
    status_update = pyqtSignal(str, str)  # symbol, status_message
    progress_update = pyqtSignal(str, int)  # symbol, percentage
    
    # Señales de logging
    log_message = pyqtSignal(str, str)  # level, message
    
    # Señales de conexión MT5
    mt5_connected = pyqtSignal(bool)  # success
    mt5_disconnected = pyqtSignal()
    
    # Señales de configuración
    settings_changed = pyqtSignal(dict)  # new_settings
    
    # Señales de símbolos
    symbol_added = pyqtSignal(str)  # symbol
    symbol_removed = pyqtSignal(str)  # symbol
    symbol_started = pyqtSignal(str)  # symbol
    symbol_stopped = pyqtSignal(str)  # symbol
