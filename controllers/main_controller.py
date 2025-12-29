"""
MainController - Controlador principal de la aplicación.
Orquesta la comunicación entre vistas, modelos y otros controladores.
"""

from PyQt6.QtCore import QObject, QTimer
from typing import Dict, List
from views.main_window import MainWindow
from controllers.symbol_controller import SymbolController
from models.database import Database
from models.mt5_connection import MT5Connection
from models.symbol_config import SymbolConfig
from utils.logger import get_logger
import config

logger = get_logger(__name__)


class MainController(QObject):
    """
    Controlador principal que gestiona toda la aplicación.
    
    Responsabilidades:
    - Inicializar la base de datos
    - Gestionar la conexión MT5
    - Crear y gestionar SymbolControllers
    - Coordinar la comunicación entre componentes
    - Manejar eventos de la UI
    """
    
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self.window = main_window
        self.db = Database()
        self.mt5 = MT5Connection()
        
        # Diccionario de controladores por símbolo
        self.symbol_controllers: Dict[str, SymbolController] = {}
        
        logger.info("MainController inicializado")
        
        # Conectar señales de la ventana
        self._connect_window_signals()
        
        # Inicializar componentes
        self._initialize()
        
        # Timer para verificar ganancia diaria (cada 30 segundos)
        self.daily_profit_timer = QTimer()
        self.daily_profit_timer.timeout.connect(self._check_daily_profit)
        self.daily_profit_timer.start(30000)  # 30 segundos
    
    def _connect_window_signals(self):
        """Conecta las señales de la ventana principal"""
        self.window.settings_requested.connect(self._on_settings_requested)
        self.window.history_requested.connect(self._on_history_requested)
        self.window.add_symbol_requested.connect(self._on_add_symbol_requested)
        self.window.clear_all_requested.connect(self._on_clear_all_requested)
        self.window.symbol_play_clicked.connect(self._on_symbol_play)
        self.window.symbol_stop_clicked.connect(self._on_symbol_stop)
        self.window.symbol_delete_clicked.connect(self._on_symbol_delete)
    
    def _initialize(self):
        """Inicializa los componentes de la aplicación"""
        logger.info("Inicializando aplicación...")
        
        # Mostrar mensaje de bienvenida
        self.window.show_status_message("Inicializando aplicación...", 0)
        
        # Intentar conectar a MT5 con credenciales guardadas
        self._try_connect_mt5()
        
        # Cargar símbolos guardados
        self._load_saved_symbols()
        
        self.window.show_status_message("Listo", 3000)
        logger.info("✅ Aplicación inicializada")
    
    def _try_connect_mt5(self):
        """Intenta conectar a MT5 con credenciales guardadas"""
        try:
            # Intentar cargar credenciales de BD
            account = self.db.get_setting('mt5_account')
            password = self.db.get_setting('mt5_password')
            server = self.db.get_setting('mt5_server')
            
            # Si no hay credenciales en BD, usar config.py
            if not all([account, password, server]):
                account = config.MT5_ACCOUNT
                password = config.MT5_PASSWORD
                server = config.MT5_SERVER
            
            logger.info(f"Intentando conectar a MT5: {server}, Cuenta: {account}")
            
            success = self.mt5.connect(account, password, server)
            
            if success:
                self.window.update_mt5_status(True, account)
                self.window.show_status_message(f"✅ Conectado a MT5 (Cuenta: {account})", 5000)
                logger.info("✅ Conexión MT5 exitosa")
            else:
                self.window.update_mt5_status(False)
                self.window.show_warning(
                    "Conexión MT5 Fallida",
                    "No se pudo conectar a MetaTrader 5.\n\n"
                    "Verifica tus credenciales en Configuración → Ajustes."
                )
                logger.warning("⚠️ No se pudo conectar a MT5")
        
        except Exception as e:
            logger.error(f"Error conectando a MT5: {e}")
            self.window.update_mt5_status(False)
            self.window.show_error(
                "Error de Conexión",
                f"Error al conectar a MT5:\n{str(e)}"
            )
    
    def _load_saved_symbols(self):
        """Carga los símbolos guardados en la BD"""
        try:
            symbols = self.db.get_active_symbols()
            logger.info(f"Cargando {len(symbols)} símbolos guardados...")
            
            for symbol_data in symbols:
                symbol_name = symbol_data['symbol']
                was_running = symbol_data['is_running']
                
                # Agregar al dashboard (from_db=True, show_errors=False para evitar diálogos durante carga)
                success = self.add_symbol(symbol_name, auto_start=False, from_db=True, show_errors=False)
                
                # Si estaba corriendo Y se agregó exitosamente, preguntar si reanudar
                if success and was_running:
                    reply = self.window.confirm(
                        "Reanudar Símbolo",
                        f"El símbolo '{symbol_name}' estaba activo.\n"
                        f"¿Deseas reanudarlo?"
                    )
                    if reply:
                        self._on_symbol_play(symbol_name)
            
            # Actualizar contador
            self._update_symbols_count()
        
        except Exception as e:
            logger.error(f"Error cargando símbolos: {e}")
    
    # ==================== GESTIÓN DE SÍMBOLOS ====================
    
    def add_symbol(self, symbol: str, auto_start: bool = False, from_db: bool = False, show_errors: bool = True) -> bool:
        """
        Agrega un nuevo símbolo al dashboard.
        
       Args:
            symbol: Nombre del símbolo
            auto_start: Si debe iniciar automáticamente
            from_db: Si el símbolo viene de BD (evita duplicar inserción)
            show_errors: Si debe mostrar diálogos de error (False durante carga inicial)
            
        Returns:
            True si se agregó exitosamente
        """
        # Verificar duplicados en controladores activos
        if symbol in self.symbol_controllers:
            if show_errors:
                self.window.show_warning(
                    "Símbolo Duplicado",
                    f"El símbolo '{symbol}' ya está en el dashboard."
                )
            logger.warning(f"Símbolo '{symbol}' ya existe en controladores activos")
            return False
        
        try:
            # Crear SymbolConfig
            symbol_config = SymbolConfig.from_symbol_name(symbol)
            
            # Guardar en BD SOLO si NO viene de BD
            if not from_db:
                try:
                    self.db.add_symbol(
                        symbol=symbol,
                        symbol_type=symbol_config.symbol_type,
                        lot_size=symbol_config.lot_size
                    )
                    logger.info(f"Símbolo '{symbol}' guardado en BD")
                except Exception as db_error:
                    # Si falla por duplicado, continuar (el símbolo ya existe en BD)
                    if "UNIQUE constraint" in str(db_error):
                        logger.warning(f"Símbolo '{symbol}' ya existe en BD, continuando...")
                    else:
                        raise  # Re-lanzar si es otro error
            
            # Crear card en el dashboard
            card = self.window.dashboard.add_symbol_card(symbol)
            
            # Crear controlador
            interval = self.db.get_setting('analysis_interval', 120)
            controller = SymbolController(symbol, card, interval)
            
            # Guardar controlador en memoria
            self.symbol_controllers[symbol] = controller
            
            logger.info(f"✅ Símbolo '{symbol}' agregado al dashboard")
            
            # Mostrar mensaje solo si es nuevo y show_errors=True
            if not from_db and show_errors:
                self.window.show_status_message(f"✅ Símbolo '{symbol}' agregado", 3000)
            
            # Actualizar contador
            self._update_symbols_count()
            
            # Auto-iniciar si se solicita
            if auto_start and self.mt5.is_connected():
                controller.start()
            
            return True
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error agregando símbolo '{symbol}': {error_msg}")
            
            # Solo mostrar diálogo si show_errors=True
            if show_errors:
                self.window.show_error(
                    "Error",
                    f"No se pudo agregar el símbolo '{symbol}':\n{error_msg}"
                )
            
            return False
    
    def remove_symbol(self, symbol: str):
        """Remueve un símbolo del dashboard"""
        if symbol not in self.symbol_controllers:
            return
        
        # Confirmar
        reply = self.window.confirm(
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar '{symbol}'?\n\n"
            f"Se detendrá el análisis y se removerá del dashboard."
        )
        
        if not reply:
            return
        
        try:
            # Detener y limpiar controlador
            controller = self.symbol_controllers[symbol]
            controller.cleanup()
            
            # Remover del diccionario
            del self.symbol_controllers[symbol]
            
            # Remover del dashboard
            self.window.dashboard.remove_symbol_card(symbol)
            
            # Actualizar BD
            self.db.delete_symbol(symbol)
            
            logger.info(f"Símbolo '{symbol}' eliminado")
            self.window.show_status_message(f"Símbolo '{symbol}' eliminado", 3000)
            
            # Actualizar contador
            self._update_symbols_count()
        
        except Exception as e:
            logger.error(f"Error eliminando símbolo: {e}")
            self.window.show_error("Error", f"No se pudo eliminar el símbolo:\n{str(e)}")
    
    def _update_symbols_count(self):
        """Actualiza el contador de símbolos en la barra de estado"""
        total = len(self.symbol_controllers)
        active = sum(1 for c in self.symbol_controllers.values() if c.is_running())
        self.window.update_symbols_count(active, total)
    
    # ==================== SLOTS PARA EVENTOS DE LA UI ====================
    
    def _on_settings_requested(self):
        """Maneja la solicitud de abrir configuración"""
        logger.info("Abriendo configuración...")
        
        from views.settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self.window)
        
        # Conectar señal de configuración guardada
        dialog.settings_saved.connect(self._on_settings_saved)
        
        dialog.exec()
    
    def _on_settings_saved(self, new_settings: dict):
        """
        Maneja cambios en la configuración.
        FLUJO: Detener workers → Desconectar MT5 → Guardar → Reconectar → Reiniciar workers
        """
        logger.info("Aplicando nuevos ajustes...")
        
        try:
            # 1. Guardar estado de símbolos activos
            active_symbols = []
            for symbol, controller in self.symbol_controllers.items():
                if controller.is_running():
                    active_symbols.append(symbol)
                    logger.info(f"   Guardando estado activo de: {symbol}")
            
            # 2. Detener TODOS los workers activos
            logger.info("Deteniendo workers activos...")
            for symbol in list(self.symbol_controllers.keys()):
                controller = self.symbol_controllers.get(symbol)
                if controller and controller.is_running():
                    controller.stop()
                    logger.info(f"   Worker detenido: {symbol}")
            
            # 3. Desconectar de MT5 completamente
            logger.info("Desconectando de MT5...")
            if self.mt5.is_connected():
                self.mt5.disconnect()
                logger.info("   ✅ MT5 desconectado")
            
            # 4. Guardar ajustes (esto ya está hecho en SettingsDialog, pero confirmamos)
            logger.info("Ajustes guardados en BD")
            
            # 5. Reconectar a MT5 con nuevas credenciales
            logger.info("Reconectando a MT5...")
            success = self._try_connect_mt5()
            
            if not success:
                self.window.show_error("Error", "No se pudo reconectar a MT5. Verifica las credenciales.")
                return
            
            # 6. Reiniciar workers que estaban activos
            if active_symbols:
                logger.info(f"Reiniciando {len(active_symbols)} workers...")
                for symbol in active_symbols:
                    controller = self.symbol_controllers.get(symbol)
                    if controller:
                        controller.start()
                        logger.info(f"   Worker reiniciado: {symbol}")
            
            logger.info("✅ Ajustes aplicados correctamente")
            self.window.show_status_message("✅ Ajustes aplicados correctamente", 3000)
            
        except Exception as e:
            logger.error(f"Error aplicando ajustes: {e}", exc_info=True)
            self.window.show_error("Error", f"Error aplicando ajustes: {e}")
    
    def _on_history_requested(self):
        """Maneja la solicitud de ver historial"""
        logger.info("Abriendo historial...")
        
        from views.history_dialog import HistoryDialog
        
        dialog = HistoryDialog(self.window)
        dialog.exec()
    
    def _on_add_symbol_requested(self):
        """Maneja la solicitud de agregar símbolo"""
        logger.info("Solicitando agregar símbolo...")
        
        # TODO: Implementar AddSymbolDialog
        # Por ahora, usar un diálogo simple de input
        from PyQt6.QtWidgets import QInputDialog
        
        # Listar símbolos disponibles de config
        available_symbols = config.ACTIVOS_PERMITIDOS
        
        symbol, ok = QInputDialog.getItem(
            self.window,
            "Agregar Símbolo",
            "Selecciona un símbolo:",
            available_symbols,
            0,
            False
        )
        
        if ok and symbol:
            self.add_symbol(symbol, auto_start=False)
    
    def _on_clear_all_requested(self):
        """Maneja la solicitud de limpiar todos los símbolos"""
        if len(self.symbol_controllers) == 0:
            self.window.show_info(
                "Sin Operaciones",
                "No hay símbolos para eliminar."
            )
            return
        
        # Confirmar acción
        num_symbols = len(self.symbol_controllers)
        reply = self.window.confirm(
            "Confirmar Limpieza",
            f"¿Estás seguro de eliminar TODOS los símbolos ({num_symbols})?\\n\\n"
            f"Se detendrán todos los análisis y se removerán del dashboard."
        )
        
        if not reply:
            return
        
        try:
            logger.info(f"🗑️ Eliminando todos los símbolos ({num_symbols})...")
            
            # Obtener lista de símbolos a eliminar
            symbols_to_remove = list(self.symbol_controllers.keys())
            
            # Eliminar cada símbolo
            for symbol in symbols_to_remove:
                try:
                    # Detener y limpiar controlador
                    controller = self.symbol_controllers[symbol]
                    controller.cleanup()
                    
                    # Remover del diccionario
                    del self.symbol_controllers[symbol]
                    
                    # Remover del dashboard
                    self.window.dashboard.remove_symbol_card(symbol)
                    
                    # Actualizar BD
                    self.db.delete_symbol(symbol)
                    
                    logger.info(f"  ✅ Símbolo '{symbol}' eliminado")
                
                except Exception as e:
                    logger.error(f"  ❌ Error eliminando símbolo '{symbol}': {e}")
            
            # Actualizar contador
            self._update_symbols_count()
            
            self.window.show_status_message(f"✅ {num_symbols} símbolos eliminados", 3000)
            logger.info(f"✅ Limpieza completada: {num_symbols} símbolos eliminados")
        
        except Exception as e:
            logger.error(f"Error durante limpieza total: {e}")
            self.window.show_error("Error", f"Error durante la limpieza:\\n{str(e)}")

    
    def _on_symbol_play(self, symbol: str):
        """Maneja el clic en Play de un símbolo"""
        if symbol in self.symbol_controllers:
            logger.info(f"▶️ Iniciando análisis para {symbol}")
            self.symbol_controllers[symbol].start()
            self._update_symbols_count()
        else:
            logger.warning(f"Controlador no encontrado para {symbol}")
    
    def _on_symbol_stop(self, symbol: str):
        """Maneja el clic en Stop de un símbolo"""
        if symbol in self.symbol_controllers:
            logger.info(f"⏹ Deteniendo análisis para {symbol}")
            self.symbol_controllers[symbol].stop()
            self._update_symbols_count()
        else:
            logger.warning(f"Controlador no encontrado para {symbol}")
    
    
    def _on_symbol_delete(self, symbol: str):
        """
        Maneja la eliminación de un símbolo.
        Llama a remove_symbol que detiene el worker y limpia todo.
        """
        logger.info(f"Solicitud de eliminar símbolo: {symbol}")
        self.remove_symbol(symbol)
        logger.info(f"Símbolo {symbol} eliminado")
    
    def _check_daily_profit(self):
        """
        Verifica la ganancia diaria y actualiza el indicador.
        Si se alcanza la meta, detiene todos los workers.
        """
        try:
            # Obtener profit del día y objetivo
            daily_target = self.db.get_setting('daily_profit_target', 0)
            current_profit = self.mt5.get_today_profit()
            
            # Actualizar UI
            self.window.update_daily_profit(current_profit, daily_target)
            
            # Verificar si se alcanzó la meta
            if daily_target > 0 and current_profit >= daily_target:
                logger.info(f"🎯 META DIARIA ALCANZADA: ${current_profit:.2f} >= ${daily_target:.2f}")
                
                # Detener todos los workers activos
                active_workers = [symbol for symbol, ctrl in self.symbol_controllers.items() 
                                 if ctrl.is_running()]
                
                if active_workers:
                    logger.info(f"⏸️ Deteniendo {len(active_workers)} workers activos...")
                    
                    for symbol in active_workers:
                        self.symbol_controllers[symbol].stop()
                        logger.info(f"   • Worker '{symbol}' detenido")
                    
                    # Mostrar mensaje al usuario
                    self.window.show_info(
                        "🎯 Meta Diaria Alcanzada",
                        f"La ganancia del día (${current_profit:.2f}) ha alcanzado "
                        f"la meta configurada (${daily_target:.2f}).\n\n"
                        "Trading pausado automáticamente.\n"
                        "Puede reanudar manualmente si lo desea."
                    )
                    
                    # Detener el timer para no mostrar el mensaje repetidamente
                    self.daily_profit_timer.stop()
        
        except Exception as e:
            logger.error(f"Error verificando ganancia diaria: {e}")
    
    def cleanup(self):
        """Limpia recursos antes de cerrar la aplicación"""
        logger.info("⏱️ Iniciando limpieza de recursos...")
        
        # Detener timer de profit diario
        if hasattr(self, 'daily_profit_timer'):
            self.daily_profit_timer.stop()
            logger.info("Timer de profit diario detenido")
        
        # Detener todos los workers
        logger.info("Deteniendo workers...")
        for symbol, controller in self.symbol_controllers.items():
            if controller.is_running():
                logger.info(f"   Deteniendo worker: {symbol}")
                controller.stop()
        
        # Desconectar MT5
        if self.mt5 and self.mt5.is_connected():
            logger.info("Desconectando de MT5...")
            self.mt5.disconnect()
            logger.info("✅ MT5 desconectado")
        
        # Cerrar BD
        self.db.close()
        
        logger.info("✅ Limpieza completada")
