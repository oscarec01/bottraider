import requests
import json
import logging
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [IA-TRADER-SENIOR] - %(message)s')

def analyze_price_action(symbol, context_data):
    """
    Analizador de IA Senior optimizado para encontrar confluencia técnica.
    Adaptado con REGLAS ESPECÍFICAS por tipo de símbolo.
    """
    try:
        url = config.OLLAMA_URL
        model = config.OLLAMA_MODEL
        
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
        
        prompt = f"""
        Estás analizando {symbol} ({tipo_activo}).
        
        {reglas_especificas}
        
        Actúa como un Trader Senior de Deriv experto en Índices Sintéticos.
        Tu objetivo es encontrar CONFLUENCIA técnica para emitir señales decisivas.
        
        CONTEXTO TÉCNICO DE {symbol}:
        {context_data}
        
        REGLAS DE DECISIÓN GENERALES:
        1. PRIORIDAD MACRO: Si la Regresión tiene un R2 > 70%, dale prioridad absoluta a esa dirección (respetando las reglas específicas del símbolo).
        2. GATILLOS: Considera el RSI y el MACD como gatillos de entrada. 
        3. CONFLUENCIA: Si la regresión es ALCISTA y el MACD o Heikin Ashi confirman esa dirección, la señal DEBE ser COMPRA (si está permitido para este símbolo). Lo mismo para VENTAS.
        4. Agresividad: No seas conservador sin motivo. Si la mayoría de indicadores (MACD, Medias, Heikin Ashi) están a favor de la tendencia macro, emite la señal.
        
        Responde ESTRICTAMENTE en este formato JSON para que el bot pueda procesarlo:
        {{
            "señal": "COMPRA/VENTA/ESPERAR",
            "confianza": "0-100",
            "razon": "Breve explicación técnica de la confluencia encontrada"
        }}
        """
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            ia_text = response.json().get("response", "").strip()
            # Extracción robusta de JSON
            start = ia_text.find('{')
            end = ia_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = ia_text[start:end]
                return json.loads(json_str)
            return json.loads(ia_text)
        else:
            logging.error(f"Fallo conexión Ollama: {response.status_code}")
            
    except Exception as e:
        logging.error(f"Error en análisis IA Senior: {e}")
    
    return {"señal": "ESPERAR", "error": "IA no disponible para confluencia"}

def query_ollama(prompt: str, timeout: int = 30) -> str:
    """
    Wrapper genérico para consultar Ollama.
    Usado por predicciones y análisis generales.
    
    Args:
        prompt: El prompt a enviar
        timeout: Timeout en segundos (default: 30)
        
    Returns:
        La respuesta de Ollama como string
    """
    try:
        url = config.OLLAMA_URL
        model = config.OLLAMA_MODEL
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            logging.error(f"Ollama error: {response.status_code}")
            return ""
            
    except Exception as e:
        logging.error(f"Error en query_ollama: {e}")
        return ""
