"""
Validadores para entrada de datos en la UI.
"""

from typing import Tuple, Optional
import re


class Validators:
    """Validadores estáticos para diferentes tipos de datos"""
    
    @staticmethod
    def validate_account(account: str) -> Tuple[bool, Optional[str]]:
        """
        Valida número de cuenta MT5.
        
        Returns:
            (is_valid, error_message)
        """
        if not account:
            return False, "Número de cuenta requerido"
        
        if not account.isdigit():
            return False, "El número de cuenta debe contener solo dígitos"
        
        if len(account) < 5:
            return False, "Número de cuenta inválido (muy corto)"
        
        return True, None
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, Optional[str]]:
        """Valida contraseña"""
        if not password:
            return False, "Contraseña requerida"
        
        if len(password) < 4:
            return False, "Contraseña debe tener al menos 4 caracteres"
        
        return True, None
    
    @staticmethod
    def validate_server(server: str) -> Tuple[bool, Optional[str]]:
        """Valida servidor"""
        if not server:
            return False, "Servidor requerido"
        
        valid_servers = ['Deriv-Demo', 'Deriv-Server', 'Deriv-Server-02']
        
        if server not in valid_servers:
            return False, f"Servidor debe ser uno de: {', '.join(valid_servers)}"
        
        return True, None
    
    @staticmethod
    def validate_lot_size(lot_size: str) -> Tuple[bool, Optional[str]]:
        """Valida tamaño de lote"""
        try:
            lot = float(lot_size)
            
            if lot <= 0:
                return False, "El lote debe ser mayor a 0"
            
            if lot > 100:
                return False, "El lote es demasiado grande"
            
            return True, None
        except ValueError:
            return False, "Lote debe ser un número válido"
    
    @staticmethod
    def validate_pips(pips: str) -> Tuple[bool, Optional[str]]:
        """Valida pips (SL/TP)"""
        try:
            value = int(pips)
            
            if value <= 0:
                return False, "Los pips deben ser mayores a 0"
            
            if value > 10000:
                return False, "Valor de pips demasiado alto"
            
            return True, None
        except ValueError:
            return False, "Pips debe ser un número entero"
    
    @staticmethod
    def validate_interval(interval: str) -> Tuple[bool, Optional[str]]:
        """Valida intervalo de análisis (en segundos)"""
        try:
            value = int(interval)
            
            if value < 30:
                return False, "Intervalo mínimo: 30 segundos"
            
            if value > 3600:
                return False, "Intervalo máximo: 1 hora (3600s)"
            
            return True, None
        except ValueError:
            return False, "Intervalo debe ser un número entero"
    
    @staticmethod
    def validate_symbol(symbol: str) -> Tuple[bool, Optional[str]]:
        """Valida nombre de símbolo"""
        if not symbol:
            return False, "Símbolo requerido"
        
        if len(symbol) < 3:
            return False, "Nombre de símbolo inválido"
        
        # Validar caracteres permitidos
        if not re.match(r'^[A-Za-z0-9\s]+$', symbol):
            return False, "Símbolo contiene caracteres inválidos"
        
        return True, None
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str]]:
        """Valida URL (para Ollama)"""
        if not url:
            return False, "URL requerida"
        
        # Validación básica de URL
        url_pattern = re.compile(
            r'^https?://'  # http:// o https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # puerto opcional
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            return False, "URL inválida"
        
        return True, None
