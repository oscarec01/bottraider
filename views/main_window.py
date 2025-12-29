"""
MainWindow - Ventana principal de la aplicación.
Incluye menú superior, dashboard, y barra de estado.
"""

from PyQt6.QtWidgets import (QMainWindow, QStatusBar, QMenuBar, QMenu,
                              QMessageBox, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from views.dashboard_view import DashboardView
from views.styles import get_theme


class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación de trading.
    
    Componentes:
    - Menú superior (Archivo, Configuración, Ver, Ayuda)
    - Dashboard con grid de símbolos
    - Barra de estado
    
    Señales:
    - settings_requested: Cuando se solicita abrir configuración
    - history_requested: Cuando se solicita ver historial
    - add_symbol_requested: Cuando se solicita agregar símbolo
    - about_requested: Solicita mostrar "Acerca de"
    """
    
    # Señales
    settings_requested = pyqtSignal()
    history_requested = pyqtSignal()
    add_symbol_requested = pyqtSignal()
    clear_all_requested = pyqtSignal()  # Señal para limpiar todos los símbolos
    about_requested = pyqtSignal()
    symbol_play_clicked = pyqtSignal(str)
    symbol_stop_clicked = pyqtSignal(str)
    symbol_delete_clicked = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤖 Bot de Trading - Deriv Synthetic Indices")
        self.setMinimumSize(1200, 700)
        
        # Aplicar tema oscuro
        self.setStyleSheet(get_theme("dark"))
        
        self._setup_ui()
        self._create_menus()
        self._create_status_bar()
        
    def _setup_ui(self):
        """Configura la interfaz principal"""
        # Dashboard como widget central
        self.dashboard = DashboardView()
        self.setCentralWidget(self.dashboard)
        
        # Conectar señales del dashboard
        self.dashboard.add_symbol_clicked.connect(self.add_symbol_requested.emit)
        self.dashboard.clear_all_clicked.connect(self.clear_all_requested.emit)
        self.dashboard.symbol_play_clicked.connect(self.symbol_play_clicked.emit)
        self.dashboard.symbol_stop_clicked.connect(self.symbol_stop_clicked.emit)
        self.dashboard.symbol_delete_clicked.connect(self.symbol_delete_clicked.emit)
    
    def _create_menus(self):
        """Crea el menú superior"""
        menubar = self.menuBar()
        
        # ==================== MENÚ ARCHIVO ====================
        file_menu = menubar.addMenu("📁 &Archivo")
        
        # Agregar Símbolo
        add_action = QAction("➕ Agregar Símbolo", self)
        add_action.setShortcut("Ctrl+N")
        add_action.setStatusTip("Agregar un nuevo símbolo para monitorear")
        add_action.triggered.connect(self.add_symbol_requested.emit)
        file_menu.addAction(add_action)
        
        file_menu.addSeparator()
        
        # Salir
        exit_action = QAction("🚪 Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Cerrar la aplicación")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # ==================== MENÚ CONFIGURACIÓN ====================
        config_menu = menubar.addMenu("⚙️ &Configuración")
        
        # Ajustes
        settings_action = QAction("⚙️ Ajustes...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.setStatusTip("Configurar MT5, parámetros del algoritmo y más")
        settings_action.triggered.connect(self.settings_requested.emit)
        config_menu.addAction(settings_action)
        
        # ==================== MENÚ VER ====================
        view_menu = menubar.addMenu("👁️ &Ver")
        
        # Historial de Operaciones
        history_action = QAction("📊 Historial de Operaciones", self)
        history_action.setShortcut("Ctrl+H")
        history_action.setStatusTip("Ver historial de trades y análisis")
        history_action.triggered.connect(self.history_requested.emit)
        view_menu.addAction(history_action)
        
        view_menu.addSeparator()
        
        # Logs
        logs_action = QAction("📝 Logs del Sistema", self)
        logs_action.setShortcut("Ctrl+L")
        logs_action.setStatusTip("Ver logs detallados del sistema")
        logs_action.triggered.connect(self._show_logs)
        view_menu.addAction(logs_action)
        
        # ==================== MENÚ AYUDA ====================
        help_menu = menubar.addMenu("❓ &Ayuda")
        
        # Documentación
        docs_action = QAction("📚 Documentación", self)
        docs_action.setShortcut("F1")
        docs_action.triggered.connect(self._show_documentation)
        help_menu.addAction(docs_action)
        
        help_menu.addSeparator()
        
        # Acerca de
        about_action = QAction("ℹ️ Acerca de", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Crea la barra de estado"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Label de conexión MT5
        self.mt5_status_label = QLabel("⚫ MT5: Desconectado")
        self.mt5_status_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        self.status_bar.addPermanentWidget(self.mt5_status_label)
        
        # Label de símbolos activos
        self.symbols_count_label = QLabel("Símbolos: 0 activos")
        self.symbols_count_label.setStyleSheet("color: #aaa; padding: 5px;")
        self.status_bar.addPermanentWidget(self.symbols_count_label)
        
        # Label de ganancia diaria (Money Management)
        self.daily_profit_label = QLabel("💵 Hoy: $0.00 / Meta: $0.00")
        self.daily_profit_label.setStyleSheet("color: #aaa; padding: 5px; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.daily_profit_label)
        
        # Mensaje inicial
        self.status_bar.showMessage("Bienvenido al Bot de Trading", 5000)
    
    # ==================== MÉTODOS PÚBLICOS ====================
    
    def update_mt5_status(self, connected: bool, account: int = None):
        """
        Actualiza el estado de conexión MT5 en la barra de estado.
        
        Args:
            connected: True si está conectado
            account: Número de cuenta (opcional)
        """
        if connected:
            text = f"🟢 MT5: Conectado"
            if account:
                text += f" (Cuenta: {account})"
            color = "#2ecc71"
        else:
            text = "⚫ MT5: Desconectado"
            color = "#7f8c8d"
        
        self.mt5_status_label.setText(text)
        self.mt5_status_label.setStyleSheet(f"color: {color}; padding: 5px; font-weight: bold;")
    
    def update_symbols_count(self, active: int, total: int = None):
        """
        Actualiza el contador de símbolos en la barra de estado.
        
        Args:
            active: Número de símbolos activos
            total: Número total de símbolos (opcional)
        """
        if total is not None:
            text = f"Símbolos: {active}/{total} activos"
        else:
            text = f"Símbolos: {active} activos"
        
        
        self.symbols_count_label.setText(text)
    
    def update_daily_profit(self, current_profit: float, target: float):
        """
        Actualiza el indicador de ganancia diaria.
        
        Args:
            current_profit: Profit actual del día en USD
            target: Objetivo de ganancia diaria (0 = sin límite)
        """
        if target > 0:
            text = f"💵 Hoy: ${current_profit:+.2f} / Meta: ${target:.2f}"
        else:
            text = f"💵 Hoy: ${current_profit:+.2f}"
        
        # Color dinámico: verde si positivo, rojo si negativo
        if current_profit >= 0:
            color = "#2ecc71"  # Verde
        else:
            color = "#e74c3c"  # Rojo
        
        self.daily_profit_label.setText(text)
        self.daily_profit_label.setStyleSheet(f"color: {color}; padding: 5px; font-weight: bold;")
    
    def show_status_message(self, message: str, timeout: int = 5000):
        """
        Muestra un mensaje en la barra de estado.
        
        Args:
            message: Mensaje a mostrar
            timeout: Duración en ms (0 = permanente)
        """
        self.status_bar.showMessage(message, timeout)
    
    def show_error(self, title: str, message: str):
        """
        Muestra un diálogo de error.
        
        Args:
            title: Título del error
            message: Mensaje detallado
        """
        QMessageBox.critical(self, title, message)
    
    def show_warning(self, title: str, message: str):
        """
        Muestra un diálogo de advertencia.
        
        Args:
            title: Título
            message: Mensaje
        """
        QMessageBox.warning(self, title, message)
    
    def show_info(self, title: str, message: str):
        """
        Muestra un diálogo informativo.
        
        Args:
            title: Título
            message: Mensaje
        """
        QMessageBox.information(self, title, message)
    
    def confirm(self, title: str, message: str) -> bool:
        """
        Muestra un diálogo de confirmación.
        
        Args:
            title: Título
            message: Pregunta
            
        Returns:
            True si el usuario confirma
        """
        reply = QMessageBox.question(
            self, 
            title, 
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    def _show_logs(self):
        """Muestra el panel de logs (placeholder)"""
        self.show_info(
            "Logs del Sistema",
            "Función en desarrollo.\nLos logs se guardan en 'trading_bot.log'"
        )
    
    def _show_documentation(self):
        """Muestra la documentación (placeholder)"""
        self.show_info(
            "Documentación",
            "Consulta los archivos:\n\n"
            "• README.md - Guía de uso\n"
            "• ALGORITMOS.md - Detalles técnicos\n"
            "• implementation_plan.md - Arquitectura"
        )
    
    def _show_about(self):
        """Muestra el diálogo "Acerca de" """
        about_text = """
        <h2>🤖 Bot de Trading - Deriv Synthetic Indices</h2>
        <p><b>Versión:</b> 2.0.0 PyQt6</p>
        <p><b>Arquitectura:</b> MVC con concurrencia</p>
        
        <h3>Características:</h3>
        <ul>
            <li>✅ Análisis de 5 pasos con IA (Ollama/Mistral)</li>
            <li>✅ Panel de 9 expertos técnicos</li>
            <li>✅ Regresión lineal para tendencia macro</li>
            <li>✅ Ejecución automática en MT5</li>
            <li>✅ Múltiples símbolos en paralelo</li>
            <li>✅ Persistencia completa en SQLite</li>
        </ul>
        
        <h3>Símbolos Soportados:</h3>
        <p>Boom, Crash, Volatility, Step Indices, XAUUSD</p>
        
        <p><i>Bot desarrollado con PyQt6, MetaTrader 5 y scikit-learn</i></p>
        
        <p style="color: #f39c12;"><b>⚠️ ADVERTENCIA:</b> El trading conlleva riesgos. 
        Use cuenta Demo primero.</p>
        """
        
        QMessageBox.about(self, "Acerca de Bot de Trading", about_text)
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        reply = self.confirm(
            "Confirmar Salida",
            "¿Está seguro de que desea cerrar la aplicación?\n\n"
            "Los workers activos serán detenidos."
        )
        
        if reply:
            event.accept()
        else:
            event.ignore()
