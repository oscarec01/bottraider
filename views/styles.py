"""
Estilos QSS modernos para la aplicación de trading.
Inspirados en diseños modernos con tema oscuro.
"""


DARK_THEME = """
/* ==================== VARIABLES ==================== */
/* Paleta de colores moderna */

/* ==================== GENERAL ==================== */
QMainWindow {
    background-color: #1a1a2e;
}

QWidget {
    color: #eee;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

/* ==================== MENU BAR ==================== */
QMenuBar {
    background-color: #16213e;
    border-bottom: 2px solid #0f3460;
    padding: 5px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 8px 15px;
    margin: 2px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #0f3460;
}

QMenuBar::item:pressed {
    background-color: #533483;
}

QMenu {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 6px;
    padding: 5px;
}

QMenu::item {
    padding: 8px 25px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #0f3460;
}

/* ==================== TOOLBAR ==================== */
QToolBar {
    background-color: #16213e;
    border: none;
    spacing: 5px;
    padding: 5px;
}

QToolButton {
    background-color: #0f3460;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    color: #eee;
    font-weight: bold;
}

QToolButton:hover {
    background-color: #533483;
}

QToolButton:pressed {
    background-color: #8b4789;
}

/* ==================== SCROLL AREA ==================== */
QScrollArea {
    border: none;
    background-color: #1a1a2e;
}

QScrollBar:vertical {
    background-color: #16213e;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #0f3460;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #533483;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ==================== SYMBOL CARD (QFrame) ==================== */
QFrame#SymbolCard {
    background-color: #16213e;
    border: 2px solid #0f3460;
    border-radius: 12px;
    padding: 15px;
}

QFrame#SymbolCard:hover {
    border-color: #533483;
    background-color: #1a2332;
}

/* ==================== LABELS ==================== */
QLabel#SymbolName {
    color: #eee;
    font-size: 14pt;
    font-weight: bold;
}

QLabel#PriceLabel {
    color: #4ecca3;
    font-size: 16pt;
    font-weight: bold;
    font-family: 'Consolas', 'Courier New', monospace;
}

QLabel#StatusLabel {
    color: #aaa;
    font-size: 9pt;
    font-style: italic;
}

QLabel#ConfidenceLabel {
    color: #ffd700;
    font-size: 10pt;
}

/* ==================== BUTTONS ==================== */
QPushButton {
    background-color: #0f3460;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    color: #eee;
    font-weight: bold;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #533483;
}

QPushButton:pressed {
    background-color: #8b4789;
}

QPushButton:disabled {
    background-color: #2a2a3e;
    color: #666;
}

/* Botón Play (verde) */
QPushButton#PlayButton {
    background-color: #27ae60;
    color: white;
}

QPushButton#PlayButton:hover {
    background-color: #2ecc71;
}

/* Botón Stop (rojo) */
QPushButton#StopButton {
    background-color: #c0392b;
    color: white;
}

QPushButton#StopButton:hover {
    background-color: #e74c3c;
}

/* Botón Add Symbol */
QPushButton#AddSymbolButton {
    background-color: #533483;
    padding: 15px 30px;
    font-size: 12pt;
}

QPushButton#AddSymbolButton:hover {
    background-color: #8b4789;
}

/* Botón Clear All */
QPushButton#ClearAllButton {
    background-color: #d35400;
    padding: 15px 30px;
    font-size: 12pt;
}

QPushButton#ClearAllButton:hover {
    background-color: #e67e22;
}


/* ==================== PROGRESS BAR ==================== */
QProgressBar {
    border: 2px solid #0f3460;
    border-radius: 6px;
    text-align: center;
    background-color: #1a1a2e;
    color: #eee;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #4ecca3;
    border-radius: 4px;
}

/* ==================== LED INDICATOR ==================== */
QLabel#LEDIndicator {
    border-radius: 8px;
    min-width: 16px;
    max-width: 16px;
    min-height: 16px;
    max-height: 16px;
}

/* Estados del LED */
QLabel#LEDRunning {
    background-color: #2ecc71;
    border: 2px solid #27ae60;
}

QLabel#LEDPaused {
    background-color: #f39c12;
    border: 2px solid #e67e22;
}

QLabel#LEDStopped {
    background-color: #7f8c8d;
    border: 2px solid #95a5a6;
}

QLabel#LEDError {
    background-color: #e74c3c;
    border: 2px solid #c0392b;
}

/* ==================== STATUS BAR ==================== */
QStatusBar {
    background-color: #16213e;
    border-top: 2px solid #0f3460;
    color: #aaa;
    padding: 5px;
}

QStatusBar::item {
    border: none;
}

/* ==================== DIALOGS ==================== */
QDialog {
    background-color: #1a1a2e;
}

/* ==================== TAB WIDGET ==================== */
QTabWidget::pane {
    border: 2px solid #0f3460;
    border-radius: 6px;
    background-color: #16213e;
}

QTabBar::tab {
    background-color: #0f3460;
    color: #eee;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #533483;
}

QTabBar::tab:hover {
    background-color: #1a3a5a;
}

/* ==================== LINE EDIT ==================== */
QLineEdit {
    background-color: #0f3460;
    border: 2px solid #16213e;
    border-radius: 6px;
    padding: 8px;
    color: #eee;
    selection-background-color: #533483;
}

QLineEdit:focus {
    border-color: #533483;
}

QLineEdit:disabled {
    background-color: #2a2a3e;
    color: #666;
}

/* ==================== SPIN BOX ==================== */
QSpinBox, QDoubleSpinBox {
    background-color: #0f3460;
    border: 2px solid #16213e;
    border-radius: 6px;
    padding: 8px;
    color: #eee;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #533483;
}

/* ==================== COMBO BOX ==================== */
QComboBox {
    background-color: #0f3460;
    border: 2px solid #16213e;
    border-radius: 6px;
    padding: 8px;
    color: #eee;
}

QComboBox:hover {
    border-color: #533483;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    border: 1px solid #0f3460;
    selection-background-color: #533483;
    color: #eee;
}

/* ==================== CHECK BOX ==================== */
QCheckBox {
    spacing: 8px;
    color: #eee;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #0f3460;
    background-color: #1a1a2e;
}

QCheckBox::indicator:checked {
    background-color: #533483;
    border-color: #8b4789;
}

/* ==================== TEXT EDIT / PLAIN TEXT EDIT ==================== */
QTextEdit, QPlainTextEdit {
    background-color: #0f1419;
    border: 2px solid #0f3460;
    border-radius: 6px;
    color: #eee;
    font-family: 'Consolas', 'Courier New', monospace;
    padding: 8px;
}

/* ==================== TABLE ==================== */
QTableWidget {
    background-color: #16213e;
    alternate-background-color: #1a2332;
    border: 2px solid #0f3460;
    border-radius: 6px;
    gridline-color: #0f3460;
}

QTableWidget::item {
    padding: 8px;
    color: #eee;
}

QTableWidget::item:selected {
    background-color: #533483;
}

QHeaderView::section {
    background-color: #0f3460;
    color: #eee;
    padding: 10px;
    border: none;
    font-weight: bold;
}

/* ==================== TOOLTIP ==================== */
QToolTip {
    background-color: #16213e;
    color: #eee;
    border: 2px solid #533483;
    border-radius: 6px;
    padding: 5px;
}
"""


LIGHT_THEME = """
/* Tema claro disponible para futuras implementaciones */
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    color: #333;
}
"""


def get_theme(theme_name: str = "dark") -> str:
    """
    Retorna el stylesheet del tema especificado.
    
    Args:
        theme_name: 'dark' o 'light'
        
    Returns:
        QString con el stylesheet
    """
    if theme_name.lower() == "light":
        return LIGHT_THEME
    return DARK_THEME
