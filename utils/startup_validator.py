"""
Startup Validator - Verifica que todos los servicios estén listos antes de iniciar.

Este módulo valida:
- Conexión a MetaTrader 5
- Servicio Ollama
- Base de datos
- Configuración válida
"""

import sys
import requests
from typing import Tuple, Dict, List
from utils.logger import get_logger

logger = get_logger(__name__)


class StartupValidator:
    """Validador de estado del sistema antes de iniciar la aplicación."""
    
    def __init__(self):
        self.mt5 = None
        self.db = None
        self.validation_results: Dict[str, bool] = {}
        
    def validate_all(self) -> Tuple[bool, List[str]]:
        """
        Ejecuta todas las validaciones de startup.
        
        Returns:
            (all_valid, error_messages)
        """
        errors = []
        
        # 1. Validar MT5
        logger.info("Validando conexión MT5...")
        mt5_valid, mt5_msg = self._validate_mt5()
        self.validation_results['mt5'] = mt5_valid
        if not mt5_valid:
            errors.append(f"❌ MT5: {mt5_msg}")
        else:
            logger.info(f"✅ MT5: {mt5_msg}")
        
        # 2. Validar Ollama
        logger.info("Validando servicio Ollama...")
        ollama_valid, ollama_msg = self._validate_ollama()
        self.validation_results['ollama'] = ollama_valid
        if not ollama_valid:
            errors.append(f"⚠️  Ollama: {ollama_msg} (Opcional, pero recomendado)")
        else:
            logger.info(f"✅ Ollama: {ollama_msg}")
        
        # 3. Validar Base de Datos
        logger.info("Validando base de datos...")
        db_valid, db_msg = self._validate_database()
        self.validation_results['database'] = db_valid
        if not db_valid:
            errors.append(f"❌ Database: {db_msg}")
        else:
            logger.info(f"✅ Database: {db_msg}")
        
        # 4. Validar Configuración
        logger.info("Validando configuración...")
        config_valid, config_msg = self._validate_config()
        self.validation_results['config'] = config_valid
        if not config_valid:
            errors.append(f"⚠️  Config: {config_msg}")
        else:
            logger.info(f"✅ Config: {config_msg}")
        
        # Determinar si todo es válido (MT5 y DB son críticos)
        all_valid = mt5_valid and db_valid
        
        return all_valid, errors
    
    def _validate_mt5(self) -> Tuple[bool, str]:
        """Valida que MT5 esté disponible y conectado."""
        try:
            import MetaTrader5 as mt5
            
            # Inicializar
            if not mt5.initialize():
                return False, "No se pudo inicializar MT5. ¿Está MetaTrader abierto?"
            
            # Verificar información de cuenta
            account_info = mt5.account_info()
            if account_info is None:
                return False, "MT5 inicializado pero no conectado a cuenta"
            
            # Shutdown para liberar recursos (se reconectará después)
            mt5.shutdown()
            
            return True, f"Conectado a cuenta {account_info.login}"
        
        except ImportError:
            return False, "Módulo MetaTrader5 no instalado (pip install MetaTrader5)"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _validate_ollama(self) -> Tuple[bool, str]:
        """Valida que Ollama esté corriendo."""
        try:
            import config
            ollama_url = getattr(config, 'OLLAMA_URL', 'http://localhost:11434/api/generate')
            
            # Intentar conexión a endpoint de versión
            version_url = ollama_url.replace('/api/generate', '/api/version')
            
            response = requests.get(version_url, timeout=3)
            
            if response.status_code == 200:
                version_data = response.json()
                version = version_data.get('version', 'unknown')
                return True, f"Servicio activo (v{version})"
            else:
                return False, f"Servicio responde con código {response.status_code}"
        
        except requests.ConnectionError:
            return False, "No se pudo conectar. Ejecuta 'ollama serve' en terminal"
        except requests.Timeout:
            return False, "Timeout al conectar a Ollama"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _validate_database(self) -> Tuple[bool, str]:
        """Valida que la base de datos sea accesible y tenga estructura correcta."""
        try:
            from models.database import Database
            
            db = Database()
            
            # Verificar que tablas existan
            conn = db._get_connection()
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            
            tables = {row['name'] for row in cursor.fetchall()}
            
            required_tables = {
                'analysis_log',
                'symbols',
                'trade_history',
                'settings',
                'execution_errors'
            }
            
            missing = required_tables - tables
            
            if missing:
                return False, f"Faltan tablas: {', '.join(missing)}"
            
            # Verificar que analysis_log tenga columnas de predicción
            cursor = conn.execute("PRAGMA table_info(analysis_log)")
            columns = {row['name'] for row in cursor.fetchall()}
            
            required_columns = {
                'prediction',
                'prediction_accuracy',
                'prediction_adjustment'
            }
            
            missing_cols = required_columns - columns
            
            if missing_cols:
                return False, f"analysis_log falta columnas: {', '.join(missing_cols)}. Ejecuta migración."
            
            return True, "Base de datos válida con estructura v2.0"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _validate_config(self) -> Tuple[bool, str]:
        """Valida que config.py tenga los valores necesarios."""
        try:
            import config
            
            # Verificar credenciales MT5
            if not hasattr(config, 'MT5_ACCOUNT') or config.MT5_ACCOUNT == 0:
                return False, "MT5_ACCOUNT no configurado en config.py"
            
            if not hasattr(config, 'MT5_PASSWORD') or config.MT5_PASSWORD == "":
                return False, "MT5_PASSWORD no configurado en config.py"
            
            if not hasattr(config, 'MT5_SERVER') or config.MT5_SERVER == "":
                return False, "MT5_SERVER no configurado en config.py"
            
            # Verificar Ollama
            if not hasattr(config, 'OLLAMA_URL'):
                return False, "OLLAMA_URL no configurado en config.py"
            
            if not hasattr(config, 'OLLAMA_MODEL'):
                return False, "OLLAMA_MODEL no configurado en config.py"
            
            return True, "Configuración completa"
        
        except ImportError:
            return False, "No se pudo importar config.py"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_validation_summary(self) -> str:
        """Retorna resumen de validaciones en formato texto."""
        summary_lines = []
        summary_lines.append("=" * 60)
        summary_lines.append("         VALIDACIÓN DE STARTUP")
        summary_lines.append("=" * 60)
        
        for service, is_valid in self.validation_results.items():
            status = "✅" if is_valid else "❌"
            summary_lines.append(f"{status} {service.upper():15} {'OK' if is_valid else 'FAILED'}")
        
        summary_lines.append("=" * 60)
        
        return "\n".join(summary_lines)


def validate_startup() -> bool:
    """
    Función de utilidad para validar startup desde main.py.
    
    Returns:
        True si todo está listo, False si hay errores críticos
    """
    validator = StartupValidator()
    all_valid, errors = validator.validate_all()
    
    print(validator.get_validation_summary())
    
    if errors:
        print("\n⚠️  ERRORES ENCONTRADOS:")
        for error in errors:
            print(f"  {error}")
        print()
    
    if not all_valid:
        print("❌ No se puede continuar. Corrige los errores críticos.")
        return False
    
    if validator.validation_results.get('ollama', False) is False:
        print("\n⚠️  ADVERTENCIA: Ollama no disponible.")
        print("   El bot funcionará con capacidades limitadas (sin IA).")
        print("   Para habilitar IA, ejecuta: ollama serve\n")
    
    print("✅ Validación exitosa. Sistema listo para iniciar.\n")
    return True


if __name__ == "__main__":
    """Permite ejecutar validación independientemente."""
    import sys
    
    if not validate_startup():
        sys.exit(1)
    
    print("Puedes iniciar la aplicación con: python main.py")
