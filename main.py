"""
🤖 Bot de Trading - Deriv Synthetic Indices
Aplicación PyQt6 con arquitectura MVC

Punto de entrada principal de la aplicación.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Configurar path para importar módulos
sys.path.insert(0, '.')

from views.main_window import MainWindow
from controllers.main_controller import MainController
from utils.logger import setup_logger, get_logger

# Configurar logging
setup_logger('TradingBot', 'trading_bot.log')
logger = get_logger(__name__)


def main():
    """Función principal de la aplicación"""
    logger.info("="*70)
    logger.info("🚀 INICIANDO BOT DE TRADING - PyQt6 MVC")
    logger.info("="*70)
    
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Bot de Trading")
    app.setOrganizationName("TradingBot")
    
    # PyQt6 maneja HiDPI automáticamente, no se requiere configuración adicional
    
    try:
        # Crear ventana principal
        logger.info("Creando ventana principal...")
        main_window = MainWindow()
        
        # Crear controlador principal
        logger.info("Inicializando controlador principal...")
        main_controller = MainController(main_window)
        
        # Mostrar ventana
        main_window.show()
        logger.info("✅ Aplicación iniciada correctamente")
        logger.info("="*70)
        
        # Ejecutar loop de la aplicación
        exit_code = app.exec()
        
        # Cleanup al salir
        logger.info("Cerrando aplicación...")
        main_controller.cleanup()
        logger.info("✅ Aplicación cerrada correctamente")
        
        return exit_code
    
    except Exception as e:
        logger.critical(f"❌ Error crítico al iniciar la aplicación: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
