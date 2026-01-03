import requests
import json
import logging
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [IA-TRADER-SENIOR] - %(message)s')

def analyze_price_action(symbol, context_data):
    """
    Analizador de IA Senior optimizado para encontrar confluencia técnica.
    Adaptado con REGLAS ESPECÍFICAS por tipo de símbolo.
    Ahora soporta múltiples proveedores de IA (Ollama / Cloudflare).
    """
    try:
        # Importar sistema de proveedores
        from models.database import Database
        from models.ai_provider import get_ai_provider
        
        # Obtener proveedor configurado
        db = Database()
        provider = get_ai_provider(db)
        
        logging.info(f"🤖 Usando proveedor de IA: {provider.get_name()}")
        
        # NO verificar disponibilidad aquí - intentar query directamente
        # La verificación de disponibilidad puede fallar por timeouts temporales
        # Es mejor intentar la query real y manejar el error si ocurre

        
        # Identificar tipo de símbolo y reglas específicas
        symbol_upper = symbol.upper()
        
        # REGLAS ESPECÍFICAS POR TIPO DE ACTIVO
        if symbol_upper.startswith('B') or 'BOOM' in symbol_upper:
            tipo_activo = "BOOM (Spike Alcista)"
            reglas_especificas = """
            ⚠️ REGLA BOOM: Este activo SOLO permite señales de COMPRA.
            - NUNCA emitas señal de VENTA en un Boom.
            - Busca confluencia técnica (RSI bajo, MACD cruzando alcista, Heikin Ashi verde) para COMPRAR en anticipación al spike.
            - Si no hay confluencia alcista, responde ESPERAR.
            """
        elif symbol_upper.startswith('C') or 'CRASH' in symbol_upper:
            tipo_activo = "CRASH (Spike Bajista)"
            reglas_especificas = """
            ⚠️ REGLA CRASH: Este activo SOLO permite señales de VENTA.
            - NUNCA emitas señal de COMPRA en un Crash.
            - Busca confluencia técnica (RSI alto, MACD cruzando bajista, Heikin Ashi rojo) para VENDER en anticipación al spike.
            - Si no hay confluencia bajista, responde ESPERAR.
            """
        elif 'STEP' in symbol_upper and 'RISE' in symbol_upper:
            tipo_activo = "STEP RISE (Escalera Alcista)"
            reglas_especificas = """
            ⚠️ REGLA STEP RISE: Prioriza señales de COMPRA (dirección del nombre).
            - Busca confirmación alcista antes de COMPRAR.
            - Solo considera VENTA si hay señales técnicas MUY fuertes en contra.
            """
        elif 'STEP' in symbol_upper and 'DROP' in symbol_upper:
            tipo_activo = "STEP DROP (Escalera Bajista)"
            reglas_especificas = """
            ⚠️ REGLA STEP DROP: Prioriza señales de VENTA (dirección del nombre).
            - Busca confirmación bajista antes de VENDER.
            - Solo considera COMPRA si hay señales técnicas MUY fuertes en contra.
            """
        elif symbol_upper.startswith('V') or 'VOLATILITY' in symbol_upper:
            tipo_activo = "VOLATILITY (Índice de Volatilidad)"
            reglas_especificas = """
            ℹ️ REGLA VOLATILITY: Puedes sugerir COMPRA o VENTA según tendencia.
            - Analiza la tendencia de la regresión lineal y el panel técnico.
            - Respeta las zonas de RSI (sobrecompra/sobreventa).
            """
        elif 'XAU' in symbol_upper or 'GOLD' in symbol_upper:
            tipo_activo = "XAUUSD (Oro)"
            reglas_especificas = """
            ℹ️ REGLA XAUUSD: Puedes sugerir COMPRA o VENTA según tendencia.
            - ⚠️ IMPORTANTE: El spread del oro es MAYOR, requiere más confirmación del RSI.
            - Solo emite señal si hay confluencia FUERTE (>75% confianza).
            - Considera movimientos más amplios debido al spread.
            """
        else:
            tipo_activo = "GENÉRICO"
            reglas_especificas = """
            ℹ️ REGLA GENÉRICA: Analiza todos los indicadores y emite la señal más probable.
            """
        
        prompt = f"""Analiza {symbol} ({tipo_activo}) y emite una señal de trading.

{reglas_especificas}

CONTEXTO TÉCNICO:
{context_data}

INSTRUCCIONES:
1. Si Regresión R² > 70%, prioriza esa dirección
2. Busca confluencia entre indicadores (MACD, RSI, Heikin Ashi)
3. Solo emite COMPRA/VENTA si hay confluencia clara

Responde SOLO en este formato JSON exacto:
{{
    "señal": "COMPRA/VENTA/ESPERAR",
    "confianza": 75,
    "razon": "Explicación breve (max 50 palabras)"
}}
"""
        
        # Consultar proveedor con timeout de 60s
        ia_text = provider.query(prompt, timeout=60, format_json=True)
        
        if ia_text:
            # LOGGING: Mostrar respuesta completa para debug
            logging.info(f"📥 Respuesta IA completa ({len(ia_text)} chars): {ia_text[:200]}...")
            
            # Extracción robusta de JSON
            start = ia_text.find('{')
            end = ia_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = ia_text[start:end]
                logging.debug(f"🔍 JSON extraído: {json_str}")
                result = json.loads(json_str)
                
                # CRÍTICO: Asegurar SIEMPRE ambas claves (español e inglés)
                # Español → Inglés
                if 'señal' in result and 'signal' not in result:
                    result['signal'] = result['señal']
                # Inglés → Español  
                if 'signal' in result and 'señal' not in result:
                    result['señal'] = result['signal']
                
                # Confianza
                if 'confianza' in result:
                    result['confidence'] = int(result['confianza'])
                if 'confidence' in result:
                    result['confianza'] = int(result['confidence'])
                
                # Razón/Reason
                if 'razon' in result and 'reason' not in result:
                    result['reason'] = result['razon']
                if 'reason' in result and 'razon' not in result:
                    result['razon'] = result['reason']
                
                # Metadata del proveedor
                result['provider'] = provider.get_name()
                
                return result
            
            # Si no encuentra JSON, intentar parsear directo
            return json.loads(ia_text)
        else:
            logging.error(f"Respuesta vacía de {provider.get_name()}")
            
    except Exception as e:
        logging.error(f"Error en análisis IA Senior: {e}", exc_info=True)
    
    # CRÍTICO: Return de error debe incluir AMBAS claves
    return {
        "señal": "ESPERAR", 
        "signal": "ESPERAR",
        "confianza": 0, 
        "confidence": 0,
        "razon": "IA no disponible para confluencia",
        "reason": "AI not available for confluence",
        "error": "IA no disponible para confluencia"
    }


def query_ollama(prompt: str, timeout: int = 30) -> str:
    """
    DEPRECATED: Usar query_ai() en su lugar.
    Mantenido por compatibilidad con código legacy.
    """
    return query_ai(prompt, timeout)


def query_ai(prompt: str, timeout: int = 30) -> str:
    """
    Wrapper genérico para consultar el proveedor de IA configurado.
    Usado por predicciones y análisis generales.
    
    Args:
        prompt: El prompt a enviar
        timeout: Timeout en segundos (default: 30)
        
    Returns:
        La respuesta del IA como string
    """
    try:
        # Importar sistema de proveedores
        from models.database import Database
        from models.ai_provider import get_ai_provider
        
        # Obtener proveedor configurado
        db = Database()
        provider = get_ai_provider(db)
        
        # Consultar proveedor
        return provider.query(prompt, timeout=timeout)
            
    except Exception as e:
        logging.error(f"Error en query_ai: {e}")
        return ""

