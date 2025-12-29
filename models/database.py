"""
Database - Wrapper para gestión de BD SQLite.
Incluye métodos para análisis, trades, errores y configuración.
"""

import sqlite3
import json
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    """Gestión de base de datos SQLite con patrón Singleton thread-safe"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = "trading_bot.db"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = "trading_bot.db"):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.db_path = db_path
        self._conn_lock = threading.Lock()
        self._local = threading.local()
        self._initialize_database()
        self._initialized = True
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene conexión thread-local"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            self._local.conn.row_factory = sqlite3.Row
            # Habilitar WAL mode para mejor concurrencia
            self._local.conn.execute('PRAGMA journal_mode=WAL')
        return self._local.conn
    
    def _initialize_database(self):
        """Crea las tablas si no existen"""
        conn = self._get_connection()
        
        # Tabla de configuración
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de símbolos
        conn.execute('''
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                symbol_type TEXT NOT NULL,
                lot_size REAL NOT NULL DEFAULT 0.35,
                is_active BOOLEAN DEFAULT 1,
                is_running BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de historial de operaciones
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                lot_size REAL NOT NULL,
                ticket INTEGER,
                open_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                close_time TIMESTAMP,
                close_price REAL,
                profit REAL,
                status TEXT DEFAULT 'OPEN',
                FOREIGN KEY (symbol) REFERENCES symbols(symbol)
            )
        ''')
        
        
        # Tabla de análisis con sistema de predicción y aprendizaje
        conn.execute('''
            CREATE TABLE IF NOT EXISTS analysis_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT,
                confidence INTEGER,
                details TEXT,
                prediction TEXT,              -- JSON: {prediction, probability, target_price, rationale}
                prediction_accuracy TEXT DEFAULT 'PENDIENTE',     -- ACERTADA/FALLIDA/PENDIENTE
                prediction_adjustment INTEGER DEFAULT 0,  -- +5 o -5 para aprendizaje
                FOREIGN KEY (symbol) REFERENCES symbols(symbol)
            )
        ''')
        
        # Tabla de errores
        conn.execute('''
            CREATE TABLE IF NOT EXISTS execution_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                stack_trace TEXT
            )
        ''')
        
        # Índices para optimización
        conn.execute('CREATE INDEX IF NOT EXISTS idx_symbols_active ON symbols(is_active)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trade_symbol ON trade_history(symbol)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_analysis_symbol ON analysis_log(symbol)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON execution_errors(timestamp)')
        
        conn.commit()
    
    # ==================== SETTINGS ====================
    
    def save_setting(self, key: str, value: Any):
        """Guarda o actualiza una configuración"""
        conn = self._get_connection()
        value_str = json.dumps(value) if not isinstance(value, str) else value
        
        with self._conn_lock:
            conn.execute('''
                INSERT INTO settings (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET 
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            ''', (key, value_str))
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Obtiene una configuración"""
        conn = self._get_connection()
        cursor = conn.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        if row is None:
            return default
        
        try:
            return json.loads(row['value'])
        except:
            return row['value']
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Obtiene todas las configuraciones"""
        conn = self._get_connection()
        cursor = conn.execute('SELECT key, value FROM settings')
        settings = {}
        
        for row in cursor:
            try:
                settings[row['key']] = json.loads(row['value'])
            except:
                settings[row['key']] = row['value']
        
        return settings
    
    # ==================== SYMBOLS ====================
    
    def add_symbol(self, symbol: str, symbol_type: str, lot_size: float = 0.35) -> int:
        """Agrega un nuevo símbolo"""
        conn = self._get_connection()
        
        with self._conn_lock:
            cursor = conn.execute('''
                INSERT INTO symbols (symbol, symbol_type, lot_size, is_active, is_running)
                VALUES (?, ?, ?, 1, 0)
            ''', (symbol, symbol_type, lot_size))
            return cursor.lastrowid
    
    def update_symbol_status(self, symbol: str, is_running: bool):
        """Actualiza el estado de ejecución de un símbolo"""
        conn = self._get_connection()
        
        with self._conn_lock:
            conn.execute('''
                UPDATE symbols 
                SET is_running = ?, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = ?
            ''', (1 if is_running else 0, symbol))
    
    def get_symbol(self, symbol: str) -> Optional[Dict]:
        """Obtiene información de un símbolo"""
        conn = self._get_connection()
        cursor = conn.execute('SELECT * FROM symbols WHERE symbol = ?', (symbol,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_active_symbols(self) -> List[Dict]:
        """Obtiene todos los símbolos activos"""
        conn = self._get_connection()
        cursor = conn.execute('SELECT * FROM symbols WHERE is_active = 1 ORDER BY created_at')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_running_symbols(self) -> List[Dict]:
        """Obtiene símbolos actualmente en ejecución"""
        conn = self._get_connection()
        cursor = conn.execute('SELECT * FROM symbols WHERE is_running = 1')
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_symbol(self, symbol: str):
        """Elimina un símbolo (soft delete)"""
        conn = self._get_connection()
        
        with self._conn_lock:
            conn.execute('''
                UPDATE symbols 
                SET is_active = 0, is_running = 0, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = ?
            ''', (symbol,))
            conn.commit()
    
    # ==================== TRADE HISTORY ====================
    
    def add_trade(self, symbol: str, trade_type: str, entry_price: float,
                  stop_loss: float, take_profit: float, lot_size: float,
                  ticket: Optional[int] = None) -> int:
        """Registra una nueva operación"""
        conn = self._get_connection()
        
        with self._conn_lock:
            cursor = conn.execute('''
                INSERT INTO trade_history 
                (symbol, trade_type, entry_price, stop_loss, take_profit, lot_size, ticket, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
            ''', (symbol, trade_type, entry_price, stop_loss, take_profit, lot_size, ticket))
            conn.commit()
            return cursor.lastrowid
    
    def close_trade(self, trade_id: int, close_price: float, profit: float):
        """Cierra una operación"""
        conn = self._get_connection()
        
        with self._conn_lock:
            conn.execute('''
                UPDATE trade_history 
                SET close_time = CURRENT_TIMESTAMP,
                    close_price = ?,
                    profit = ?,
                    status = 'CLOSED'
                WHERE id = ?
            ''', (close_price, profit, trade_id))
            conn.commit()
    
    def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Obtiene historial de operaciones"""
        conn = self._get_connection()
        
        if symbol:
            cursor = conn.execute('''
                SELECT * FROM trade_history 
                WHERE symbol = ? 
                ORDER BY open_time DESC 
                LIMIT ?
            ''', (symbol, limit))
        else:
            cursor = conn.execute('''
                SELECT * FROM trade_history 
                ORDER BY open_time DESC 
                LIMIT ?
            ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    
    # ==================== ANALYSIS LOG ====================
    
    def save_analysis(self, symbol: str, analysis_result: dict):
        """
        Guarda el resultado del análisis en la BD.
        Incluye predicción futura y verificación de predicción anterior.
        """
        import json
        from datetime import datetime
        
        conn = self._get_connection()
        
        try:
            # Extraer acción y confianza desde paso5
            paso5 = analysis_result.get('paso5', {})
            action = paso5.get('decision', 'ESPERAR')
            
            # CRÍTICO: Usar confianza final de paso5 (incluye ajuste)
            confidence = paso5.get('final_confidence', 
                                  analysis_result.get('confidence', 0))
            
            # Extraer razonamiento (puede estar en paso5 o en reasoning directo)
            reasoning = paso5.get('reasoning', analysis_result.get('reasoning', 'Sin razonamiento'))
            
            # Extraer predicción
            prediction = analysis_result.get('prediction')
            prediction_json = json.dumps(prediction) if prediction else None
            
            # Verificación de predicción anterior
            verification = analysis_result.get('prediction_verification', {})
            
            if verification.get('had_prediction'):
                accuracy = 'ACERTADA' if verification.get('was_accurate') else 'FALLIDA'
                adjustment = verification.get('confidence_adjustment', 0)
            else:
                accuracy = 'PENDIENTE'
                adjustment = 0
            
            # Convertir datetime a string para JSON
            analysis_copy = analysis_result.copy()
            if 'timestamp' in analysis_copy:
                if hasattr(analysis_copy['timestamp'], 'isoformat'):
                    analysis_copy['timestamp'] = analysis_copy['timestamp'].isoformat()
            
            # Extraer datos de cada paso para logging
            paso1_data = analysis_result.get('paso1', {})
            paso2_data = analysis_result.get('paso2', {})
            paso3_data = analysis_result.get('paso3', {})
            paso4_data = analysis_result.get('paso4', {})
            
            with self._conn_lock:
                cursor = conn.execute('''
                    INSERT INTO analysis_log 
                    (timestamp, symbol, action, confidence, details, prediction, prediction_accuracy, prediction_adjustment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    symbol,
                    action,
                    confidence,
                    json.dumps(analysis_copy),  # Usar copia con timestamp convertido
                    prediction_json,
                    accuracy,
                    adjustment
                ))
                
                conn.commit()
                
                # Log detallado de lo que se guardó
                logger.info(f"✅ Análisis guardado en BD:")
                logger.info(f"   Symbol: {symbol}")
                logger.info(f"   Action: {action}")
                logger.info(f"   Confidence: {confidence}%")
                logger.info(f"   Base: {paso5.get('base_confidence', 0)}%")
                logger.info(f"   Adjustment: {paso5.get('adjustment', 0):+d}%")
                logger.info(f"   Paso 2: {paso2_data.get('tendencia', 'N/A')} ({paso2_data.get('confianza', 0)}%)")
                logger.info(f"   Paso 3: {paso3_data.get('veredicto_matematico', 'N/A')} ({paso3_data.get('confianza_matematica', 0)}%)")
                logger.info(f"   Paso 4: {paso4_data.get('recommendation', 'N/A')}")
                logger.info(f"   Reasoning: {reasoning[:50]}..." if len(reasoning) > 50 else f"   Reasoning: {reasoning}")
                logger.info(f"   Prediction: {prediction.get('prediction', 'N/A') if prediction else 'N/A'}")
                logger.info(f"   Accuracy: {accuracy}")
        
        except Exception as e:
            logger.error(f"❌ ERROR guardando análisis: {e}")
            import traceback
            traceback.print_exc()
    
    def get_last_analysis(self, symbol: str) -> Optional[dict]:
        """
        Obtiene el último análisis guardado para un símbolo.
        Usado para verificar predicciones anteriores.
        
        Returns:
            dict con prediction, timestamp, details
        """
        import json
        
        try:
            conn = self._get_connection() # Use self._get_connection()
            cursor = conn.execute('''
                SELECT details, prediction, timestamp, prediction_accuracy
                FROM analysis_log
                WHERE symbol = ? AND prediction IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (symbol,))
            
            row = cursor.fetchone()
            
            if row:
                details = json.loads(row['details']) if row['details'] else {} # Access by column name
                prediction = json.loads(row['prediction']) if row['prediction'] else None # Access by column name
                
                return {
                    'details': details,
                    'prediction': prediction,
                    'timestamp': row['timestamp'], # Access by column name
                    'accuracy': row['prediction_accuracy'] # Access by column name
                }
        
        except Exception as e:
            # Assuming a logger is available or print
            print(f"Error obteniendo último análisis: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def get_analysis_history(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Obtiene historial de análisis"""
        try:
            conn = self._get_connection()
            
            if symbol:
                cursor = conn.execute('''
                    SELECT * FROM analysis_log 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (symbol, limit))
            else:
                cursor = conn.execute('''
                    SELECT * FROM analysis_log 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            # NO usar logger para evitar recursión
            print(f"ERROR en get_analysis_history: {e}")
            return []
    
    def get_latest_analysis(self, symbol: str) -> Optional[Dict]:
        """Obtiene el análisis más reciente de un símbolo"""
        conn = self._get_connection()
        cursor = conn.execute('''
            SELECT * FROM analysis_log 
            WHERE symbol = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''', (symbol,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # ==================== ERROR LOG ====================
    
    def log_error(self, error_type: str, error_message: str, 
                  symbol: Optional[str] = None, stack_trace: Optional[str] = None):
        """Registra un error"""
        conn = self._get_connection()
        
        with self._conn_lock:
            conn.execute('''
                INSERT INTO execution_errors 
                (symbol, error_type, error_message, stack_trace)
                VALUES (?, ?, ?, ?)
            ''', (symbol, error_type, error_message, stack_trace))
            conn.commit()
    
    def get_errors(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Obtiene historial de errores"""
        try:
            conn = self._get_connection()
            
            if symbol:
                cursor = conn.execute('''
                    SELECT * FROM execution_errors 
                    WHERE symbol = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (symbol, limit))
            else:
                cursor = conn.execute('''
                    SELECT * FROM execution_errors 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"ERROR en get_errors: {e}")
            return []
    
    def close(self):
        """Cierra la conexión (útil para cleanup)"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
