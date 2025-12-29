"""
Trailing Stop Manager - Gestiona trailing stops automáticos.

Característica especial: Al activarse por primera vez, mueve el SL a 
precio_entrada + 1 pip (CERO RIESGO), luego usa la distancia configurada.
"""

from PyQt6.QtCore import QObject, pyqtSignal
import MetaTrader5 as mt5
from models.database import Database
from utils.logger import get_logger

logger = get_logger(__name__)


class TrailingStopManager(QObject):
    """
    Gestor de trailing stops para posiciones abiertas con lógica de cero riesgo.
    
    Primera actualización: SL a precio_entrada + 1 pip (garantiza profit mínimo)
    Actualizaciones siguientes: SL siguiendo precio a distancia configurada
    """
    
    trailing_updated = pyqtSignal(str, float)  # symbol, new_sl
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        # Diccionario: ticket -> {'activation_price': float, 'activated': bool, 'first_update': bool}
        self.positions_tracking = {}
    
    def check_and_apply_trailing(self, symbol: str):
        """
        Verifica posiciones abiertas y aplica trailing stop si corresponde.
        
        Args:
            symbol: Símbolo a verificar
        """
        # Verificar si trailing está habilitado
        if not self.db.get_setting('enable_trailing_stop', False):
            return
        
        # Obtener parámetros
        activation_pips = self.db.get_setting('trailing_activation', 100)
        distance_pips = self.db.get_setting('trailing_distance', 50)
        
        # Obtener posiciones abiertas
        positions = mt5.positions_get(symbol=symbol)
        
        if not positions:
            return
        
        for position in positions:
            self._process_position(position, activation_pips, distance_pips)
    
    def _process_position(self, position, activation_pips: int, distance_pips: int):
        """Procesa una posición individual para trailing stop."""
        ticket = position.ticket
        symbol = position.symbol
        position_type = position.type  # 0=BUY, 1=SELL
        open_price = position.price_open
        current_sl = position.sl
        current_price = position.price_current
        
        # Obtener info del símbolo
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return
        
        point = symbol_info.point
        digits = symbol_info.digits
        
        # Calcular profit en pips
        if position_type == 0:  # BUY
            profit_pips = int((current_price - open_price) / point)
        else:  # SELL
            profit_pips = int((open_price - current_price) / point)
        
        # Verificar si está en tracking
        if ticket not in self.positions_tracking:
            self.positions_tracking[ticket] = {
                'activation_price': None,
                'activated': False,
                'first_update': True  # Bandera para primera actualización
            }
        
        tracking = self.positions_tracking[ticket]
        
        # Verificar activación
        if not tracking['activated'] and profit_pips >= activation_pips:
            logger.info(f"[SCALPING] ✅ Trailing activado para {symbol} (Profit: {profit_pips} pips)")
            tracking['activated'] = True
            tracking['activation_price'] = current_price
        
        # Si está activado, mover SL
        if tracking['activated']:
            # LÓGICA ESPECIAL: Primera actualización a CERO RIESGO
            if tracking['first_update']:
                new_sl = self._calculate_zero_risk_sl(
                    position_type, open_price, point, digits
                )
                tracking['first_update'] = False  # Ya no es la primera
                
                logger.info(f"[SCALPING] 🛡️ PRIMERA ACTUALIZACIÓN - SL a cero riesgo (entrada + 1 pip)")
            else:
                # Actualizaciones siguientes: distancia normal
                new_sl = self._calculate_new_sl(
                    position_type, current_price, distance_pips, point, digits
                )
            
            # Solo mover si el nuevo SL es mejor que el actual
            should_update = False
            
            if position_type == 0:  # BUY
                should_update = new_sl > current_sl if current_sl > 0 else True
            else:  # SELL
                should_update = new_sl < current_sl if current_sl > 0 else True
            
            if should_update:
                success = self._modify_sl(ticket, new_sl)
                
                if success:
                    logger.info(f"[SCALPING] 📈 SL actualizado para {symbol} a {new_sl}")
                    self.trailing_updated.emit(symbol, new_sl)
    
    def _calculate_zero_risk_sl(self, position_type: int, open_price: float, 
                                  point: float, digits: int) -> float:
        """
        Calcula SL de cero riesgo: precio_entrada + 1 pip.
        
        Garantiza que la operación esté en profit mínimo aunque el mercado retroceda.
        """
        if position_type == 0:  # BUY
            # SL = Entrada + 1 pip (asegura profit mínimo)
            new_sl = open_price + point
        else:  # SELL
            # SL = Entrada - 1 pip
            new_sl = open_price - point
        
        return round(new_sl, digits)
    
    def _calculate_new_sl(self, position_type: int, current_price: float, 
                          distance_pips: int, point: float, digits: int) -> float:
        """Calcula el nuevo SL basado en la distancia del trailing."""
        distance_price = distance_pips * point
        
        if position_type == 0:  # BUY
            new_sl = current_price - distance_price
        else:  # SELL
            new_sl = current_price + distance_price
        
        return round(new_sl, digits)
    
    def _modify_sl(self, ticket: int, new_sl: float) -> bool:
        """Modifica el SL de una posición."""
        try:
            position = mt5.positions_get(ticket=ticket)
            
            if not position:
                return False
            
            position = position[0]
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return True
            else:
                logger.error(f"Error modificando SL: Código {result.retcode}")
                return False
        
        except Exception as e:
            logger.error(f"Excepción modificando SL: {e}")
            return False
    
    def cleanup_closed_positions(self):
        """Limpia tracking de posiciones cerradas."""
        try:
            current_tickets = [p.ticket for p in mt5.positions_get() or []]
            
            # Remover tickets cerrados
            closed = [t for t in self.positions_tracking.keys() if t not in current_tickets]
            
            for ticket in closed:
                del self.positions_tracking[ticket]
                logger.debug(f"Tracking limpiado para ticket {ticket}")
        
        except Exception as e:
            logger.error(f"Error limpiando posiciones: {e}")
