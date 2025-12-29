"""
Views package - Interfaz de usuario PyQt6
"""

from .main_window import MainWindow
from .dashboard_view import DashboardView
from .symbol_card import SymbolCard
from .settings_dialog import SettingsDialog
from .history_dialog import HistoryDialog

# Placeholders (no importar hasta que estén implementados)
# from .logs_panel import LogsPanel
# from .add_symbol_dialog import AddSymbolDialog

__all__ = [
    'MainWindow',
    'DashboardView',
    'SymbolCard',
    'SettingsDialog',
    'HistoryDialog',
    # 'LogsPanel',
    # 'AddSymbolDialog'
]
