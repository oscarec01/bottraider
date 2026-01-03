"""
SettingsDialog - Diálogo de configuración de la aplicación.
Permite editar parámetros del algoritmo, credenciales MT5 y más.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                              QWidget, QLabel, QLineEdit, QPushButton, QSpinBox,
                              QDoubleSpinBox, QComboBox, QGroupBox, QFormLayout,
                              QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from models.database import Database
from models.mt5_connection import MT5Connection
from utils.validators import Validators
from utils.logger import get_logger

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """
    Diálogo de configuración con pestañas para:
    - Credenciales MT5
    - Parámetros del algoritmo
    - Configuración de Ollama
    - Gestión de riesgo
    
    Señales:
    - settings_saved: Cuando se guardan los ajustes
    """
    
    settings_saved = pyqtSignal(dict)  # Emite los nuevos settings
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Configuración del Bot de Trading")
        self.setMinimumSize(700, 600)
        
        self.db = Database()
        self.mt5 = MT5Connection()
        
        self._setup_ui()
        self._load_current_settings()
    
    def _setup_ui(self):
        """Configura la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Tab Widget
        self.tabs = QTabWidget()
        
        # Crear pestañas
        self.tabs.addTab(self._create_mt5_tab(), "🔌 MT5 Connection")
        self.tabs.addTab(self._create_algorithm_tab(), "🧮 Algoritmo")
        self.tabs.addTab(self._create_risk_tab(), "⚠️ Gestión de Riesgo")
        self.tabs.addTab(self._create_ollama_tab(), "🤖 Ollama / IA")
        
        layout.addWidget(self.tabs)
        
        # Botones inferiores
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.test_connection_btn = QPushButton("🔍 Test Connection MT5")
        self.test_connection_btn.clicked.connect(self._test_mt5_connection)
        buttons_layout.addWidget(self.test_connection_btn)
        
        self.save_btn = QPushButton("💾 Guardar Cambios")
        self.save_btn.setObjectName("PlayButton")  # Verde
        self.save_btn.clicked.connect(self._save_settings)
        buttons_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("❌ Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def _create_mt5_tab(self):
        """Crea la pestaña de configuración MT5"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de credenciales
        cred_group = QGroupBox("Credenciales MT5")
        cred_layout = QFormLayout(cred_group)
        
        self.mt5_account_input = QLineEdit()
        self.mt5_account_input.setPlaceholderText("Ej: 29514809")
        cred_layout.addRow("Número de Cuenta:", self.mt5_account_input)
        
        self.mt5_password_input = QLineEdit()
        self.mt5_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.mt5_password_input.setPlaceholderText("Tu contraseña MT5")
        cred_layout.addRow("Contraseña:", self.mt5_password_input)
        
        self.mt5_server_combo = QComboBox()
        self.mt5_server_combo.addItems(["Deriv-Demo", "Deriv-Server", "Deriv-Server-02"])
        cred_layout.addRow("Servidor:", self.mt5_server_combo)
        
        layout.addWidget(cred_group)
        
        # Información de conexión actual
        info_group = QGroupBox("Estado de Conexión")
        info_layout = QVBoxLayout(info_group)
        
        self.connection_status_label = QLabel("⚫ Desconectado")
        self.connection_status_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        info_layout.addWidget(self.connection_status_label)
        
        layout.addWidget(info_group)
        
        # Advertencia
        warning = QLabel("⚠️ IMPORTANTE: Los cambios en las credenciales requieren reconexión.\n"
                        "Los workers activos se detendrán temporalmente.")
        warning.setStyleSheet("color: #f39c12; padding: 10px; background-color: #2a2a3e; border-radius: 6px;")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        layout.addStretch()
        return widget
    
    def _create_algorithm_tab(self):
        """Crea la pestaña de parámetros del algoritmo"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Regresión Lineal
        regression_group = QGroupBox("Parámetros de Regresión Lineal")
        regression_layout = QFormLayout(regression_group)
        
        self.regression_period = QSpinBox()
        self.regression_period.setRange(7, 90)
        self.regression_period.setValue(30)
        self.regression_period.setSuffix(" días")
        regression_layout.addRow("Período de Análisis:", self.regression_period)
        
        self.regression_timeframe = QComboBox()
        self.regression_timeframe.addItems(["H1 (Horario)", "H4 (4 Horas)", "D1 (Diario)"])
        regression_layout.addRow("Timeframe:", self.regression_timeframe)
        
        self.regression_threshold = QDoubleSpinBox()
        self.regression_threshold.setRange(0.1, 2.0)
        self.regression_threshold.setValue(0.5)
        self.regression_threshold.setSingleStep(0.1)
        self.regression_threshold.setDecimals(1)
        regression_layout.addRow("Umbral de Pendiente:", self.regression_threshold)
        
        layout.addWidget(regression_group)
        
        # Análisis Técnico
        technical_group = QGroupBox("Panel de Expertos Técnicos")
        technical_layout = QFormLayout(technical_group)
        
        self.technical_period = QSpinBox()
        self.technical_period.setRange(50, 200)
        self.technical_period.setValue(100)
        self.technical_period.setSuffix(" velas")
        technical_layout.addRow("Período M5:", self.technical_period)
        
        self.expert_consensus = QSpinBox()
        self.expert_consensus.setRange(3, 9)
        self.expert_consensus.setValue(5)
        self.expert_consensus.setSuffix(" de 9")
        technical_layout.addRow("Consenso Requerido:", self.expert_consensus)
        
        layout.addWidget(technical_group)
        
        # Intervalo de análisis
        interval_group = QGroupBox("Frecuencia de Análisis")
        interval_layout = QFormLayout(interval_group)
        
        self.analysis_interval = QSpinBox()
        self.analysis_interval.setRange(30, 600)
        self.analysis_interval.setValue(120)
        self.analysis_interval.setSuffix(" segundos")
        interval_layout.addRow("Intervalo entre Análisis:", self.analysis_interval)
        
        layout.addWidget(interval_group)
        
        # Nota
        note = QLabel("💡 NOTA: Cambios se aplicarán dinámicamente a los workers activos.")
        note.setStyleSheet("color: #4ecca3; padding: 10px;")
        layout.addWidget(note)
        
        layout.addStretch()
        return widget
    
    def _create_risk_tab(self):
        """Crea la pestaña de gestión de riesgo"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Stop Loss / Take Profit
        sl_tp_group = QGroupBox("Stop Loss / Take Profit")
        sl_tp_layout = QFormLayout(sl_tp_group)
        
        self.sl_synthetics = QSpinBox()
        self.sl_synthetics.setRange(100, 2000)
        self.sl_synthetics.setValue(500)
        self.sl_synthetics.setSuffix(" pips")
        sl_tp_layout.addRow("SL (Sintéticos):", self.sl_synthetics)
        
        self.tp_synthetics = QSpinBox()
        self.tp_synthetics.setRange(100, 5000)
        self.tp_synthetics.setValue(1000)
        self.tp_synthetics.setSuffix(" pips")
        sl_tp_layout.addRow("TP (Sintéticos):", self.tp_synthetics)
        
        self.sl_xauusd = QSpinBox()
        self.sl_xauusd.setRange(50, 1000)
        self.sl_xauusd.setValue(300)
        self.sl_xauusd.setSuffix(" pips")
        sl_tp_layout.addRow("SL (XAUUSD):", self.sl_xauusd)
        
        self.tp_xauusd = QSpinBox()
        self.tp_xauusd.setRange(100, 2000)
        self.tp_xauusd.setValue(600)
        self.tp_xauusd.setSuffix(" pips")
        sl_tp_layout.addRow("TP (XAUUSD):", self.tp_xauusd)
        
        layout.addWidget(sl_tp_group)
        
        # Confianza mínima
        confidence_group = QGroupBox("Filtros de Confianza")
        confidence_layout = QFormLayout(confidence_group)
        
        self.min_confidence_ia = QSpinBox()
        self.min_confidence_ia.setRange(50, 95)
        self.min_confidence_ia.setValue(70)
        self.min_confidence_ia.setSuffix(" %")
        confidence_layout.addRow("Confianza Mínima IA:", self.min_confidence_ia)
        
        self.enable_auto_trading = QCheckBox("Ejecutar trades automáticamente")
        self.enable_auto_trading.setChecked(True)
        confidence_layout.addRow("Auto-Trading:", self.enable_auto_trading)
        
        layout.addWidget(confidence_group)
        
        # Money Management
        money_group = QGroupBox("💰 Gestión de Capital")
        money_layout = QFormLayout(money_group)
        
        self.risk_percentage = QDoubleSpinBox()
        self.risk_percentage.setRange(0.1, 5.0)
        self.risk_percentage.setValue(1.0)
        self.risk_percentage.setSingleStep(0.1)
        self.risk_percentage.setDecimals(1)
        self.risk_percentage.setSuffix(" %")
        money_layout.addRow("% Riesgo por Operación:", self.risk_percentage)
        
        self.daily_profit_target = QSpinBox()
        self.daily_profit_target.setRange(0, 10000)
        self.daily_profit_target.setValue(0)
        self.daily_profit_target.setSuffix(" USD")
        self.daily_profit_target.setSpecialValueText("Sin límite")
        money_layout.addRow("Objetivo Ganancia Diaria:", self.daily_profit_target)
        
        self.risk_reward_ratio = QDoubleSpinBox()
        self.risk_reward_ratio.setRange(1.0, 5.0)
        self.risk_reward_ratio.setValue(3.0)
        self.risk_reward_ratio.setSingleStep(0.5)
        self.risk_reward_ratio.setDecimals(1)
        self.risk_reward_ratio.setPrefix("1:")
        money_layout.addRow("Ratio Riesgo:Beneficio:", self.risk_reward_ratio)
        
        layout.addWidget(money_group)
        
        # Scalping & Protección
        scalping_group = QGroupBox("📈 Scalping Avanzado")
        scalping_layout = QFormLayout(scalping_group)
        
        self.scalper_mode = QCheckBox("Enfoque exclusivo en últimos 15 minutos M5")
        self.scalper_mode.setChecked(False)
        scalping_layout.addRow("Modo Scalper (M5):", self.scalper_mode)
        
        self.max_spread_pips = QSpinBox()
        self.max_spread_pips.setRange(1, 100)
        self.max_spread_pips.setValue(10)
        self.max_spread_pips.setSuffix(" pips")
        self.max_spread_pips.setToolTip("Rechazar órdenes si spread excede este valor")
        scalping_layout.addRow("Spread Máximo Permitido:", self.max_spread_pips)
        
        self.enable_trailing_stop = QCheckBox("Activar Trailing Stop automático")
        self.enable_trailing_stop.setChecked(False)
        scalping_layout.addRow("Trailing Stop:", self.enable_trailing_stop)
        
        self.trailing_activation = QSpinBox()
        self.trailing_activation.setRange(10, 1000)  # Ampliado para Boom/Crash
        self.trailing_activation.setValue(300)  # Default optimizado para spikes
        self.trailing_activation.setSuffix(" pips")
        self.trailing_activation.setToolTip("Profit necesario para activar trailing (300 pips para Boom/Crash)")
        scalping_layout.addRow("Activación Trailing:", self.trailing_activation)
        
        self.trailing_distance = QSpinBox()
        self.trailing_distance.setRange(10, 500)  # Ampliado para Boom/Crash
        self.trailing_distance.setValue(150)  # Default optimizado para volatilidad
        self.trailing_distance.setSuffix(" pips")
        self.trailing_distance.setToolTip("Distancia del SL al precio actual (150 pips para Boom/Crash)")
        scalping_layout.addRow("Distancia Trailing:", self.trailing_distance)
        
        layout.addWidget(scalping_group)
        
        
        layout.addStretch()
        return widget
    
    def _create_ollama_tab(self):
        """Crea la pestaña de configuración de IA (Ollama / Cloudflare)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Selector de proveedor
        provider_group = QGroupBox("🤖 Proveedor de IA")
        provider_layout = QFormLayout(provider_group)
        
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems(["Ollama (Local)", "Cloudflare Workers AI"])
        self.ai_provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addRow("Proveedor:", self.ai_provider_combo)
        
        self.enable_ia = QCheckBox("Habilitar Análisis con IA")
        self.enable_ia.setChecked(True)
        provider_layout.addRow("Estado:", self.enable_ia)
        
        layout.addWidget(provider_group)
        
        # ===== CONFIGURACIÓN OLLAMA =====
        self.ollama_group = QGroupBox("⚙️ Configuración de Ollama")
        ollama_layout = QFormLayout(self.ollama_group)
        
        self.ollama_url = QLineEdit()
        self.ollama_url.setText("http://localhost:11434/api/generate")
        ollama_layout.addRow("URL de Ollama:", self.ollama_url)
        
        self.ollama_model = QComboBox()
        self.ollama_model.addItems(["mistral", "llama2", "llama3", "codellama", "gemma"])
        ollama_layout.addRow("Modelo:", self.ollama_model)
        
        ollama_info = QLabel("ℹ️ Asegúrate de que Ollama esté corriendo con 'ollama serve'")
        ollama_info.setStyleSheet("color: #aaa; padding: 5px;")
        ollama_info.setWordWrap(True)
        ollama_layout.addRow(ollama_info)
        
        layout.addWidget(self.ollama_group)
        
        # ===== CONFIGURACIÓN CLOUDFLARE =====
        self.cloudflare_group = QGroupBox("☁️ Configuración de Cloudflare Workers AI")
        cloudflare_layout = QFormLayout(self.cloudflare_group)
        
        self.cloudflare_account_id = QLineEdit()
        self.cloudflare_account_id.setPlaceholderText("Ej: 8f296c9441738764c450954bfbcbc543")
        cloudflare_layout.addRow("Account ID:", self.cloudflare_account_id)
        
        self.cloudflare_api_token = QLineEdit()
        self.cloudflare_api_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.cloudflare_api_token.setPlaceholderText("Tu API Token de Cloudflare")
        cloudflare_layout.addRow("API Token:", self.cloudflare_api_token)
        
        self.cloudflare_model = QComboBox()
        self.cloudflare_model.addItems([
            "@cf/mistral/mistral-7b-instruct-v0.1",
            "@cf/meta/llama-3-8b-instruct",
            "@cf/meta/llama-2-7b-chat-int8",
            "@cf/qwen/qwen1.5-7b-chat-awq"
        ])
        self.cloudflare_model.setToolTip("Modelo de IA a utilizar en Cloudflare Workers")
        cloudflare_layout.addRow("Modelo:", self.cloudflare_model)
        
        # Botón de test para Cloudflare
        self.test_cloudflare_btn = QPushButton("🔍 Test Cloudflare Connection")
        self.test_cloudflare_btn.clicked.connect(self._test_cloudflare_connection)
        cloudflare_layout.addRow(self.test_cloudflare_btn)
        
        cloudflare_info = QLabel("ℹ️ Obtén tus credenciales en: Cloudflare Dashboard → Workers & Pages → AI")
        cloudflare_info.setStyleSheet("color: #aaa; padding: 5px;")
        cloudflare_info.setWordWrap(True)
        cloudflare_layout.addRow(cloudflare_info)
        
        layout.addWidget(self.cloudflare_group)
        
        layout.addStretch()
        return widget
    
    def _on_provider_changed(self, index):
        """Maneja el cambio de proveedor de IA"""
        if index == 0:  # Ollama
            self.ollama_group.setVisible(True)
            self.cloudflare_group.setVisible(False)
        else:  # Cloudflare
            self.ollama_group.setVisible(False)
            self.cloudflare_group.setVisible(True)
    
    def _test_cloudflare_connection(self):
        """Prueba la conexión a Cloudflare Workers AI"""
        account_id = self.cloudflare_account_id.text().strip()
        api_token = self.cloudflare_api_token.text().strip()
        model = self.cloudflare_model.currentText()
        
        if not account_id or not api_token:
            QMessageBox.warning(
                self,
                "Validación",
                "Por favor ingresa el Account ID y API Token de Cloudflare"
            )
            return
        
        self.test_cloudflare_btn.setEnabled(False)
        self.test_cloudflare_btn.setText("Probando...")
        
        try:
            from models.ai_provider import CloudflareProvider
            
            provider = CloudflareProvider(account_id, api_token, model)
            
            if provider.is_available():
                QMessageBox.information(
                    self,
                    "✅ Conexión Exitosa",
                    f"Conectado a Cloudflare Workers AI correctamente.\n\n"
                    f"Modelo: {model}\n"
                    f"El servicio está disponible y listo para usar."
                )
            else:
                QMessageBox.critical(
                    self,
                    "❌ Error de Conexión",
                    "No se pudo conectar a Cloudflare Workers AI.\n\n"
                    "Verifica:\n"
                    "• Account ID correcto\n"
                    "• API Token válido con permisos de Workers AI\n"
                    "• Conexión a Internet activa"
                )
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Excepción al conectar:\n{str(e)}")
        
        finally:
            self.test_cloudflare_btn.setEnabled(True)
            self.test_cloudflare_btn.setText("🔍 Test Cloudflare Connection")

    
    def _load_current_settings(self):
        """Carga los ajustes actuales desde la BD"""
        try:
            # MT5
            account = self.db.get_setting('mt5_account', '')
            password = self.db.get_setting('mt5_password', '')
            server = self.db.get_setting('mt5_server', 'Deriv-Demo')
            
            if account:
                self.mt5_account_input.setText(str(account))
            if password:
                self.mt5_password_input.setText(password)
            
            idx = self.mt5_server_combo.findText(server)
            if idx >= 0:
                self.mt5_server_combo.setCurrentIndex(idx)
            
            # Algoritmo
            self.regression_period.setValue(self.db.get_setting('regression_period', 30))
            self.regression_threshold.setValue(self.db.get_setting('regression_threshold', 0.5))
            self.technical_period.setValue(self.db.get_setting('technical_period', 100))
            self.expert_consensus.setValue(self.db.get_setting('expert_consensus', 5))
            self.analysis_interval.setValue(self.db.get_setting('analysis_interval', 120))
            
            # Riesgo
            self.sl_synthetics.setValue(self.db.get_setting('sl_synthetics', 500))
            self.tp_synthetics.setValue(self.db.get_setting('tp_synthetics', 1000))
            self.sl_xauusd.setValue(self.db.get_setting('sl_xauusd', 300))
            self.tp_xauusd.setValue(self.db.get_setting('tp_xauusd', 600))
            self.min_confidence_ia.setValue(self.db.get_setting('min_confidence_ia', 70))
            self.enable_auto_trading.setChecked(self.db.get_setting('enable_auto_trading', True))
            
            # Money Management
            self.risk_percentage.setValue(self.db.get_setting('risk_percentage', 1.0))
            self.daily_profit_target.setValue(self.db.get_setting('daily_profit_target', 0))
            self.risk_reward_ratio.setValue(self.db.get_setting('risk_reward_ratio', 3.0))
            
            # Scalping
            self.scalper_mode.setChecked(self.db.get_setting('scalper_mode', False))
            self.max_spread_pips.setValue(self.db.get_setting('max_spread_pips', 10))
            self.enable_trailing_stop.setChecked(self.db.get_setting('enable_trailing_stop', False))
            self.trailing_activation.setValue(self.db.get_setting('trailing_activation', 300))  # Default 300 para Boom/Crash
            self.trailing_distance.setValue(self.db.get_setting('trailing_distance', 150))  # Default 150 para Boom/Crash
            
            # AI Provider
            ai_provider = self.db.get_setting('ai_provider', 'ollama')
            if ai_provider == 'cloudflare':
                self.ai_provider_combo.setCurrentIndex(1)
            else:
                self.ai_provider_combo.setCurrentIndex(0)
            
            # Ollama
            self.ollama_url.setText(self.db.get_setting('ollama_url', 'http://localhost:11434/api/generate'))
            model = self.db.get_setting('ollama_model', 'mistral')
            idx = self.ollama_model.findText(model)
            if idx >= 0:
                self.ollama_model.setCurrentIndex(idx)
            self.enable_ia.setChecked(self.db.get_setting('enable_ia', True))
            
            # Cloudflare
            self.cloudflare_account_id.setText(self.db.get_setting('cloudflare_account_id', ''))
            self.cloudflare_api_token.setText(self.db.get_setting('cloudflare_api_token', ''))
            cf_model = self.db.get_setting('cloudflare_model', '@cf/mistral/mistral-7b-instruct-v0.1')
            idx = self.cloudflare_model.findText(cf_model)
            if idx >= 0:
                self.cloudflare_model.setCurrentIndex(idx)
            
            # Establecer visibilidad inicial de grupos
            self._on_provider_changed(self.ai_provider_combo.currentIndex())

            
            # Estado de conexión
            if self.mt5.is_connected():
                account_info = self.mt5.get_account_info()
                if account_info:
                    self.connection_status_label.setText(
                        f"🟢 Conectado (Cuenta: {account_info['account']})"
                    )
                    self.connection_status_label.setStyleSheet("color: #2ecc71; font-size: 12pt; font-weight: bold;")
            
            logger.info("Configuración actual cargada")
        
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
    
    def _test_mt5_connection(self):
        """Prueba la conexión a MT5 con las credenciales ingresadas"""
        # Validar inputs
        account = self.mt5_account_input.text()
        password = self.mt5_password_input.text()
        server = self.mt5_server_combo.currentText()
        
        is_valid, error = Validators.validate_account(account)
        if not is_valid:
            QMessageBox.warning(self, "Validación", error)
            return
        
        is_valid, error = Validators.validate_password(password)
        if not is_valid:
            QMessageBox.warning(self, "Validación", error)
            return
        
        # Intentar conexión
        self.test_connection_btn.setEnabled(False)
        self.test_connection_btn.setText("Probando...")
        
        try:
            success = self.mt5.connect(int(account), password, server)
            
            if success:
                account_info = self.mt5.get_account_info()
                QMessageBox.information(
                    self,
                    "✅ Conexión Exitosa",
                    f"Conectado a MT5 correctamente.\n\n"
                    f"Cuenta: {account_info['account']}\n"
                    f"Servidor: {account_info['server']}\n"
                    f"Balance: ${account_info['balance']:.2f}\n"
                    f"Equity: ${account_info['equity']:.2f}"
                )
                self.connection_status_label.setText(f"🟢 Conectado (Cuenta: {account})")
                self.connection_status_label.setStyleSheet("color: #2ecc71; font-size: 12pt; font-weight: bold;")
            else:
                QMessageBox.critical(
                    self,
                    "❌ Error de Conexión",
                    "No se pudo conectar a MT5.\n\n"
                    "Verifica:\n"
                    "• MetaTrader 5 esté abierto\n"
                    "• Credenciales correctas\n"
                    "• Servidor correcto"
                )
                self.connection_status_label.setText("⚫ Error al conectar")
                self.connection_status_label.setStyleSheet("color: #e74c3c; font-size: 12pt; font-weight: bold;")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Excepción al conectar:\n{str(e)}")
        
        finally:
            self.test_connection_btn.setEnabled(True)
            self.test_connection_btn.setText("🔍 Test Connection MT5")
    
    def _save_settings(self):
        """Guarda todos los ajustes en la BD"""
        try:
            # Recopilar todos los settings
            new_settings = {
                # MT5
                'mt5_account': int(self.mt5_account_input.text()) if self.mt5_account_input.text() else None,
                'mt5_password': self.mt5_password_input.text(),
                'mt5_server': self.mt5_server_combo.currentText(),
                
                # Algoritmo
                'regression_period': self.regression_period.value(),
                'regression_threshold': self.regression_threshold.value(),
                'technical_period': self.technical_period.value(),
                'expert_consensus': self.expert_consensus.value(),
                'analysis_interval': self.analysis_interval.value(),
                
                # Riesgo
                'sl_synthetics': self.sl_synthetics.value(),
                'tp_synthetics': self.tp_synthetics.value(),
                'sl_xauusd': self.sl_xauusd.value(),
                'tp_xauusd': self.tp_xauusd.value(),
                'min_confidence_ia': self.min_confidence_ia.value(),
                'enable_auto_trading': self.enable_auto_trading.isChecked(),
                
                # Money Management
                'risk_percentage': self.risk_percentage.value(),
                'daily_profit_target': self.daily_profit_target.value(),
                'risk_reward_ratio': self.risk_reward_ratio.value(),
                
                # Scalping
                'scalper_mode': self.scalper_mode.isChecked(),
                'max_spread_pips': self.max_spread_pips.value(),
                'enable_trailing_stop': self.enable_trailing_stop.isChecked(),
                'trailing_activation': self.trailing_activation.value(),
                'trailing_distance': self.trailing_distance.value(),
                
                # AI Provider
                'ai_provider': 'cloudflare' if self.ai_provider_combo.currentIndex() == 1 else 'ollama',
                
                # Ollama
                'ollama_url': self.ollama_url.text(),
                'ollama_model': self.ollama_model.currentText(),
                'enable_ia': self.enable_ia.isChecked(),
                
                # Cloudflare
                'cloudflare_account_id': self.cloudflare_account_id.text().strip(),
                'cloudflare_api_token': self.cloudflare_api_token.text().strip(),
                'cloudflare_model': self.cloudflare_model.currentText()
            }
            
            # Guardar en BD
            for key, value in new_settings.items():
                if value is not None:
                    self.db.save_setting(key, value)
            
            logger.info("✅ Configuración guardada exitosamente")
            
            # Emitir señal
            self.settings_saved.emit(new_settings)
            
            # Cerrar diálogo
            QMessageBox.information(
                self,
                "✅ Guardado",
                "Configuración guardada exitosamente.\n\n"
                "Los cambios se aplicarán dinámicamente a los workers activos."
            )
            
            self.accept()
        
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar la configuración:\n{str(e)}"
            )
