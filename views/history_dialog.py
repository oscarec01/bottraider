"""
HistoryDialog - Visor de historial de análisis y operaciones.
Muestra razonamiento detallado del algoritmo y permite exportar a CSV.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                              QWidget, QTableWidget, QTableWidgetItem, QPushButton,
                              QLabel, QComboBox, QMessageBox, QFileDialog,
                              QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from models.database import Database
from utils.logger import get_logger
import csv
from datetime import datetime

logger = get_logger(__name__)


class HistoryDialog(QDialog):
    """
    Diálogo para ver historial de:
    - Análisis (razonamientos del algoritmo)
    - Trades ejecutados
    - Errores
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Historial y Razonamiento")
        self.setMinimumSize(1200, 700)
        
        # Usar Database wrapper
        self.db = Database()
        
        # Estilo para tablas (Dark Mode Fix)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #0f1419;
                color: #ffffff;
                gridline-color: #333333;
                selection-background-color: #4ecca3;
                selection-color: #000000;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #4ecca3;
                padding: 5px;
                border: 1px solid #333333;
            }
        """)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Configura la interfaz"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 Historial de Análisis y Operaciones")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #4ecca3;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Filtro por símbolo
        filter_label = QLabel("Filtrar por símbolo:")
        header_layout.addWidget(filter_label)
        
        self.symbol_filter = QComboBox()
        self.symbol_filter.addItem("Todos")
        self.symbol_filter.currentTextChanged.connect(self._apply_filter)
        header_layout.addWidget(self.symbol_filter)
        
        # Botón exportar
        self.export_btn = QPushButton("📥 Exportar a CSV")
        self.export_btn.setObjectName("PlayButton")
        self.export_btn.clicked.connect(self._export_to_csv)
        header_layout.addWidget(self.export_btn)
        
        # Botón refresh
        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_analysis_tab(), "🧠 Razonamiento del Algoritmo")
        self.tabs.addTab(self._create_trades_tab(), "💰 Operaciones Ejecutadas")
        self.tabs.addTab(self._create_errors_tab(), "❌ Historial de Errores")
        
        layout.addWidget(self.tabs)
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _create_analysis_tab(self):
        """Crea la pestaña de análisis con razonamiento"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Descripción
        desc = QLabel("📋 Cada fila muestra el razonamiento completo del algoritmo (5 pasos)")
        desc.setStyleSheet("color: #aaa; padding: 10px;")
        layout.addWidget(desc)
        
        # Tabla
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(9)
        self.analysis_table.setHorizontalHeaderLabels([
            "Timestamp",
            "Símbolo",
            "Paso 2: Regresión",
            "Paso 3: Panel",
            "Paso 4: IA",
            "Paso 5: Veredicto",
            "Acción Final",
            "Confianza",
            "Razonamiento"
        ])
        
        # Configurar tabla
        self.analysis_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.analysis_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.analysis_table.setAlternatingRowColors(True)
        self.analysis_table.horizontalHeader().setStretchLastSection(True)
        
        # Ajustar columnas
        header = self.analysis_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.analysis_table)
        
        return widget
    
    def _create_trades_tab(self):
        """Crea la pestaña de operaciones"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tabla
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(10)
        self.trades_table.setHorizontalHeaderLabels([
            "Apertura",
            "Símbolo",
            "Tipo",
            "Precio Entrada",
            "SL",
            "TP",
            "Lote",
            "Ticket",
            "Estado",
            "Profit"
        ])
        
        self.trades_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.trades_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.trades_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.trades_table)
        
        return widget
    
    def _create_errors_tab(self):
        """Crea la pestaña de errores"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tabla
        self.errors_table = QTableWidget()
        self.errors_table.setColumnCount(4)
        self.errors_table.setHorizontalHeaderLabels([
            "Timestamp",
            "Símbolo",
            "Tipo de Error",
            "Mensaje"
        ])
        
        self.errors_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.errors_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.errors_table.setAlternatingRowColors(True)
        self.errors_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.errors_table)
        
        return widget
    
    def _load_data(self):
        """Carga todos los datos desde la BD"""
        # IMPORTANTE: Bloquear señales para evitar loop infinito
        self.symbol_filter.blockSignals(True)
        
        try:
            # Cargar análisis
            try:
                self._load_analysis_data()
            except Exception as e:
                print(f"Error cargando análisis: {e}")
                self.analysis_table.setRowCount(0)
            
            # Cargar trades
            try:
                self._load_trades_data()
            except Exception as e:
                print(f"Error cargando trades: {e}")
                self.trades_table.setRowCount(0)
            
            # Cargar errores
            try:
                self._load_errors_data()
            except Exception as e:
                print(f"Error cargando errores: {e}")
                self.errors_table.setRowCount(0)
            
            # Actualizar filtro de símbolos (SOLO UNA VEZ)
            try:
                self._update_symbol_filter()
            except Exception as e:
                print(f"Error actualizando filtro: {e}")
        
        except Exception as e:
            print(f"Error general cargando datos de historial: {e}")
        
        finally:
            # Restaurar señales
            self.symbol_filter.blockSignals(False)
    
    def _load_analysis_data(self):
        """Carga el historial de análisis"""
        try:
            analyses = self.db.get_analysis_history(limit=200)
            
            if len(analyses) == 0:
                print("⚠️ No hay análisis en la base de datos")
                return
            
            self.analysis_table.setRowCount(len(analyses))
            
            for row, analysis in enumerate(analyses):
                try:
                    # Timestamp
                    timestamp = analysis.get('timestamp', 'N/A')
                    self.analysis_table.setItem(row, 0, QTableWidgetItem(str(timestamp)))
                    
                    # Símbolo
                    self.analysis_table.setItem(row, 1, QTableWidgetItem(str(analysis.get('symbol', 'N/A'))))
                    
                    # Parsear details JSON para obtener todos los pasos
                    import json
                    
                    details = analysis.get('details', '{}')
                    action = analysis.get('action', 'N/A')  
                    confidence = analysis.get('confidence', 0)
                    
                    # Extraer reasoning y datos de pasos desde details
                    try:
                        analysis_data = json.loads(details) if details else {}
                        
                        # Paso 2
                        paso2 = analysis_data.get('paso2', {})
                        paso2_text = f"{paso2.get('tendencia', 'N/A')} ({paso2.get('confianza', 0)}%)"
                        
                        # Paso 3
                        paso3 = analysis_data.get('paso3', {})
                        paso3_text = f"{paso3.get('veredicto_matematico', 'N/A')} ({paso3.get('confianza_matematica', 0)}%)"
                        
                        # Paso 4
                        paso4 = analysis_data.get('paso4', {})
                        paso4_text = f"{paso4.get('recommendation', paso4.get('decision', 'N/A'))} ({paso4.get('confianza', 0)}%)"
                        
                        # Paso 5
                        paso5 = analysis_data.get('paso5', {})
                        paso5_text = paso5.get('decision', 'N/A')
                        
                        # Reasoning
                        reasoning = paso5.get('reasoning', analysis_data.get('reasoning', 'N/A'))
                        
                    except (json.JSONDecodeError, Exception) as e:
                        paso2_text = 'Error parsing'
                        paso3_text = 'Error parsing'
                        paso4_text = 'Error parsing'
                        paso5_text = 'Error parsing'
                        reasoning = f'Error: {str(e)}'
                    
                    # Agregar a tabla
                    self.analysis_table.setItem(row, 2, QTableWidgetItem(paso2_text))
                    self.analysis_table.setItem(row, 3, QTableWidgetItem(paso3_text))
                    self.analysis_table.setItem(row, 4, QTableWidgetItem(paso4_text))
                    self.analysis_table.setItem(row, 5, QTableWidgetItem(paso5_text))
                    
                    # Acción Final
                    action_item = QTableWidgetItem(action)
                    
                    # Colorear según acción
                    if action == 'COMPRA':
                        action_item.setForeground(QColor('#2ecc71'))
                        action_item.setFont(QFont('Arial', 10, QFont.Weight.Bold))
                    elif action == 'VENTA':
                        action_item.setForeground(QColor('#e74c3c'))
                        action_item.setFont(QFont('Arial', 10, QFont.Weight.Bold))
                    else:
                        action_item.setForeground(QColor('#f39c12'))
                    
                    self.analysis_table.setItem(row, 6, action_item)
                    
                    # Confianza
                    conf_item = QTableWidgetItem(f"{confidence}%")
                    self.analysis_table.setItem(row, 7, conf_item)
                    
                    # Razonamiento completo
                    reasoning_text = reasoning[:100] + '...' if len(str(reasoning)) > 100 else str(reasoning)
                    self.analysis_table.setItem(row, 8, QTableWidgetItem(reasoning_text))
                
                except Exception as row_err:
                    print(f"❌ Error procesando fila {row}: {row_err}")
                    continue
            
        except Exception as e:
            print(f"❌ CRÍTICO: Error en _load_analysis_data: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_trades_data(self):
        """Carga el historial de trades"""
        trades = self.db.get_trade_history(limit=200)
        
        self.trades_table.setRowCount(len(trades))
        
        for row, trade in enumerate(trades):
            self.trades_table.setItem(row, 0, QTableWidgetItem(str(trade['open_time'])))
            self.trades_table.setItem(row, 1, QTableWidgetItem(trade['symbol']))
            
            # Tipo (coloreado)
            trade_type = trade['trade_type']
            type_item = QTableWidgetItem(trade_type)
            if trade_type == 'COMPRA':
                type_item.setForeground(QColor('#2ecc71'))
            else:
                type_item.setForeground(QColor('#e74c3c'))
            type_item.setFont(QFont('Arial', 10, QFont.Weight.Bold))
            self.trades_table.setItem(row, 2, type_item)
            
            self.trades_table.setItem(row, 3, QTableWidgetItem(f"{trade['entry_price']:.5f}"))
            self.trades_table.setItem(row, 4, QTableWidgetItem(f"{trade['stop_loss']:.5f}"))
            self.trades_table.setItem(row, 5, QTableWidgetItem(f"{trade['take_profit']:.5f}"))
            self.trades_table.setItem(row, 6, QTableWidgetItem(str(trade['lot_size'])))
            self.trades_table.setItem(row, 7, QTableWidgetItem(str(trade['ticket'] or 'N/A')))
            
            # Estado
            status = trade['status']
            status_item = QTableWidgetItem(status)
            if status == 'OPEN':
                status_item.setForeground(QColor('#f39c12'))
            else:
                status_item.setForeground(QColor('#95a5a6'))
            self.trades_table.setItem(row, 8, status_item)
            
            # Profit
            profit = trade['profit'] or 0
            profit_item = QTableWidgetItem(f"${profit:.2f}")
            if profit > 0:
                profit_item.setForeground(QColor('#2ecc71'))
            elif profit < 0:
                profit_item.setForeground(QColor('#e74c3c'))
            self.trades_table.setItem(row, 9, profit_item)
    
    def _load_errors_data(self):
        """Carga el historial de errores"""
        errors = self.db.get_errors(limit=200)
        
        self.errors_table.setRowCount(len(errors))
        
        for row, error in enumerate(errors):
            self.errors_table.setItem(row, 0, QTableWidgetItem(str(error['timestamp'])))
            self.errors_table.setItem(row, 1, QTableWidgetItem(error['symbol'] or 'General'))
            self.errors_table.setItem(row, 2, QTableWidgetItem(error['error_type']))
            
            # Mensaje de error (en rojo)
            msg_item = QTableWidgetItem(error['error_message'])
            msg_item.setForeground(QColor('#e74c3c'))
            self.errors_table.setItem(row, 3, msg_item)
    
    def _update_symbol_filter(self):
        """Actualiza el combo de filtro con símbolos únicos"""
        symbols = self.db.get_active_symbols()
        
        current = self.symbol_filter.currentText()
        self.symbol_filter.clear()
        self.symbol_filter.addItem("Todos")
        
        for symbol_data in symbols:
            self.symbol_filter.addItem(symbol_data['symbol'])
        
        # Restaurar selección
        idx = self.symbol_filter.findText(current)
        if idx >= 0:
            self.symbol_filter.setCurrentIndex(idx)
    
    def _apply_filter(self):
        """Aplica filtro por símbolo"""
        try:
            symbol = self.symbol_filter.currentText()
            
            if symbol == "Todos":
                self._load_data()
            else:
                # Cargar solo el símbolo seleccionado
                self._load_filtered_data(symbol)
        except Exception as e:
            print(f"Error aplicando filtro: {e}")
    
    def _load_filtered_data(self, symbol: str):
        """Carga datos filtrados por símbolo"""
        try:
            # Análisis
            analyses = self.db.get_analysis_history(symbol=symbol, limit=200)
            self._populate_analysis_table(analyses)
            
            # Trades
            trades = self.db.get_trade_history(symbol=symbol, limit=200)
            self._populate_trades_table(trades)
        
        except Exception as e:
            logger.error(f"Error filtrando datos: {e}")
    
    def _populate_analysis_table(self, analyses):
        """Rellena la tabla de análisis con datos"""
        # Implementación similar a _load_analysis_data pero con datos filtrados
        pass
    
    def _populate_trades_table(self, trades):
        """Rellena la tabla de trades con datos"""
        # Implementación similar a _load_trades_data pero con datos filtrados
        pass
    
    def _export_to_csv(self):
        """Exporta el historial a CSV"""
        current_tab = self.tabs.currentIndex()
        
        # Seleccionar archivo
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Historial a CSV",
            f"historial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            if current_tab == 0:  # Análisis
                self._export_analysis_csv(filename)
            elif current_tab == 1:  # Trades
                self._export_trades_csv(filename)
            elif current_tab == 2:  # Errores
                self._export_errors_csv(filename)
            
            QMessageBox.information(
                self,
                "✅ Exportado",
                f"Historial exportado exitosamente a:\n{filename}"
            )
            
            logger.info(f"Historial exportado a {filename}")
        
        except Exception as e:
            logger.error(f"Error exportando a CSV: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo exportar:\n{str(e)}")
    
    def _export_analysis_csv(self, filename: str):
        """Exporta tabla de análisis a CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Headers
            headers = []
            for col in range(self.analysis_table.columnCount()):
                headers.append(self.analysis_table.horizontalHeaderItem(col).text())
            writer.writerow(headers)
            
            # Datos
            for row in range(self.analysis_table.rowCount()):
                row_data = []
                for col in range(self.analysis_table.columnCount()):
                    item = self.analysis_table.item(row, col)
                    row_data.append(item.text() if item else '')
                writer.writerow(row_data)
    
    def _export_trades_csv(self, filename: str):
        """Exporta tabla de trades a CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            headers = []
            for col in range(self.trades_table.columnCount()):
                headers.append(self.trades_table.horizontalHeaderItem(col).text())
            writer.writerow(headers)
            
            for row in range(self.trades_table.rowCount()):
                row_data = []
                for col in range(self.trades_table.columnCount()):
                    item = self.trades_table.item(row, col)
                    row_data.append(item.text() if item else '')
                writer.writerow(row_data)
    
    def _export_errors_csv(self, filename: str):
        """Exporta tabla de errores a CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            headers = []
            for col in range(self.errors_table.columnCount()):
                headers.append(self.errors_table.horizontalHeaderItem(col).text())
            writer.writerow(headers)
            
            for row in range(self.errors_table.rowCount()):
                row_data = []
                for col in range(self.errors_table.columnCount()):
                    item = self.errors_table.item(row, col)
                    row_data.append(item.text() if item else '')
                writer.writerow(row_data)
