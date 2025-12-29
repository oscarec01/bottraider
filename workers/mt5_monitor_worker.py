"""
Worker thread para monitorear posiciones MT5 y aplicar trailing stops.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from models.mt5_connection import MT5Connection
from workers.trailing_stop_manager import TrailingStopManager
from models.database import Database
import time
import logging

logger = logging.getLogger(__name__)


class MT5MonitorWorker(QThread):
    """Worker que monitorea posiciones en MT5 y aplica trailing stops"""
    
    # Señales
    positions_updated = pyqtSignal(list)
    position_closed = pyqtSignal(dict)
    account_info_updated = pyqtSignal(dict)
    trailing_updated = pyqtSignal(int, float)  # ticket, nuevo_sl
    
    def __init__(self, mt5_conn: MT5Connection, interval: int = 3):
        super().__init__()
        self.mt5_conn = mt5_conn
        self.interval = interval
        self._is_running = False
        
        # Tracking de posiciones para detectar cierres
        self._last_positions = {}
        
        # Manager de trailing stops
        self.trailing_manager = TrailingStopManager()
        
        # Database para settings
        self.db = Database()
        
        logger.info(f"MT5MonitorWorker creado (intervalo: {interval}s)")
    
    def run(self):
        """Ciclo principal del monitor"""
        logger.info(f"Iniciando MT5MonitorWorker (intervalo: {self.interval}s)")
        self._is_running = True
        
        try:
            while self._is_running:
                try:
                    if not self.mt5_conn.is_connected():
                        time.sleep(5)
                        continue
                    
                    # Obtener posiciones actuales
                    positions = self.mt5_conn.get_positions()
                    
                    # Crear diccionario por ticket
                    current_positions = {p['ticket']: p for p in positions}
                    
                    # Detectar posiciones cerradas
                    for ticket, pos in self._last_positions.items():
                        if ticket not in current_positions:
                            logger.info(f"✅ Posición cerrada: {pos['symbol']} ({ticket})")
                            self.position_closed.emit(pos)
                    
                    # Actualizar último estado
                    self._last_positions = current_positions
                    
                    # Emitir posiciones actuales
                    self.positions_updated.emit(positions)
                    
                    # Actualizar info de cuenta
                    account_info = self.mt5_conn.get_account_info()
                    if account_info:
                        self.account_info_updated.emit(account_info)
                    
                    # Aplicar trailing stops a todas las posiciones abiertas
                    self._check_trailing_stops()
                    
                    # Esperar intervalo
                    time.sleep(self.interval)
                
                except Exception as e:
                    logger.error(f"Error en MT5MonitorWorker: {e}", exc_info=True)
            
        finally:
            logger.info("MT5MonitorWorker detenido")
    
    def _check_trailing_stops(self):
        """Verifica y aplica trailing stops para todos los símbolos con posiciones."""
        try:
            # Obtener todas las posiciones abiertas
            all_positions = self.mt5_conn.get_positions()
            
            if not all_positions:
                return
            
            # Obtener símbolos únicos
            symbols = list(set([p['symbol'] for p in all_positions]))
            
            # Aplicar trailing para cada símbolo
            for symbol in symbols:
                self.trailing_manager.check_and_apply_trailing(symbol)
            
            # Limpiar tracking de posiciones cerradas (cada 10 ciclos)
            if hasattr(self, '_cleanup_counter'):
                self._cleanup_counter += 1
                if self._cleanup_counter >= 10:
                    self.trailing_manager.cleanup_closed_positions()
                    self._cleanup_counter = 0
            else:
                self._cleanup_counter = 0
        
        except Exception as e:
            logger.error(f"Error en _check_trailing_stops: {e}", exc_info=True)
    
    def stop(self):
        """Detiene el worker"""
        logger.info("Deteniendo MT5MonitorWorker...")
        self._is_running = False
