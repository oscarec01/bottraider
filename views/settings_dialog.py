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
        self.expert_consensus.setRange(3, 12)
        self.expert_consensus.setValue(5)
        self.expert_consensus.setSuffix(" de 12")
        technical_layout.addRow("Consenso Requerido:", self.expert_consensus)
        
        layout.addWidget(technical_group)
        
        # Intervalo de análisis
        interval_group = QGroupBox("Frecuencia de Análisis")
        interval_layout = QFormLayout(interval_group)
        
        self.analysis_interval = QSpinBox()
        self.analysis_interval.setRange(8, 600)
        self.analysis_interval.setValue(10)
        self.analysis_interval.setSuffix(" segundos")
        self.analysis_interval.setToolTip(
            "En modo frecuencia/volátil se usa 8–15s (sin IA). Fuera de frecuencia puede ser mayor."
        )
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

        self.confidence_threshold = QSpinBox()
        self.confidence_threshold.setRange(40, 90)
        self.confidence_threshold.setValue(55)
        self.confidence_threshold.setSuffix(" %")
        self.confidence_threshold.setToolTip("Umbral de confianza final del setup para ejecutar")
        confidence_layout.addRow("Umbral Setup Final:", self.confidence_threshold)

        self.min_setup_score = QSpinBox()
        self.min_setup_score.setRange(40, 90)
        self.min_setup_score.setValue(55)
        self.min_setup_score.setSuffix(" pts")
        self.min_setup_score.setToolTip("Calidad mínima del setup (Boom dip / Crash rally / Trend)")
        confidence_layout.addRow("Score Mínimo Setup:", self.min_setup_score)
        
        self.enable_auto_trading = QCheckBox("Ejecutar trades automáticamente")
        self.enable_auto_trading.setChecked(True)
        confidence_layout.addRow("Auto-Trading:", self.enable_auto_trading)

        self.capital_preservation = QCheckBox(
            "Modo NO PERDER: solo setups muy claros (puede estar horas sin operar)"
        )
        self.capital_preservation.setChecked(False)
        self.capital_preservation.setToolTip(
            "Prioriza no perder: umbrales altos, bloquea señales conflictivas, "
            "máximo 1 posición en la cuenta. Anula la agresividad del modo frecuencia."
        )
        confidence_layout.addRow("Capital first:", self.capital_preservation)

        self.use_atr_stops = QCheckBox("SL adaptativo por ATR (recomendado)")
        self.use_atr_stops.setChecked(True)
        confidence_layout.addRow("Stops ATR:", self.use_atr_stops)
        
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
        self.risk_reward_ratio.setValue(2.0)
        self.risk_reward_ratio.setSingleStep(0.5)
        self.risk_reward_ratio.setDecimals(1)
        self.risk_reward_ratio.setPrefix("1:")
        self.risk_reward_ratio.setToolTip("1:2 es más realista en M5 que 1:3 con SL amplios")
        money_layout.addRow("Ratio Riesgo:Beneficio:", self.risk_reward_ratio)

        self.max_daily_loss = QSpinBox()
        self.max_daily_loss.setRange(0, 10000)
        self.max_daily_loss.setValue(0)
        self.max_daily_loss.setSuffix(" USD")
        self.max_daily_loss.setSpecialValueText("Sin límite")
        self.max_daily_loss.setToolTip("Si la pérdida del día alcanza este valor, no abre más trades")
        money_layout.addRow("Pérdida Diaria Máxima:", self.max_daily_loss)
        
        layout.addWidget(money_group)
        
        # Scalping & Protección
        scalping_group = QGroupBox("📈 Scalping Avanzado")
        scalping_layout = QFormLayout(scalping_group)
        
        self.frequency_scalp_mode = QCheckBox(
            "Modo FRECUENCIA: muchas ops + proteger ganancias"
        )
        self.frequency_scalp_mode.setChecked(False)
        self.frequency_scalp_mode.setToolTip(
            "Ciclos cortos. Al ganar lo suficiente asegura con SL y deja correr."
        )
        scalping_layout.addRow("Modo Frecuencia:", self.frequency_scalp_mode)

        self.let_winners_run = QCheckBox(
            "Dejar correr ganancias (no cerrar al primer $; asegurar SL y trail)"
        )
        self.let_winners_run.setChecked(True)
        self.let_winners_run.setToolTip(
            "Si vas ganando: mueve SL a break-even+ y deja la op abierta. "
            "Solo cierra si no se puede asegurar por reglas del broker."
        )
        scalping_layout.addRow("Dejar correr:", self.let_winners_run)

        self.micro_profit_usd = QDoubleSpinBox()
        self.micro_profit_usd.setRange(0.001, 50.0)
        self.micro_profit_usd.setDecimals(3)
        self.micro_profit_usd.setSingleStep(0.1)
        self.micro_profit_usd.setValue(0.5)
        self.micro_profit_usd.setPrefix("$ ")
        self.micro_profit_usd.setToolTip(
            "Cerrar en cuanto el profit flotante >= este valor. "
            "Nota: con lote mínimo 1.0 en V100, $0.001 casi nunca es alcanzable "
            "por el tamaño del tick; usa 0.10–0.50 en la práctica."
        )
        scalping_layout.addRow("Micro ganancia:", self.micro_profit_usd)

        self.micro_loss_usd = QDoubleSpinBox()
        self.micro_loss_usd.setRange(0.0, 100.0)
        self.micro_loss_usd.setDecimals(3)
        self.micro_loss_usd.setSingleStep(0.1)
        self.micro_loss_usd.setValue(0.0)
        self.micro_loss_usd.setPrefix("$ ")
        self.micro_loss_usd.setSpecialValueText("OFF (usar solo SL broker)")
        self.micro_loss_usd.setToolTip(
            "0 = NO cortar pérdidas automáticamente (recomendado). "
            "Un corte a -$1 en Boom cerraba todo en rojo y reentraba peor."
        )
        scalping_layout.addRow("Micro pérdida (corte):", self.micro_loss_usd)

        self.max_trade_seconds = QSpinBox()
        self.max_trade_seconds.setRange(10, 600)
        self.max_trade_seconds.setValue(90)
        self.max_trade_seconds.setSuffix(" s")
        scalping_layout.addRow("Máx. tiempo por trade:", self.max_trade_seconds)

        self.scalper_mode = QCheckBox("Enfoque exclusivo en últimos 15 minutos M5")
        self.scalper_mode.setChecked(False)
        scalping_layout.addRow("Modo Scalper (M5):", self.scalper_mode)
        
        self.max_spread_pips = QSpinBox()
        self.max_spread_pips.setRange(1, 500)
        self.max_spread_pips.setValue(50)
        self.max_spread_pips.setSuffix(" pts")
        self.max_spread_pips.setToolTip(
            "Solo Forex/XAUUSD. En Boom/Crash/Volatility se usa % del precio."
        )
        scalping_layout.addRow("Spread Máx (Forex pts):", self.max_spread_pips)

        self.max_spread_pct = QDoubleSpinBox()
        self.max_spread_pct.setRange(0.05, 2.0)
        self.max_spread_pct.setValue(0.25)
        self.max_spread_pct.setSingleStep(0.05)
        self.max_spread_pct.setDecimals(2)
        self.max_spread_pct.setSuffix(" %")
        self.max_spread_pct.setToolTip(
            "Sintéticos Deriv: rechaza si (ask-bid)/precio > este %. "
            "Boom 1000 normal ~0.01%; Crash/V75 ~0.03–0.05%."
        )
        scalping_layout.addRow("Spread Máx (Sintéticos %):", self.max_spread_pct)
        
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
        self.ai_provider_combo.addItems([
            "Ollama (Local)",
            "Cloudflare Workers AI",
            "OpenRouter",
        ])
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

        # ===== CONFIGURACIÓN OPENROUTER =====
        self.openrouter_group = QGroupBox("OpenRouter (recomendada si Cloudflare falla)")
        openrouter_layout = QFormLayout(self.openrouter_group)

        self.openrouter_api_key = QLineEdit()
        self.openrouter_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openrouter_api_key.setPlaceholderText("sk-or-v1-...")
        openrouter_layout.addRow("API Key:", self.openrouter_api_key)

        self.openrouter_model = QComboBox()
        self.openrouter_model.setEditable(True)
        self.openrouter_model.addItems([
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "google/gemini-2.0-flash-001",
            "anthropic/claude-3.5-sonnet",
            "meta-llama/llama-3.1-8b-instruct",
        ])
        openrouter_layout.addRow("Modelo:", self.openrouter_model)

        self.test_openrouter_btn = QPushButton("Test OpenRouter")
        self.test_openrouter_btn.clicked.connect(self._test_openrouter_connection)
        openrouter_layout.addRow(self.test_openrouter_btn)

        openrouter_info = QLabel(
            "API: https://openrouter.ai/api/v1/chat/completions — "
            "gpt-4o-mini es más barato; gpt-4o más capaz."
        )
        openrouter_info.setStyleSheet("color: #aaa; padding: 5px;")
        openrouter_info.setWordWrap(True)
        openrouter_layout.addRow(openrouter_info)

        layout.addWidget(self.openrouter_group)
        
        layout.addStretch()
        return widget
    
    def _on_provider_changed(self, index):
        """Maneja el cambio de proveedor de IA"""
        self.ollama_group.setVisible(index == 0)
        self.cloudflare_group.setVisible(index == 1)
        self.openrouter_group.setVisible(index == 2)

    def _test_openrouter_connection(self):
        """Prueba la conexión a OpenRouter"""
        api_key = self.openrouter_api_key.text().strip()
        model = self.openrouter_model.currentText().strip()
        if not api_key:
            QMessageBox.warning(self, "Validación", "Ingresa la API Key de OpenRouter")
            return

        self.test_openrouter_btn.setEnabled(False)
        self.test_openrouter_btn.setText("Probando...")
        try:
            from models.ai_provider import OpenRouterProvider
            provider = OpenRouterProvider(api_key, model)
            text = provider.query(
                'Responde SOLO este JSON: {"ok": true, "provider": "openrouter"}',
                timeout=45,
                format_json=True,
            )
            if text:
                QMessageBox.information(
                    self,
                    "Conexion Exitosa",
                    f"OpenRouter OK.\nModelo: {model}\nRespuesta:\n{text[:300]}",
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "OpenRouter no respondio. Revisa API key, creditos y modelo.",
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Excepcion:\n{e}")
        finally:
            self.test_openrouter_btn.setEnabled(True)
            self.test_openrouter_btn.setText("Test OpenRouter")
    
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
            self.confidence_threshold.setValue(self.db.get_setting('confidence_threshold', 55))
            self.min_setup_score.setValue(self.db.get_setting('min_setup_score', 55))
            self.enable_auto_trading.setChecked(self.db.get_setting('enable_auto_trading', True))
            self.capital_preservation.setChecked(
                self.db.get_setting('capital_preservation', False)
            )
            self.use_atr_stops.setChecked(self.db.get_setting('use_atr_stops', True))
            
            # Money Management
            self.risk_percentage.setValue(self.db.get_setting('risk_percentage', 1.0))
            self.daily_profit_target.setValue(self.db.get_setting('daily_profit_target', 0))
            self.risk_reward_ratio.setValue(self.db.get_setting('risk_reward_ratio', 2.0))
            self.max_daily_loss.setValue(self.db.get_setting('max_daily_loss', 0))
            
            # Scalping / frecuencia
            self.frequency_scalp_mode.setChecked(
                self.db.get_setting('frequency_scalp_mode', False)
            )
            self.let_winners_run.setChecked(
                self.db.get_setting('let_winners_run', True)
            )
            self.micro_profit_usd.setValue(
                float(self.db.get_setting('micro_profit_usd', 0.5))
            )
            self.micro_loss_usd.setValue(
                float(self.db.get_setting('micro_loss_usd', 1.0))
            )
            self.max_trade_seconds.setValue(
                int(self.db.get_setting('max_trade_seconds', 90))
            )
            self.scalper_mode.setChecked(self.db.get_setting('scalper_mode', False))
            self.max_spread_pips.setValue(self.db.get_setting('max_spread_pips', 50))
            self.max_spread_pct.setValue(self.db.get_setting('max_spread_pct', 0.25))
            self.enable_trailing_stop.setChecked(self.db.get_setting('enable_trailing_stop', False))
            self.trailing_activation.setValue(self.db.get_setting('trailing_activation', 300))  # Default 300 para Boom/Crash
            self.trailing_distance.setValue(self.db.get_setting('trailing_distance', 150))  # Default 150 para Boom/Crash
            
            # AI Provider
            ai_provider = self.db.get_setting('ai_provider', 'ollama')
            provider_idx = {'ollama': 0, 'cloudflare': 1, 'openrouter': 2}.get(ai_provider, 0)
            self.ai_provider_combo.setCurrentIndex(provider_idx)
            
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

            # OpenRouter
            self.openrouter_api_key.setText(self.db.get_setting('openrouter_api_key', ''))
            or_model = self.db.get_setting('openrouter_model', 'openai/gpt-4o-mini')
            idx = self.openrouter_model.findText(or_model)
            if idx >= 0:
                self.openrouter_model.setCurrentIndex(idx)
            else:
                self.openrouter_model.setEditText(or_model)
            
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
                'confidence_threshold': (
                    max(self.confidence_threshold.value(), 65)
                    if self.capital_preservation.isChecked()
                    else self.confidence_threshold.value()
                ),
                'min_setup_score': (
                    max(self.min_setup_score.value(), 70)
                    if self.capital_preservation.isChecked()
                    else self.min_setup_score.value()
                ),
                'enable_auto_trading': self.enable_auto_trading.isChecked(),
                'max_total_positions': (
                    1 if (
                        self.capital_preservation.isChecked()
                        and not self.frequency_scalp_mode.isChecked()
                    ) else 3
                ),
                'use_atr_stops': self.use_atr_stops.isChecked(),
                
                # Money Management
                'risk_percentage': (
                    min(self.risk_percentage.value(), 0.5)
                    if self.capital_preservation.isChecked()
                    else self.risk_percentage.value()
                ),
                'daily_profit_target': self.daily_profit_target.value(),
                'risk_reward_ratio': self.risk_reward_ratio.value(),
                'max_daily_loss': self.max_daily_loss.value(),
                
                # Scalping / frecuencia
                # Si activan frecuencia volátil, apaga "no perder" (son opuestos)
                'frequency_scalp_mode': self.frequency_scalp_mode.isChecked(),
                'capital_preservation': (
                    False if self.frequency_scalp_mode.isChecked()
                    else self.capital_preservation.isChecked()
                ),
                'let_winners_run': self.let_winners_run.isChecked(),
                'micro_profit_usd': self.micro_profit_usd.value(),
                'micro_loss_usd': self.micro_loss_usd.value(),
                'max_trade_seconds': self.max_trade_seconds.value(),
                'frequency_skip_ia': True,
                'scalper_mode': self.scalper_mode.isChecked(),
                'max_spread_pips': self.max_spread_pips.value(),
                'max_spread_pct': self.max_spread_pct.value(),
                'enable_trailing_stop': (
                    True if self.let_winners_run.isChecked()
                    else self.enable_trailing_stop.isChecked()
                ),
                'trailing_activation': self.trailing_activation.value(),
                'trailing_distance': self.trailing_distance.value(),
                'max_loss_streak': 2 if self.capital_preservation.isChecked() else 3,
                'loss_streak_cooldown_sec': (
                    900 if self.capital_preservation.isChecked() else 300
                ),
                
                # AI Provider
                'ai_provider': {0: 'ollama', 1: 'cloudflare', 2: 'openrouter'}.get(
                    self.ai_provider_combo.currentIndex(), 'ollama'
                ),
                
                # Ollama
                'ollama_url': self.ollama_url.text(),
                'ollama_model': self.ollama_model.currentText(),
                'enable_ia': self.enable_ia.isChecked(),
                
                # Cloudflare
                'cloudflare_account_id': self.cloudflare_account_id.text().strip(),
                'cloudflare_api_token': self.cloudflare_api_token.text().strip(),
                'cloudflare_model': self.cloudflare_model.currentText(),

                # OpenRouter
                'openrouter_api_key': self.openrouter_api_key.text().strip(),
                'openrouter_model': self.openrouter_model.currentText().strip(),
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
