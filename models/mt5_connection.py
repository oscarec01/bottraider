"""
Gestión de conexión MT5 con patrón Singleton thread-safe.
Permite múltiples workers acceder a MT5 de forma segura.
"""

import MetaTrader5 as mt5
import threading
from typing import Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class MT5Connection:
    """Singleton thread-safe para gestión de conexión MT5"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._connected = False
        self._account = None
        self._server = None
        self._operation_lock = threading.Lock()
        self._initialized = True
        logger.info("MT5Connection inicializado")
    
    def connect(self, account: int, password: str, server: str) -> bool:
        """
        Conecta a MetaTrader 5.
        
        Args:
            account: Número de cuenta
            password: Contraseña
            server: Servidor (ej: "Deriv-Demo")
            
        Returns:
            True si la conexión fue exitosa
        """
        with self._operation_lock:
            # Si ya está conectado, cerrar primero
            if self._connected:
                logger.info("Ya hay una conexión activa, desconectando...")
                self.disconnect()
            
            # Inicializar MT5
            if not mt5.initialize():
                error = mt5.last_error()
                logger.error(f"mt5.initialize() falló: {error}")
                return False
            
            # Login
            authorized = mt5.login(account, password=password, server=server)
            
            if authorized:
                self._connected = True
                self._account = account
                self._server = server
                
                account_info = mt5.account_info()
                if account_info:
                    logger.info(f"✅ Conectado a MT5")
                    logger.info(f"   Cuenta: {account}")
                    logger.info(f"   Servidor: {server}")
                    logger.info(f"   Balance: ${account_info.balance:.2f}")
                    logger.info(f"   Equity: ${account_info.equity:.2f}")
                    logger.info(f"   Moneda: {account_info.currency}")
                return True
            else:
                error = mt5.last_error()
                logger.error(f"❌ Login falló - Cuenta: {account}, Server: {server}")
                logger.error(f"   Error: {error}")
                mt5.shutdown()
                return False
    
    def disconnect(self):
        """Desconecta de MT5"""
        with self._operation_lock:
            if self._connected:
                mt5.shutdown()
                self._connected = False
                self._account = None
                self._server = None
                logger.info("Desconectado de MT5")
    
    def is_connected(self) -> bool:
        """Verifica si está conectado"""
        return self._connected
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Obtiene información de la cuenta"""
        if not self._connected:
            logger.warning("No conectado a MT5")
            return None
        
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return None
            
            return {
                'account': account_info.login,
                'server': account_info.server,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'margin_free': account_info.margin_free,
                'margin_level': account_info.margin_level,
                'currency': account_info.currency,
                'profit': account_info.profit
            }
        except Exception as e:
            logger.error(f"Error obteniendo info de cuenta: {e}")
            return None
    
    def calculate_lot_size(self, symbol: str, risk_percentage: float, sl_distance_pips: int) -> tuple[float, str]:
        """
        Calcula el tamaño de lote basado en gestión de riesgo.
        
        Formula: Lot Size = (Balance × Risk%) / (SL_Distance × Point × Contract_Size)
        
        Args:
            symbol: Símbolo a operar
            risk_percentage: % del balance a arriesgar (ej: 1.0 = 1%)
            sl_distance_pips: Distancia del SL en pips
            
        Returns:
            (lot_size, warning_message)
        """
        if not self._connected:
            logger.warning("No conectado a MT5 para calcular lotaje")
            return 0.01, "No conectado a MT5"
        
        with self._operation_lock:
            # Obtener info de cuenta
            account_info = mt5.account_info()
            if not account_info:
                return 0.01, "No se pudo obtener info de cuenta"
            
            balance = account_info.balance
            
            # Obtener info del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return 0.01, f"No se pudo obtener info de {symbol}"
            
            point = symbol_info.point
            vol_min = symbol_info.volume_min
            vol_max = symbol_info.volume_max
            vol_step = symbol_info.volume_step
            contract_size = symbol_info.trade_contract_size
            
            # Calcular riesgo en dinero
            risk_amount = balance * (risk_percentage / 100)
            
            # Distancia SL en precio
            sl_distance_price = sl_distance_pips * point
            
            # Cálculo de lotaje: Riesgo / (Distancia_SL × Contract_Size)
            if sl_distance_price > 0 and contract_size > 0:
                lot_size = risk_amount / (sl_distance_price * contract_size)
            else:
                lot_size = vol_min
            
            # Normalizar al step
            if vol_step > 0:
                steps = round(lot_size / vol_step)
                lot_size = steps * vol_step
            
            # Validar límites
            warning = ""
            original_lot = lot_size
            
            # VALIDACIÓN ESPECIAL: Boom/Crash requieren mínimo 0.20 lotes (Deriv)
            is_boom_crash = self._is_boom_crash_index(symbol)
            
            if is_boom_crash:
                BOOM_CRASH_MIN_LOT = 0.20
                
                if lot_size < BOOM_CRASH_MIN_LOT:
                    lot_size = BOOM_CRASH_MIN_LOT
                    warning = f"⚠️ Boom/Crash: Lotaje ajustado a mínimo {BOOM_CRASH_MIN_LOT} lotes (requerido por broker)"
                    logger.warning(warning)
            else:
                # Validar límites estándar para otros símbolos
                if lot_size < vol_min:
                    lot_size = vol_min
                    warning = f"⚠️ Lotaje calculado ({original_lot:.4f}) < mínimo ({vol_min}). Usando mínimo."
                elif lot_size > vol_max:
                    lot_size = vol_max
                    warning = f"⚠️ Lotaje calculado ({original_lot:.4f}) > máximo ({vol_max}). Usando máximo."

            
            # Calcular decimales correctos
            import math
            if vol_step > 0:
                decimal_places = max(0, -int(math.floor(math.log10(vol_step))))
            else:
                decimal_places = 2
            
            lot_size = round(lot_size, decimal_places)
            
            # Logs informativos
            logger.info(f"💰 MONEY MANAGEMENT:")
            logger.info(f"   Balance: ${balance:.2f}")
            logger.info(f"   Riesgo: {risk_percentage}% = ${risk_amount:.2f}")
            logger.info(f"   SL Distance: {sl_distance_pips} pips ({sl_distance_price:.5f} precio)")
            logger.info(f"   Contract Size: {contract_size}")
            logger.info(f"   Lotaje calculado: {lot_size}")
            
            if warning:
                logger.warning(warning)
            
            return lot_size, warning
    
    def _is_boom_crash_index(self, symbol: str) -> bool:
        """
        Detecta si el símbolo es un índice Boom o Crash.
        Estos índices requieren volúmenes mínimos especiales.
        
        Returns:
            True si es Boom/Crash
        """
        keywords = [
            'Boom 300', 'Boom 500', 'Boom 600', 'Boom 900', 'Boom 1000',
            'Crash 300', 'Crash 500', 'Crash 600', 'Crash 900', 'Crash 1000'
        ]
        return any(keyword.lower() in symbol.lower() for keyword in keywords)
    
    def get_today_profit(self) -> float:
        """
        Obtiene el profit acumulado del día actual desde las 00:00.
        
        Returns:
            Profit en USD del día actual
        """
        if not self._connected:
            logger.debug("No conectado a MT5 para obtener profit diario")
            return 0.0
        
        with self._operation_lock:
            from datetime import datetime, timedelta
            
            try:
                # Obtener deals del día (desde las 00:00)
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                deals = mt5.history_deals_get(today_start, datetime.now())
                
                if deals is None or len(deals) == 0:
                    return 0.0
                
                # Sumar profit de todos los deals
                total_profit = sum(deal.profit for deal in deals)
                
                logger.debug(f"Profit del día: ${total_profit:.2f} ({len(deals)} deals)")
                
                return total_profit
            
            except Exception as e:
                logger.error(f"Error obteniendo profit diario: {e}")
                return 0.0
    
    def get_current_spread(self, symbol: str) -> tuple[float, int]:
        """
        Obtiene el spread actual del símbolo.
        
        Args:
            symbol: Símbolo a consultar
            
        Returns:
            (spread_price, spread_pips)
        """
        if not self._connected:
            logger.debug("No conectado a MT5 para obtener spread")
            return 0.0, 0
        
        with self._operation_lock:
            try:
                tick = mt5.symbol_info_tick(symbol)
                symbol_info = mt5.symbol_info(symbol)
                
                if not tick or not symbol_info:
                    return 0.0, 0
                
                spread_price = tick.ask - tick.bid
                spread_pips = int(spread_price / symbol_info.point)
                
                return spread_price, spread_pips
            
            except Exception as e:
                logger.error(f"Error obteniendo spread: {e}")
                return 0.0, 0
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del símbolo.
        Thread-safe.
        """
        if not self._connected:
            logger.warning("No conectado a MT5")
            return None
        
        with self._operation_lock:
            info = mt5.symbol_info(symbol)
            
            if info is None:
                logger.error(f"Símbolo {symbol} no encontrado")
                return None
            
            # Asegurar que esté visible en Market Watch
            if not info.visible:
                if not mt5.symbol_select(symbol, True):
                    logger.error(f"No se pudo hacer visible {symbol}")
                    return None
                # Actualizar info
                info = mt5.symbol_info(symbol)
            
            return {
                'name': info.name,
                'point': info.point,
                'digits': info.digits,
                'spread': info.spread,
                'trade_stops_level': info.trade_stops_level,
                'trade_contract_size': info.trade_contract_size,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max,
                'volume_step': info.volume_step,
                'filling_mode': info.filling_mode,
                'visible': info.visible
            }
    
    def get_market_data(self, symbol: str, timeframe: int, count: int = 100):
        """
        Obtiene datos históricos del mercado.
        
        Args:
            symbol: Nombre del símbolo
            timeframe: mt5.TIMEFRAME_* (ej: mt5.TIMEFRAME_M5)
            count: Número de velas
            
        Returns:
            pandas.DataFrame o None
        """
        if not self._connected:
            logger.warning("No conectado a MT5")
            return None
        
        with self._operation_lock:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                error = mt5.last_error()
                logger.error(f"Error obteniendo datos de {symbol}: {error}")
                return None
            
            # Convertir a pandas DataFrame
            import pandas as pd
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            return df
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """Obtiene precio actual (bid/ask)"""
        if not self._connected:
            return None
        
        with self._operation_lock:
            tick = mt5.symbol_info_tick(symbol)
            
            if tick is None:
                return None
            
            return {
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'time': tick.time
            }
    
    def get_positions(self, symbol: Optional[str] = None):
        """
        Obtiene posiciones abiertas.
        
        Args:
            symbol: Filtrar por símbolo (opcional)
        """
        if not self._connected:
            return []
        
        with self._operation_lock:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            return [
                {
                    'ticket': p.ticket,
                    'symbol': p.symbol,
                    'type': 'BUY' if p.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': p.volume,
                    'price_open': p.price_open,
                    'sl': p.sl,
                    'tp': p.tp,
                    'price_current': p.price_current,
                    'profit': p.profit,
                    'time': p.time
                }
                for p in positions
            ]
    
    def send_order(self, symbol: str, order_type: str, volume: float,
                   price: float, sl: float, tp: float, 
                   magic: int = 123456, comment: str = "PyQt Bot") -> Dict[str, Any]:
        """
        Envía una orden a MT5 con validaciones completas.
        
        Validaciones:
        1. Spread máximo permitido
        2. Volumen normalizado
        3. Tipo de orden válido
        4. Stops correctos
        
        Returns:
            Dict con resultado de la operación
        """
        if not self._connected:
            return {'success': False, 'error': 'No conectado a MT5'}
        
        with self._operation_lock:
            # ==================== VALIDACIÓN 1: Spread Máximo ====================
            from models.database import Database
            db = Database()
            
            max_spread = db.get_setting('max_spread_pips', 10)
            spread_price, spread_pips = self.get_current_spread(symbol)
            
            if spread_pips > max_spread:
                logger.warning(f"⚠️ SPREAD ALTO: {spread_pips} pips > máximo {max_spread} pips")
                logger.warning(f"   Orden rechazada para proteger capital en {symbol}")
                return {
                    'success': False, 
                    'error': f'Spread muy alto: {spread_pips} pips (máx: {max_spread})'
                }
            
            logger.info(f"✅ Spread OK: {spread_pips} pips (máx: {max_spread})")
            
            # ==================== VALIDACIÓN 2: Volumen ====================
            # Obtener info del símbolo para validación de volumen
            symbol_info_obj = mt5.symbol_info(symbol)
            if symbol_info_obj is None:
                return {'success': False, 'error': f'Símbolo {symbol} no encontrado'}
            
            # Obtener point y digits para normalización de precios
            point = symbol_info_obj.point
            digits = symbol_info_obj.digits
            
            
            # --- NORMALIZACIÓN DE VOLUMEN (Fix Error 10014) ---
            vol_min = symbol_info_obj.volume_min
            vol_max = symbol_info_obj.volume_max
            vol_step = symbol_info_obj.volume_step
            
            # 1. Ajustar al paso más cercano
            if vol_step > 0:
                steps = round(volume / vol_step)
                volume = steps * vol_step
            
            # 2. Respetar límites
            if volume < vol_min:
                volume = vol_min
            elif volume > vol_max:
                volume = vol_max
            
            # 3. Calcular decimales correctos basados en vol_step
            # Para vol_step=0.01 → 2 decimales
            # Para vol_step=0.001 → 3 decimales
            # Para vol_step=1.0 → 0 decimales
            import math
            if vol_step > 0:
                decimal_places = max(0, -int(math.floor(math.log10(vol_step))))
            else:
                decimal_places = 2  # Fallback
            
            volume = round(volume, decimal_places)
            
            logger.info(f"⚖️ Volumen normalizado: {volume} (Step: {vol_step}, Min: {vol_min})")
            
            # Los valores price, sl, tp YA vienen normalizados desde trading_worker.py
            # NO normalizar aquí de nuevo - causaría doble normalización
            logger.info(f"💰 Valores recibidos (ya normalizados):")
            logger.info(f"   Precio: {price}")
            logger.info(f"   SL: {sl}")
            logger.info(f"   TP: {tp}")
            
            # Determinar filling mode
            filling_mode = symbol_info_obj.filling_mode
            
            if filling_mode & 2:  # IOC
                type_filling = mt5.ORDER_FILLING_IOC
            elif filling_mode & 1:  # FOK
                type_filling = mt5.ORDER_FILLING_FOK
            elif filling_mode & 4:  # RETURN
                type_filling = mt5.ORDER_FILLING_RETURN
            else:
                return {'success': False, 'error': 'No hay filling mode compatible'}
            
            
            # Mapear tipo de orden (soporta COMPRA/VENTA español y BUY/SELL inglés)
            if order_type in ['COMPRA', 'BUY']:
                mt5_order_type = mt5.ORDER_TYPE_BUY
            elif order_type in ['VENTA', 'SELL']:
                mt5_order_type = mt5.ORDER_TYPE_SELL
            else:
                return {'success': False, 'error': f'Tipo de orden inválido: {order_type}'}
            
            # Construir request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5_order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "magic": magic,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": type_filling,
            }
            
            # LOG CRÍTICO: Ver EXACTAMENTE qué se envía a MT5
            logger.info(f"🔧 REQUEST EXACTO a MT5:")
            logger.info(f"   symbol: {request['symbol']}")
            logger.info(f"   volume: {request['volume']}")
            logger.info(f"   type: {'BUY' if mt5_order_type == mt5.ORDER_TYPE_BUY else 'SELL'}")
            logger.info(f"   price: {request['price']} (type: {type(request['price'])})")
            logger.info(f"   sl: {request['sl']} (type: {type(request['sl'])})")
            logger.info(f"   tp: {request['tp']} (type: {type(request['tp'])})")
            logger.info(f"   filling: {type_filling}")
            
            # Enviar orden
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f'Error {result.retcode}: {result.comment}'
                }
            
            logger.info(f"✅ Orden ejecutada: {order_type} {symbol} @ {result.price}")
            
            return {
                'success': True,
                'ticket': result.order,
                'volume': result.volume,
                'price': result.price,
                'deal': result.deal
            }
    
    def __del__(self):
        """Cleanup al destruir la instancia"""
        self.disconnect()
