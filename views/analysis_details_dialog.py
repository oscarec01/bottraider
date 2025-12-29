"""
AnalysisDetailsDialog - Diálogo que muestra análisis detallado.
Muestra los 9 expertos del panel técnico individualmente.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QScrollArea, QWidget, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class AnalysisDetailsDialog(QDialog):
    """
    Diálogo que muestra el desglose completo del análisis:
    - Identificación del activo
    - Regresión lineal detallada
    - Panel de 9 expertos (individual)
    - Análisis de IA
    - Veredicto final
    """
    
    def __init__(self, analysis_data: dict, symbol: str, parent=None):
        super().__init__(parent)
        self.analysis_data = analysis_data
        self.symbol = symbol
        
        self.setWindowTitle(f"📊 Análisis Detallado: {symbol}")
        self.setMinimumSize(700, 600)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QLabel(f"Análisis Completo de {self.symbol}")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Área de scroll para el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # ==================== PASO 1: IDENTIFICACIÓN ====================
        self._add_section(content_layout, "PASO 1: Identificación del Activo", 
                         self._create_paso1_content())
        
        # ==================== PASO 2: REGRESIÓN LINEAL ====================
        self._add_section(content_layout, "PASO 2: Regresión Lineal (30 días H1)", 
                         self._create_paso2_content())
        
        # ==================== PASO 3: PANEL DE EXPERTOS ====================
        self._add_section(content_layout, "PASO 3: Panel de Expertos Técnicos (M5)", 
                         self._create_paso3_content())
        
        # ==================== PASO 4: ANÁLISIS IA ====================
        self._add_section(content_layout, "PASO 4: Análisis de IA", 
                         self._create_paso4_content())
        
        # ==================== PASO 5: VEREDICTO FINAL ====================
        self._add_section(content_layout, "PASO 5: Veredicto Final Consolidado", 
                         self._create_paso5_content())
        
        # ==================== PASO 6: PRONÓSTICO FUTURO ====================
        self._add_section(content_layout, "PASO 6: PRONÓSTICO FUTURO (Próximos 15 min)", 
                         self._create_paso6_content())
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _add_section(self, layout, title, content_widget):
        """Agrega una sección con título y contenido"""
        # Frame contenedor
        section_frame = QFrame()
        section_frame.setObjectName("SectionFrame")
        section_frame.setStyleSheet("""
            QFrame#SectionFrame {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        section_layout = QVBoxLayout(section_frame)
        section_layout.setSpacing(10)
        
        # Título de sección
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #3498db; padding-bottom: 5px;")
        section_layout.addWidget(title_label)
        
        # Contenido
        section_layout.addWidget(content_widget)
        
        layout.addWidget(section_frame)
    
    def _create_paso1_content(self):
        """Crea contenido del Paso 1"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        paso1 = self.analysis_data.get('paso1', {})
        
        self._add_info_row(layout, "Símbolo:", self.symbol)
        self._add_info_row(layout, "Tipo de Activo:", paso1.get('asset_type', 'N/A'))
        self._add_info_row(layout, "Mercado:", paso1.get('market', 'N/A'))
        self._add_info_row(layout, "Timestamp:", paso1.get('timestamp', 'N/A'))
        
        return widget
    
    def _create_paso2_content(self):
        """Crea contenido del Paso 2 - Regresión"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        paso2 = self.analysis_data.get('paso2', {})
        
        tendencia = paso2.get('tendencia', 'N/A')
        confianza = paso2.get('confianza', 0)
        recomendacion = paso2.get('recomendacion', 'N/A')
        
        # Color según tendencia
        color = self._get_signal_color(tendencia)
        
        self._add_info_row(layout, "Tendencia:", tendencia, color)
        self._add_info_row(layout, "Confianza R²:", f"{confianza}%")
        self._add_info_row(layout, "Recomendación:", recomendacion, self._get_signal_color(recomendacion))
        
        return widget
    
    def _create_paso3_content(self):
        """Crea contenido del Paso 3 - Panel de Expertos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        paso3 = self.analysis_data.get('paso3', {})
        experts = paso3.get('experts', {})
        
        # Mostrar cada experto
        expert_names = {
            'RSI': f"RSI ({paso3.get('rsi', 'N/A')})",
            'EMA_CROSS': "EMA Cross (4 EMAs)",
            'MACD': f"MACD ({paso3.get('macd', 'N/A')})",
            'BOLLINGER': "Bandas de Bollinger",
            'HEIKIN_ASHI': f"Heikin Ashi ({paso3.get('heikin_ashi', 'N/A')})",
            'STOCHASTIC': f"Estocástico ({paso3.get('stoch_k', 'N/A')})",
            'MICRO_SR': "Micro Soporte/Resistencia",
            'VOLATILITY': "Análisis de Volatilidad",
            'VOLUME': "Análisis de Volumen"
        }
        
        for i, (key, name) in enumerate(expert_names.items(), 1):
            signal = experts.get(key, 'N/A')
            color = self._get_signal_color(signal)
            self._add_info_row(layout, f"[E{i}] {name}:", signal, color, bold_value=True)
        
        # Separador
        layout.addWidget(self._create_separator())
        
        # Conteo de votos
        buys = sum(1 for v in experts.values() if v == "COMPRA")
        sells = sum(1 for v in experts.values() if v == "VENTA")
        waits = sum(1 for v in experts.values() if v == "ESPERAR")
        
        votes_label = QLabel(f"Votos: COMPRA={buys}, VENTA={sells}, ESPERAR={waits}")
        votes_label.setStyleSheet("font-weight: bold; color: #95a5a6;")
        layout.addWidget(votes_label)
        
        # Veredicto del panel
        veredicto = paso3.get('veredicto_matematico', 'N/A')
        confianza = paso3.get('confianza_matematica', 0)
        
        veredicto_text = f"{veredicto} ({confianza}%)"
        self._add_info_row(layout, "═► VEREDICTO PANEL:", veredicto_text, 
                          self._get_signal_color(veredicto), bold_value=True)
        
        return widget
    
    def _create_paso4_content(self):
        """Crea contenido del Paso 4 - IA"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        paso4 = self.analysis_data.get('paso4', {})
        
        senal = paso4.get('señal', 'N/A')
        confianza = paso4.get('confianza', 0)
        razon = paso4.get('razon', 'N/A')
        
        self._add_info_row(layout, "Señal IA:", senal, self._get_signal_color(senal))
        self._add_info_row(layout, "Confianza IA:", f"{confianza}%")
        
        # Razón en múltiples líneas
        razon_label = QLabel("Razón:")
        razon_label.setStyleSheet("color: #aaa; font-size: 9pt;")
        layout.addWidget(razon_label)
        
        razon_value = QLabel(razon)
        razon_value.setWordWrap(True)
        razon_value.setStyleSheet("color: #ecf0f1; font-size: 9pt; padding-left: 10px;")
        layout.addWidget(razon_value)
        
        return widget
    
    def _create_paso5_content(self):
        """Crea contenido del Paso 5 - Veredicto Final"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        final_action = self.analysis_data.get('final_action', 'ESPERAR')
        confidence = self.analysis_data.get('confidence', 0)
        reasoning = self.analysis_data.get('reasoning', 'N/A')
        
        self._add_info_row(layout, "ACCIÓN FINAL:", f">>> {final_action} <<<", 
                          self._get_signal_color(final_action), bold_value=True, large=True)
        self._add_info_row(layout, "Confianza Final:", f"{confidence}%", large=True)
        
        # Motivo en múltiples líneas
        motivo_label = QLabel("Motivo:")
        motivo_label.setStyleSheet("color: #aaa; font-size: 10pt; font-weight: bold;")
        layout.addWidget(motivo_label)
        
        motivo_value = QLabel(reasoning)
        motivo_value.setWordWrap(True)
        motivo_value.setStyleSheet("color: #ecf0f1; font-size: 10pt; padding-left: 10px;")
        layout.addWidget(motivo_value)
        
        return widget
    
    def _create_paso6_content(self):
        """Crea contenido del Paso 6 - Pronóstico Futuro"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        prediction = self.analysis_data.get('prediction', {})
        
        if prediction and prediction.get('prediction'):
            # Hay predicción
            self._add_info_row(layout, "📊 Predicción:", prediction.get('prediction', 'N/A'))
            self._add_info_row(layout, "🎯 Probabilidad:", f"{prediction.get('probability', 0)}%")
            self._add_info_row(layout, "💰 Precio Objetivo:", f"{prediction.get('target_price', 0)}")
            self._add_info_row(layout, "⏱️ Timeframe:", prediction.get('timeframe', 'N/A'))
            
            # Rationale en múltiples líneas
            rationale_label = QLabel("📝 Rationale:")
            rationale_label.setStyleSheet("color: #aaa; font-size: 9pt;")
            layout.addWidget(rationale_label)
            
            rationale_value = QLabel(prediction.get('rationale', 'N/A'))
            rationale_value.setWordWrap(True)
            rationale_value.setStyleSheet("color: #ecf0f1; font-size: 9pt; padding-left: 10px;")
            layout.addWidget(rationale_value)
            
            # Verificación de predicción anterior
            verification = self.analysis_data.get('prediction_verification', {})
            if verification.get('had_prediction'):
                layout.addWidget(self._create_separator())
                
                was_accurate = verification.get('was_accurate', False)
                adjustment = verification.get('confidence_adjustment', 0)
                
                status_text = "✅ ACERTADA" if was_accurate else "❌ FALLIDA"
                status_color = "#2ecc71" if was_accurate else "#e74c3c"
                
                self._add_info_row(layout, "📊 Predicción Anterior:", 
                                 f"{status_text} ({adjustment:+d}%)", 
                                 status_color, bold_value=True)
        else:
            # No hay predicción
            no_pred_label = QLabel("⚠️ No se generó predicción en este análisis")
            no_pred_label.setStyleSheet("color: #f39c12; font-size: 9pt; font-style: italic;")
            layout.addWidget(no_pred_label)
        
        return widget
    
    def _add_info_row(self, layout, label_text, value_text, color="#ecf0f1", bold_value=False, large=False):
        """Agrega una fila de información"""
        row_layout = QHBoxLayout()
        
        label = QLabel(label_text)
        font_size = "10pt" if large else "9pt"
        label.setStyleSheet(f"color: #aaa; font-size: {font_size};")
        
        value = QLabel(str(value_text))
        value_style = f"color: {color}; font-size: {font_size};"
        if bold_value:
            value_style += " font-weight: bold;"
        value.setStyleSheet(value_style)
        value.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        row_layout.addWidget(label)
        row_layout.addStretch()
        row_layout.addWidget(value)
        
        layout.addLayout(row_layout)
    
    def _create_separator(self):
        """Crea una línea separadora"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #444; max-height: 1px;")
        return line
    
    def _get_signal_color(self, signal):
        """Retorna color según la señal"""
        signal_upper = str(signal).upper()
        
        if 'COMPRA' in signal_upper or 'ALCISTA' in signal_upper:
            return '#2ecc71'  # Verde
        elif 'VENTA' in signal_upper or 'BAJISTA' in signal_upper:
            return '#e74c3c'  # Rojo
        elif 'ESPERAR' in signal_upper or 'NEUTRAL' in signal_upper or 'NEUTRO' in signal_upper:
            return '#f39c12'  # Amarillo
        else:
            return '#ecf0f1'  # Blanco/gris
