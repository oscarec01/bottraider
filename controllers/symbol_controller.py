"""
SymbolController - Controlador que gestiona un símbolo específico.
Conecta la vista (SymbolCard) con el modelo (TradingWorker).
"""

from PyQt6.QtCore import QObject
from typing import Optional
from workers.trading_worker import TradingWorker
from views.symbol_card import SymbolCard
from models.database import Database
from models.mt5_connection import MT5Connection
from utils.logger import get_logger

logger = get_logger(__name__)


class SymbolController(QObject):
    """
    Controlador para un símbolo específico.
    
    Responsabilidades:
    - Crear y gestionar el TradingWorker
    - Conectar señales del worker con la vista (SymbolCard)
    - Manejar comandos de start/stop/pause
    - Actualizar el card con datos en tiempo real
    """
    
    def __init__(self, symbol: str, card: SymbolCard, interval: int = 120):
        """
        Args:
            symbol: Nombre del símbolo
            card: SymbolCard asociado
            interval: Intervalo de análisis en segundos
        """
        super().__init__()
        self.symbol = symbol
        self.card = card
        self.interval = interval
        
        # Worker (se crea pero no se inicia automáticamente)
        self.worker: Optional[TradingWorker] = None
        
        # Referencias a modelos
        self.db = Database()
        self.mt5 = MT5Connection()
        
        logger.info(f"SymbolController creado para {symbol}")
    
    def _create_worker(self):
        """Crea el worker si no existe"""
        if self.worker is None:
            self.worker = TradingWorker(self.symbol, self.interval)
            self._connect_worker_signals()
            logger.info(f"Worker creado para {self.symbol}")
    
    def _connect_worker_signals(self):
        """Conecta las señales del worker con los slots del card"""
        if not self.worker:
            return
        
        # Análisis iniciado
        self.worker.analysis_started.connect(self._on_analysis_started)
        
        # Análisis completado
        self.worker.analysis_complete.connect(self._on_analysis_complete)
        
        # Trade ejecutado
        self.worker.trade_executed.connect(self._on_trade_executed)
        
        # Error
        self.worker.error_occurred.connect(self._on_error)
        
        # Actualización de estado
        self.worker.status_update.connect(self._on_status_update)
        
        # Actualización de progreso
        self.worker.progress_update.connect(self._on_progress_update)
    
    # ==================== COMANDOS PÚBLICOS ====================
    
    def start(self):
        """Inicia el worker"""
        if not self.mt5.is_connected():
            logger.warning(f"No se puede iniciar {self.symbol}: MT5 no conectado")
            self.card.set_error_state("MT5 no conectado")
            return
        
        # Crear worker si no existe
        self._create_worker()
        
        # Iniciar worker si no está corriendo
        if not self.worker.is_running():
            logger.info(f"▶️ Iniciando worker para {self.symbol}")
            self.worker.start()
            self.card.set_running(True)
            
            # Actualizar BD
            self.db.update_symbol_status(self.symbol, True)
        else:
            logger.warning(f"{self.symbol} ya está en ejecución")
    
    def stop(self):
        """Detiene el worker"""
        if self.worker and self.worker.is_running():
            logger.info(f"⏹ Deteniendo worker para {self.symbol}")
            self.worker.stop()
            self.card.set_running(False)
            self.card.update_status("Detenido")
            self.card.update_progress(0)
            
            # Actualizar BD
            self.db.update_symbol_status(self.symbol, False)
        else:
            logger.warning(f"{self.symbol} no está en ejecución")
    
    def pause(self):
        """Pausa el worker"""
        if self.worker and self.worker.is_running():
            logger.info(f"⏸ Pausando worker para {self.symbol}")
            self.worker.pause()
            self.card.update_status("Pausado")
    
    def resume(self):
        """Reanuda el worker"""
        if self.worker and self.worker.is_paused():
            logger.info(f"▶️ Reanudando worker para {self.symbol}")
            self.worker.resume()
            self.card.update_status("Activo")
    
    def is_running(self) -> bool:
        """Verifica si el worker está corriendo"""
        return self.worker is not None and self.worker.is_running()
    
    def cleanup(self):
        """Limpia recursos del controlador"""
        if self.worker:
            if self.worker.is_running():
                self.worker.stop()
            self.worker.deleteLater()
            self.worker = None
        logger.info(f"SymbolController limpiado para {self.symbol}")
    
    # ==================== SLOTS PARA SEÑALES DEL WORKER ====================
    
    def _on_analysis_started(self, symbol: str):
        """Maneja el inicio del análisis"""
        if symbol == self.symbol:
            self.card.update_status("Analizando...")
            self.card.update_progress(10)
            logger.debug(f"[{symbol}] Análisis iniciado")
    
    def _on_analysis_complete(self, symbol: str, result: dict):
        """
        Maneja la finalización del análisis.
        Actualiza el card con los resultados.
        """
        if symbol != self.symbol:
            return
        
        final_action = result.get('final_action', 'ESPERAR')
        confidence = result.get('confidence', 0)
        
        # Actualizar señal y confianza
        self.card.update_signal(final_action, confidence)
        
        # Extraer información del Paso 2 (Regresión Lineal)
        paso2 = result.get('paso2', {})
        regression_tendencia = paso2.get('tendencia', 'N/A')
        regression_confianza = paso2.get('confianza', 0)
        regression_text = f"{regression_tendencia} ({regression_confianza}%)"
        
        # Extraer información del Paso 3 (Panel de Expertos)
        paso3 = result.get('paso3', {})
        panel_veredicto = paso3.get('veredicto_matematico', 'N/A')
        panel_confianza = paso3.get('confianza_matematica', 0)
        panel_text = f"{panel_veredicto} ({panel_confianza}%)"
        
        # Actualizar detalles del análisis CON análisis completo
        self.card.update_analysis_details(
            regression_text, 
            panel_text, 
            full_analysis=result  # ← Pasar análisis completo
        )
        
        # Actualizar precio si está disponible
        try:
            price_data = self.mt5.get_current_price(self.symbol)
            if price_data:
                price = price_data.get('bid', 0)
                self.card.update_price(price)
        except Exception as e:
            logger.error(f"Error obteniendo precio: {e}")
        
        # Mensaje de estado
        if final_action in ['COMPRA', 'VENTA']:
            self.card.update_status(f"Señal: {final_action} ({confidence}%)")
        else:
            self.card.update_status(f"Sin señal ({confidence}%)")
        
        logger.info(f"[{symbol}] Análisis completo: {final_action} ({confidence}%)")

    
    def _on_trade_executed(self, symbol: str, trade_data: dict):
        """Maneja la ejecución de un trade"""
        if symbol != self.symbol:
            return
        
        action = trade_data.get('action', '???')
        price = trade_data.get('price', 0)
        ticket = trade_data.get('ticket', 0)
        
        self.card.update_status(f"✅ {action} @ {price:.5f} (#{ticket})")
        
        logger.info(f"[{symbol}] Trade ejecutado: {action} @ {price:.5f}")
    
    def _on_error(self, symbol: str, error_message: str):
        """Maneja errores del worker"""
        if symbol != self.symbol:
            return
        
        # Obtener detalles del error desde la BD si están disponibles
        try:
            errors = self.db.get_errors(symbol=symbol, limit=1)
            error_details = errors[0]['stack_trace'] if errors else error_message
        except:
            error_details = error_message
        
        self.card.set_error_state(error_message, error_details)
        logger.error(f"[{symbol}] Error: {error_message}")
    
    def _on_status_update(self, symbol: str, status: str):
        """Actualiza el estado mostrado en el card"""
        if symbol != self.symbol:
            return
        
        self.card.update_status(status)
    
    def _on_progress_update(self, symbol: str, progress: int):
        """Actualiza la barra de progreso del card"""
        if symbol != self.symbol:
            return
        
        self.card.update_progress(progress)
