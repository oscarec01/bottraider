"""
Configuración de símbolos y parámetros de trading.
"""

from typing import Dict
from dataclasses import dataclass


@dataclass
class SymbolConfig:
    """Configuración de un símbolo específico"""
    
    name: str
    symbol_type: str  # BOOM, CRASH, VOLATILITY, etc.
    lot_size: float
    sl_pips: int
    tp_pips: int
    is_active: bool = True
    
    @classmethod
    def from_symbol_name(cls, symbol: str, lot_size: float = 0.35):
        """
        Crea configuración basándose en el nombre del símbolo.
        
        Args:
            symbol: Nombre del símbolo
            lot_size: Tamaño de lote (opcional)
            
        Returns:
            SymbolConfig
        """
        symbol_upper = symbol.upper()
        
        # Detectar tipo
        if symbol_upper.startswith('B') or 'BOOM' in symbol_upper:
            symbol_type = "BOOM"
            sl, tp = 500, 1000
        elif symbol_upper.startswith('C') or 'CRASH' in symbol_upper:
            symbol_type = "CRASH"
            sl, tp = 500, 1000
        elif symbol_upper.startswith('V') or 'VOLATILITY' in symbol_upper:
            symbol_type = "VOLATILITY"
            sl, tp = 500, 1000
        elif 'XAU' in symbol_upper or 'GOLD' in symbol_upper:
            symbol_type = "XAUUSD"
            sl, tp = 300, 600
            lot_size = 0.01 if lot_size == 0.35 else lot_size
        elif 'STEP' in symbol_upper:
            symbol_type = "STEP"
            sl, tp = 500, 1000
        else:
            symbol_type = "GENERIC"
            sl, tp = 500, 1000
        
        return cls(
            name=symbol,
            symbol_type=symbol_type,
            lot_size=lot_size,
            sl_pips=sl,
            tp_pips=tp
        )
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        return {
            'name': self.name,
            'symbol_type': self.symbol_type,
            'lot_size': self.lot_size,
            'sl_pips': self.sl_pips,
            'tp_pips': self.tp_pips,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Crea desde diccionario"""
        return cls(
            name=data['name'],
            symbol_type=data['symbol_type'],
            lot_size=data['lot_size'],
            sl_pips=data['sl_pips'],
            tp_pips=data['tp_pips'],
            is_active=data.get('is_active', True)
        )
