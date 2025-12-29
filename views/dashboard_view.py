"""
DashboardView - Vista principal con grid dinámico de SymbolCards.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                              QPushButton, QGridLayout, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, List
from views.symbol_card import SymbolCard


class DashboardView(QWidget):
    """
    Dashboard principal que muestra un grid dinámico de SymbolCards.
    
    Características:
    - Grid responsivo que se adapta al tamaño de ventana
    - Scroll automático cuando hay muchos cards
    - Botón "Agregar Símbolo"
    - Gestión dinámica de cards
    
    Señales:
    - add_symbol_clicked: Cuando se presiona agregar símbolo
    - symbol_play_clicked: Cuando se presiona play en un símbolo
    - symbol_stop_clicked: Cuando se presiona stop en un símbolo
    """
    
    # Señales
    add_symbol_clicked = pyqtSignal()
    clear_all_clicked = pyqtSignal()  # Señal para limpiar todos los símbolos
    symbol_play_clicked = pyqtSignal(str)  # symbol
    symbol_stop_clicked = pyqtSignal(str)  # symbol
    symbol_delete_clicked = pyqtSignal(str)  # symbol
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: Dict[str, SymbolCard] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz del dashboard"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # ==================== HEADER ====================
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 Trading Dashboard")
        title.setStyleSheet("""
            font-size: 18pt;
            font-weight: bold;
            color: #4ecca3;
            padding: 10px;
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Botón Limpiar Todo
        self.clear_all_button = QPushButton("🗑️ Limpiar Todo")
        self.clear_all_button.setObjectName("ClearAllButton")
        self.clear_all_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_all_button.setMinimumHeight(45)
        self.clear_all_button.clicked.connect(self.clear_all_clicked.emit)
        
        header_layout.addWidget(self.clear_all_button)
        
        # Botón Agregar Símbolo
        self.add_button = QPushButton("➕ Agregar Símbolo")
        self.add_button.setObjectName("AddSymbolButton")
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.setMinimumHeight(45)
        self.add_button.clicked.connect(self.add_symbol_clicked.emit)
        
        header_layout.addWidget(self.add_button)
        
        main_layout.addLayout(header_layout)
        
        # ==================== SCROLL AREA CON GRID ====================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget contenedor del grid
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        # Mensaje cuando no hay símbolos
        self.empty_message = QLabel("No hay símbolos agregados.\nPresiona '➕ Agregar Símbolo' para comenzar.")
        self.empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_message.setStyleSheet("""
            font-size: 14pt;
            color: #aaa;
            padding: 50px;
        """)
        self.grid_layout.addWidget(self.empty_message, 0, 0, Qt.AlignmentFlag.AlignCenter)
        
        scroll.setWidget(self.grid_container)
        main_layout.addWidget(scroll)
    
    def add_symbol_card(self, symbol: str) -> SymbolCard:
        """
        Agrega un nuevo SymbolCard al grid.
        
        Args:
            symbol: Nombre del símbolo
            
        Returns:
            SymbolCard creado
        """
        # Si ya existe, no crear duplicado
        if symbol in self._cards:
            return self._cards[symbol]
        
        # Ocultar mensaje de vacío si es el primer card
        if len(self._cards) == 0:
            self.empty_message.hide()
        
        # Crear card
        card = SymbolCard(symbol)
        
        # Conectar señales del card
        card.play_clicked.connect(self.symbol_play_clicked.emit)
        card.stop_clicked.connect(self.symbol_stop_clicked.emit)
        card.delete_clicked.connect(self.symbol_delete_clicked.emit)
        
        # Agregar al grid (3 columnas responsivas)
        num_cards = len(self._cards)
        row = num_cards // 3
        col = num_cards % 3
        
        self.grid_layout.addWidget(card, row, col)
        
        # Guardarlo
        self._cards[symbol] = card
        
        return card
    
    def remove_symbol_card(self, symbol: str):
        """
        Remueve un SymbolCard del grid.
        
        Args:
            symbol: Nombre del símbolo a remover
        """
        if symbol not in self._cards:
            return
        
        card = self._cards[symbol]
        
        # Remover del layout
        self.grid_layout.removeWidget(card)
        card.deleteLater()
        
        # Remover del diccionario
        del self._cards[symbol]
        
        # Reorganizar el grid
        self._reorganize_grid()
        
        # Si no quedan cards, mostrar mensaje
        if len(self._cards) == 0:
            self.empty_message.show()
    
    def _reorganize_grid(self):
        """Reorganiza el grid después de remover un card"""
        # Remover todos los widgets del layout
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget and widget != self.empty_message:
                self.grid_layout.removeWidget(widget)
        
        # Re-agregar en orden
        for idx, (symbol, card) in enumerate(self._cards.items()):
            row = idx // 3
            col = idx % 3
            self.grid_layout.addWidget(card, row, col)
    
    def get_card(self, symbol: str) -> SymbolCard:
        """
        Obtiene el card de un símbolo.
        
        Args:
            symbol: Nombre del símbolo
            
        Returns:
            SymbolCard o None si no existe
        """
        return self._cards.get(symbol)
    
    def get_all_symbols(self) -> List[str]:
        """Retorna lista de todos los símbolos en el dashboard"""
        return list(self._cards.keys())
    
    def clear(self):
        """Remueve todos los cards"""
        for symbol in list(self._cards.keys()):
            self.remove_symbol_card(symbol)
