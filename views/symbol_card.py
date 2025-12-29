"""
SymbolCard - Widget tipo Card para cada símbolo de trading.
Muestra precio actual, estado, botón Play/Stop e indicador LED.
"""

from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QProgressBar, QWidget, QDialog,
                              QTextEdit, QVBoxLayout as QVBoxLayout2, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QFont, QMouseEvent
from typing import Optional, List, Dict, Any


class SymbolCard(QFrame):
    """
    Widget tipo Card que representa un símbolo de trading.
    
    Componentes:
    - Nombre del símbolo
    - Indicador LED de estado
    - Precio actual (actualizado en tiempo real)
    - Última señal (COMPRA/VENTA/ESPERAR)
    - Confianza (%)
    - Barra de progreso
    - Botón Play/Stop
    
    Señales:
    - play_clicked: Cuando se presiona Play
    - stop_clicked: Cuando se presiona Stop
    - delete_clicked: Cuando se presiona el botón X
    """
    
    # Señales personalizadas
    play_clicked = pyqtSignal(str)  # symbol
    stop_clicked = pyqtSignal(str)  # symbol
    delete_clicked = pyqtSignal(str)  # symbol
    
    def __init__(self, symbol: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.symbol = symbol
        self._is_running = False
        self._current_price = 0.0
        self._last_signal = "---"
        self._confidence = 0
        self._full_analysis: Optional[Dict[str, Any]] = None  # Análisis completo
        
        # Historial de errores (últimos 50)
        self._error_history: List[dict] = []
        self._current_error = None
        
        self.setObjectName("SymbolCard")
        self.setMinimumSize(280, 200)
        self.setMaximumWidth(350)
        
        # Habilitar doble clic
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Configura la interfaz del card"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ==================== HEADER (Nombre + LED) ====================
        header_layout = QHBoxLayout()
        
        # Nombre del símbolo
        self.name_label = QLabel(self.symbol)
        self.name_label.setObjectName("SymbolName")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.name_label.setFont(font)
        
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()
        
        # LED Indicator
        self.led_indicator = QLabel()
        self.led_indicator.setObjectName("LEDIndicator")
        self.led_indicator.setToolTip("Estado del análisis")
        self._update_led_state("stopped")
        header_layout.addWidget(self.led_indicator)
        
        # TODO: Botón X - Reimplementar sin CSS inline
        header_layout.addWidget(self.led_indicator)
        
        layout.addLayout(header_layout)
        
        # ==================== PRECIO ====================
        price_layout = QHBoxLayout()
        
        price_label_text = QLabel("Precio:")
        price_label_text.setStyleSheet("color: #aaa; font-size: 9pt;")
        
        self.price_value = QLabel("---")
        self.price_value.setObjectName("PriceLabel")
        self.price_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        price_layout.addWidget(price_label_text)
        price_layout.addStretch()
        price_layout.addWidget(self.price_value)
        
        layout.addLayout(price_layout)
        
        # ==================== ÚLTIMA SEÑAL ====================
        signal_layout = QHBoxLayout()
        
        signal_label_text = QLabel("Última señal:")
        signal_label_text.setStyleSheet("color: #aaa; font-size: 9pt;")
        
        self.signal_value = QLabel("---")
        self.signal_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.signal_value.setStyleSheet("font-weight: bold; font-size: 11pt;")
        
        signal_layout.addWidget(signal_label_text)
        signal_layout.addStretch()
        signal_layout.addWidget(self.signal_value)
        
        layout.addLayout(signal_layout)
        
        # ==================== CONFIANZA ====================
        conf_layout = QHBoxLayout()
        
        conf_label_text = QLabel("Confianza:")
        conf_label_text.setStyleSheet("color: #aaa; font-size: 9pt;")
        
        self.confidence_value = QLabel("0%")
        self.confidence_value.setObjectName("ConfidenceLabel")
        self.confidence_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        conf_layout.addWidget(conf_label_text)
        conf_layout.addStretch()
        conf_layout.addWidget(self.confidence_value)
        
        layout.addLayout(conf_layout)
        
        # ==================== PANEL DE EXPERTOS ====================
        panel_layout = QHBoxLayout()
        
        panel_label_text = QLabel("Panel Expertos:")
        panel_label_text.setStyleSheet("color: #aaa; font-size: 9pt;")
        
        self.panel_value = QLabel("---")
        self.panel_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.panel_value.setStyleSheet("font-size: 9pt;")
        
        panel_layout.addWidget(panel_label_text)
        panel_layout.addStretch()
        panel_layout.addWidget(self.panel_value)
        
        layout.addLayout(panel_layout)
        
        # ==================== REGRESIÓN LINEAL ====================
        regression_layout = QHBoxLayout()
        
        regression_label_text = QLabel("Regresión Lineal:")
        regression_label_text.setStyleSheet("color: #aaa; font-size: 9pt;")
        
        self.regression_value = QLabel("---")
        self.regression_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.regression_value.setStyleSheet("font-size: 9pt;")
        
        regression_layout.addWidget(regression_label_text)
        regression_layout.addStretch()
        regression_layout.addWidget(self.regression_value)
        
        layout.addLayout(regression_layout)
        
        # ==================== PREDICCIÓN ANTERIOR (Sistema de Aprendizaje) ====================
        self.prediction_label = QLabel("🔮 Predicción Anterior: Pendiente")
        self.prediction_label.setWordWrap(True)
        self.prediction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prediction_label.setStyleSheet("color: #7f8c8d; font-size: 10px; font-weight: bold; padding: 8px; margin: 5px; border-radius: 4px; background-color: rgba(127, 140, 141, 0.1);")
        layout.addWidget(self.prediction_label)
        
        # ==================== BOTÓN VER DETALLES ====================
        self.details_button = QPushButton("📊 Ver Detalles")
        self.details_button.setObjectName("DetailsButton")
        self.details_button.setMinimumHeight(30)
        self.details_button.setStyleSheet("""
            QPushButton#DetailsButton {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #2c3e50;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton#DetailsButton:hover {
                background-color: #3498db;
            }
        """)
        layout.addWidget(self.details_button)
        
        # ==================== BARRA DE PROGRESO ====================
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(6)
        
        layout.addWidget(self.progress_bar)
        
        # ==================== ESTADO ====================
        self.status_label = QLabel("Detenido")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        
        layout.addWidget(self.status_label)
        
        # ==================== BOTÓN PLAY/STOP ====================
        self.action_button = QPushButton("▶ Iniciar")
        self.action_button.setObjectName("PlayButton")
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_button.setMinimumHeight(40)
        
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.action_button.setFont(font)
        
        layout.addWidget(self.action_button)
        
        layout.addStretch()
    
    def _connect_signals(self):
        """Conecta las señales internas"""
        self.action_button.clicked.connect(self._on_action_button_clicked)
        self.details_button.clicked.connect(self._on_details_clicked)
        # self.delete_btn.clicked.connect(self._on_delete_clicked)  # TODO: Reimplementar
    
    def _on_action_button_clicked(self):
        """Maneja el clic en el botón de acción"""
        if self._is_running:
            self.stop_clicked.emit(self.symbol)
        else:
            self.play_clicked.emit(self.symbol)
    
    def _on_delete_clicked(self):
        """Maneja el clic en el botón X"""
        self.delete_clicked.emit(self.symbol)
    
    def _update_led_state(self, state: str):
        """
        Actualiza el indicador LED.
        
        Args:
            state: 'running', 'paused', 'stopped', 'error'
        """
        state_map = {
            'running': ('LEDRunning', '#2ecc71', 'Ejecutando'),
            'paused': ('LEDPaused', '#f39c12', 'Pausado'),
            'stopped': ('LEDStopped', '#7f8c8d', 'Detenido'),
            'error': ('LEDError', '#e74c3c', 'Error')
        }
        
        if state in state_map:
            object_name, color, tooltip = state_map[state]
            self.led_indicator.setObjectName(object_name)
            self.led_indicator.setToolTip(tooltip)
            # Forzar actualización de estilo
            self.led_indicator.style().unpolish(self.led_indicator)
            self.led_indicator.style().polish(self.led_indicator)
    
    # ==================== SLOTS PÚBLICOS ====================
    
    def set_running(self, running: bool):
        """
        Actualiza el estado de ejecución.
        
        Args:
            running: True si está corriendo
        """
        self._is_running = running
        
        if running:
            self.action_button.setText("⏹ Detener")
            self.action_button.setObjectName("StopButton")
            self._update_led_state("running")
        else:
            self.action_button.setText("▶ Iniciar")
            self.action_button.setObjectName("PlayButton")
            self._update_led_state("stopped")
        
        # Forzar actualización de estilo del botón
        self.action_button.style().unpolish(self.action_button)
        self.action_button.style().polish(self.action_button)
    
    def update_analysis(self, analysis_result: dict):
        """Actualiza la card con los resultados del análisis"""
        try:
            paso5 = analysis_result.get('paso5', {})
            action = paso5.get('decision', paso5.get('final_action', 'ESPERAR'))
            reasoning = paso5.get('razon', paso5.get('reasoning', 'Sin razón'))
            
            # Obtener confianza del paso 4
            paso4 = analysis_result.get('paso4', {})
            confidence_raw = paso4.get('confianza', 0)
            
            if isinstance(confidence_raw, str):
                confidence = int(''.join(filter(str.isdigit, confidence_raw)) or '0')
            else:
                confidence = int(confidence_raw)
            
            # Actualizar label de análisis
            signal_emoji = {
                "COMPRA": "📈",
                "VENTA": "📉",
                "ESPERAR": "⏸"
            }.get(action, "❓")
            signal = action # Assuming 'action' is the signal
            signal_colors = {
                "COMPRA": "#2ecc71",
                "VENTA": "#e74c3c",
                "ESPERAR": "#f39c12"
            }

            analysis_text = f"{signal_emoji} {signal}   Conf: {confidence}%"
            
            # ========== Agregar verificación de predicción anterior ==========
            verification = analysis_result.get('prediction_verification', {})
            
            if verification.get('had_prediction'):
                was_accurate = verification.get('was_accurate', False)
                adjustment = verification.get('confidence_adjustment', 0)
                
                if was_accurate:
                    self.prediction_label.setText(
                        f"🔮 Predicción Anterior: ✅ ACERTADA ({adjustment:+d}%)"
                    )
                    self.prediction_label.setStyleSheet("""
                        color: #2ecc71; 
                        background-color: rgba(46, 204, 113, 0.1);
                        padding: 8px; 
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 10px;
                        margin: 5px;
                    """)
                else:
                    self.prediction_label.setText(
                        f"🔮 Predicción Anterior: ❌ FALLIDA ({adjustment:+d}%)"
                    )
                    self.prediction_label.setStyleSheet("""
                        color: #e74c3c; 
                        background-color: rgba(231, 76, 60, 0.1);
                        padding: 8px; 
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 10px;
                        margin: 5px;
                    """)
            else:
                # Primera predicción
                self.prediction_label.setText("🔮 Predicción Anterior: Pendiente")
                self.prediction_label.setStyleSheet("""
                    color: #7f8c8d; 
                    background-color: rgba(127, 140, 141, 0.1);
                    padding: 8px; 
                    border-radius: 4px;
                    font-size: 10px;
                    margin: 5px;
                """)
            
            # Agregar predicción actual al texto
            prediction = analysis_result.get('prediction', {})
            if prediction and prediction.get('prediction'):
                pred_text = f"\n\n🎯 Pronóstico: {prediction.get('prediction', 'N/A')}"
                pred_text += f"\n   Probabilidad: {prediction.get('probability', 0)}%"
                pred_text += f"\n   Target: {prediction.get('target_price', 0)}"
                analysis_text += pred_text
            
            self.analysis_label.setText(analysis_text)
            self.analysis_label.setStyleSheet(f"color: {signal_colors.get(signal, '#7f8c8d')}; font-weight: bold; font-size: 12px;")
            
            # Actualizar acción con colores
            if action == "COMPRA":
                self.action_label.setText("📈 COMPRA")
                self.action_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 16px;")
            elif action == "VENTA":
                self.action_label.setText("📉 VENTA")
                self.action_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 16px;")
            else:
                self.action_label.setText("⏸ ESPERAR")
                self.action_label.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 16px;")
            
            # Actualizar confianza
            self.confidence_label.setText(f"Confianza: {confidence}%")
            
            # Actualizar razón
            self.analysis_label.setText(f"💭 {reasoning}")
            
            # ==================== ACTUALIZAR PREDICCIÓN ANTERIOR ====================
            verification = analysis_result.get('prediction_verification', {})
            
            if verification.get('had_prediction'):
                was_accurate = verification.get('was_accurate', False)
                adjustment = verification.get('confidence_adjustment', 0)
                
                if was_accurate:
                    self.prediction_label.setText(f"🔮 Predicción Anterior: ✅ ACERTADA ({adjustment:+d}%)")
                    self.prediction_label.setStyleSheet("color: #2ecc71; font-size: 11px; font-weight: bold; padding: 5px; background-color: rgba(46, 204, 113, 0.1); border-radius: 3px;")
                else:
                    self.prediction_label.setText(f"🔮 Predicción Anterior: ❌ FALLIDA ({adjustment:+d}%)")
                    self.prediction_label.setStyleSheet("color: #e74c3c; font-size: 11px; font-weight: bold; padding: 5px; background-color: rgba(231, 76, 60, 0.1); border-radius: 3px;")
            else:
                self.prediction_label.setText("🔮 Predicción Anterior: Pendiente")
                self.prediction_label.setStyleSheet("color: #7f8c8d; font-size: 11px; font-weight: bold; padding: 5px;")
            
            # ==================== MOSTRAR PREDICCIÓN ACTUAL ====================
            prediction = analysis_result.get('prediction')
            if prediction:
                pred_text = f"🎯 Pronóstico: {prediction.get('prediction', 'N/A')} "
                pred_text += f"({prediction.get('probability', 0)}% prob.) "
                pred_text += f"→ {prediction.get('target_price', 0)}"
                
                # Agregar a los detalles
                current_text = self.analysis_label.text()
                self.analysis_label.setText(f"{current_text}\n{pred_text}")
        
        except Exception as e:
            logger.error(f"Error actualizando análisis en card: {e}")
    
    def update_price(self, price: float):
        """
        Actualiza el precio mostrado.
        
        Args:
            price: Precio actual
        """
        self._current_price = price
        self.price_value.setText(f"{price:.5f}")
    
    def update_signal(self, signal: str, confidence: int = 0):
        """
        Actualiza la última señal y confianza.
        
        Args:
            signal: 'COMPRA', 'VENTA', 'ESPERAR'
            confidence: Confianza en % (ya viene como 0-100, no como 0-1)
        """
        self._last_signal = signal
        self._confidence = confidence
        
        # Actualizar label de señal con colores
        color_map = {
            'COMPRA': '#2ecc71',
            'VENTA': '#e74c3c',
            'ESPERAR': '#f39c12',
            '---': '#aaa'
        }
        
        color = color_map.get(signal, '#aaa')
        self.signal_value.setText(signal)
        self.signal_value.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11pt;")
        
        # Actualizar confianza
        # Fix: Manejar escalas incorrectas (ej: 5423 -> 54.23%)
        if confidence > 100:
            confidence = confidence / 100.0
            
        final_conf = min(confidence, 100.0)
        
        if final_conf > 0:
            formatted_conf = f"{round(final_conf, 1)}%"
        else:
            formatted_conf = "0%"
            
        self.confidence_value.setText(formatted_conf)
    
    def update_analysis_details(self, regression_text: str, panel_text: str, full_analysis: Optional[Dict[str, Any]] = None):
        """
        Actualiza los detalles del análisis (panel y regresión).
        
        Args:
            regression_text: Texto de regresión (ej: "ALCISTA (78%)")
            panel_text: Texto del panel (ej: "ALCISTA (67%)")
            full_analysis: Diccionario completo con todo el análisis (opcional)
        """
        # Guardar análisis completo
        if full_analysis:
            self._full_analysis = full_analysis
        
        # Colores según veredicto
        color_map = {
            'ALCISTA': '#2ecc71',
            'BAJISTA': '#e74c3c',
            'NEUTRAL': '#f39c12',
            'NEUTRO': '#f39c12'
        }
        
        # Panel de Expertos
        panel_color = '#aaa'
        for key, color in color_map.items():
            if key in panel_text.upper():
                panel_color = color
                break
        
        self.panel_value.setText(panel_text)
        self.panel_value.setStyleSheet(f"color: {panel_color}; font-size: 9pt;")
        
        # Regresión Lineal
        regression_color = '#aaa'
        for key, color in color_map.items():
            if key in regression_text.upper():
                regression_color = color
                break
        
        self.regression_value.setText(regression_text)
        self.regression_value.setStyleSheet(f"color: {regression_color}; font-size: 9pt;")
    
    def _on_details_clicked(self):
        """Maneja el clic en el botón Ver Detalles"""
        if not self._full_analysis:
            QMessageBox.information(self, "Sin datos", 
                                  "No hay análisis disponible todavía.\nEjecuta un análisis primero.")
            return
        
        # Importar aquí para evitar importación circular
        from views.analysis_details_dialog import AnalysisDetailsDialog
        
        dialog = AnalysisDetailsDialog(self._full_analysis, self.symbol, self)
        dialog.exec()
    
    def update_status(self, status: str):
        """
        Actualiza el mensaje de estado.
        
        Args:
            status: Mensaje de estado
        """
        self.status_label.setText(status)
    
    def update_progress(self, value: int):
        """
        Actualiza la barra de progreso.
        
        Args:
            value: Valor de 0-100
        """
        self.progress_bar.setValue(value)
    
    def set_error_state(self, error_msg: str, error_details: str = None):
        """
        Pone el card en estado de error.
        
        Args:
            error_msg: Mensaje de error (corto)
            error_details: Detalles completos del error (stack trace, etc.)
        """
        from datetime import datetime
        
        self._update_led_state("error")
        self.status_label.setText(f"❌ {error_msg}")
        self.status_label.setStyleSheet("color: #e74c3c;")
        
        # Guardar error en historial
        error_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': error_msg,
            'details': error_details or error_msg
        }
        
        self._error_history.insert(0, error_entry)  # Más reciente primero
        
        # Limitar a 50 errores
        if len(self._error_history) > 50:
            self._error_history = self._error_history[:50]
        
        # Guardar error actual
        self._current_error = error_entry
        
        # Tooltip indica doble clic
        self.setToolTip("🔴 Doble clic para ver detalles del error")
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """
        Maneja el doble clic en el card.
        Si hay errores, muestra un diálogo con el log de errores.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if self._error_history:
                self._show_error_dialog()
        
        super().mouseDoubleClickEvent(event)
    
    def _show_error_dialog(self):
        """Muestra un diálogo con el historial de errores del símbolo"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"❌ Errores de {self.symbol}")
        dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Header
        header = QLabel(f"Historial de Errores: {self.symbol}")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #e74c3c; padding: 10px;")
        layout.addWidget(header)
        
        # TextEdit con historial
        error_text = QTextEdit()
        error_text.setReadOnly(True)
        error_text.setStyleSheet("QTextEdit { background-color: #0f1419; color: #eee; font-family: 'Consolas', 'Courier New', monospace; font-size: 10pt; padding: 10px; }")
        
        # Construir texto con todos los errores
        error_log = f"Total de errores: {len(self._error_history)}\n"
        error_log += "=" * 70 + "\n\n"
        
        for idx, error in enumerate(self._error_history, 1):
            error_log += f"[{idx}] {error['timestamp']}\n"
            error_log += f"Mensaje: {error['message']}\n"
            error_log += f"Detalles:\n{error['details']}\n"
            error_log += "-" * 70 + "\n\n"
        
        error_text.setPlainText(error_log)
        layout.addWidget(error_text)
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def clear_errors(self):
        """Limpia el historial de errores"""
        self._error_history = []
        self._current_error = None
        self.setToolTip("")
    
    def reset(self):
        """Resetea el card a estado inicial"""
        self.update_price(0.0)
        self.update_signal("---", 0)
        self.update_analysis_details("---", "---")
        self.update_status("Detenido")
        self.update_progress(0)
        self.set_running(False)
        self.status_label.setStyleSheet("")
        self.clear_errors()
