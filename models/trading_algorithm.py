"""
Algoritmo principal de trading que integra los 5 pasos de análisis.
"""

import sys
sys.path.append('..')  # Para importar módulos legacy

from datetime import datetime
from typing import Dict, Any, Optional
import MetaTrader5 as mt5
import pandas as pd

from models.mt5_connection import MT5Connection
from models.database import Database
from utils.logger import get_logger

# Importar módulos legacy
try:
    from prediction_models import get_monthly_probability
    from technical_indicators import get_technical_summary
    from sentiment_analysis import analyze_price_action
    import config
except ImportError as e:
    print(f"Error importando módulos legacy: {e}")
    print("Asegúrate de que los archivos originales estén en la raíz del proyecto")

logger = get_logger(__name__)


class TradingAlgorithm:
    """
    Algoritmo de trading de 5 pasos que integra:
    1. Identificación del activo
    2. Regresión lineal (30 días)
    3. Panel de expertos técnicos
    4. Análisis con IA
    5. Veredicto final consolidado
    """
    
    def __init__(self):
        self.mt5_conn = MT5Connection()
        self.db = Database()
        logger.info("TradingAlgorithm inicializado")
    
    def _get_recent_data(self, symbol: str, n: int = 500) -> Optional[pd.DataFrame]:
        """
        Obtiene datos recientes (M5) para análisis técnico.
        
        CRÍTICO: Siempre descarga mínimo 500 velas para alimentar el Panel de Expertos.
        El Modo Scalper NO afecta la descarga de datos, solo la decisión final de IA.
        
        Args:
            symbol: Símbolo a analizar
            n: Número de velas (default: 500 - suficiente para EMA37 y todos los indicadores)
            
        Returns:
            DataFrame con datos o None
        """
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, n)
            if rates is None or len(rates) == 0:
                logger.error(f"No se pudieron obtener datos de {symbol}")
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            logger.info(f"📊 Datos obtenidos: {len(df)} velas M5 (suficiente para panel de expertos)")
            return df
        except Exception as e:
            logger.error(f"Error obteniendo datos recientes: {e}")
            return None
    
    def _get_history_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """
        Obtiene datos históricos (M5) para regresión lineal.
        
        Args:
            symbol: Símbolo a analizar
            days: Número de días (default: 30)
            
        Returns:
            DataFrame con datos o None
        """
        # M5: 12 velas/hora × 24 horas = 288 velas/día
        n = days * 288  # 30 días = 8640 velas M5
        return self.mt5_conn.get_market_data(symbol, mt5.TIMEFRAME_M5, n)
    
    def _detect_asset_type(self, symbol: str) -> str:
        """Detecta el tipo de activo y retorna descripción"""
        symbol_upper = symbol.upper()
        
        if symbol_upper.startswith('B') or 'BOOM' in symbol_upper:
            return "BOOM"
        elif symbol_upper.startswith('C') or 'CRASH' in symbol_upper:
            return "CRASH"
        elif 'STEP' in symbol_upper and 'RISE' in symbol_upper:
            return "STEP_RISE"
        elif 'STEP' in symbol_upper and 'DROP' in symbol_upper:
            return "STEP_DROP"
        elif symbol_upper.startswith('V') or 'VOLATILITY' in symbol_upper:
            return "VOLATILITY"
        elif 'XAU' in symbol_upper or 'GOLD' in symbol_upper:
            return "XAUUSD"
        else:
            return "GENERIC"
    
    def _validate_signal_compatibility(self, signal: str, symbol: str) -> tuple[bool, str]:
        """
        Valida que la señal sea compatible con el tipo de activo.
        
        Args:
            signal: 'COMPRA', 'VENTA', 'ESPERAR'
            symbol: Nombre del símbolo
            
        Returns:
            (is_valid, reason)
        """
        asset_type = self._detect_asset_type(symbol)
        
        if signal == "COMPRA":
            if asset_type == "CRASH":
                return False, "⚠️ BLOQUEADO: Señal de COMPRA NO permitida en activo CRASH"
        elif signal == "VENTA":
            if asset_type == "BOOM":
                return False, "⚠️ BLOQUEADO: Señal de VENTA NO permitida en activo BOOM"
        
        return True, "Señal compatible con tipo de activo"
    
    def _is_boom_index(self, symbol: str) -> bool:
        """
        Detecta si el símbolo es un índice Boom.
        Boom genera spikes alcistas, solo operar BUY en modo scalper.
        """
        boom_keywords = ['Boom 300', 'Boom 500', 'Boom 600', 'Boom 900', 'Boom 1000']
        return any(keyword.lower() in symbol.lower() for keyword in boom_keywords)
    
    def _is_crash_index(self, symbol: str) -> bool:
        """
        Detecta si el símbolo es un índice Crash.
        Crash genera spikes bajistas, solo operar SELL en modo scalper.
        """
        crash_keywords = ['Crash 300', 'Crash 500', 'Crash 600', 'Crash 900', 'Crash 1000']
        return any(keyword.lower() in symbol.lower() for keyword in crash_keywords)
    
    def _verify_previous_prediction(self, symbol: str, current_price: float) -> dict:
        """
        Verifica si la predicción anterior fue acertada comparando con el precio actual.
        
        Returns:
            {
                'had_prediction': bool,
                'was_accurate': bool,
                'confidence_adjustment': int,  # +5 o -5
                'details': str
            }
        """
        try:
            # Obtener último análisis con predicción
            last_analysis = self.db.get_last_analysis(symbol)
            
            if not last_analysis or not last_analysis.get('prediction'):
                return {
                    'had_prediction': False,
                    'was_accurate': None,
                    'confidence_adjustment': 0,
                    'details': 'Sin predicción previa'
                }
            
            prediction = last_analysis['prediction']
            predicted_price = prediction.get('target_price', 0)
            predicted_direction = prediction.get('prediction', '')
            probability = prediction.get('probability', 0)
            
            # Calcular diferencia en pips
            symbol_info = self.mt5_conn.get_symbol_info(symbol)
            if symbol_info:
                point = symbol_info.get('point', 0.00001)
                price_diff_pips = int((current_price - predicted_price) / point)
            else:
                price_diff_pips = 0
            
            # Tolerancia: 50 pips
            accuracy_threshold = 50
            
            # Verificar acierto según dirección predicha
            was_accurate = False
            
            if 'alcista' in predicted_direction.lower() or 'spike' in predicted_direction.lower():
                # Predicción alcista: precio debe haber subido
                was_accurate = price_diff_pips > -accuracy_threshold
            elif 'bajista' in predicted_direction.lower() or 'corrección' in predicted_direction.lower():
                # Predicción bajista: precio debe haber bajado
                was_accurate = price_diff_pips < accuracy_threshold
            else:
                # Consolidación: precio debe estar cerca
                was_accurate = abs(price_diff_pips) < accuracy_threshold
            
            # Ajuste de confianza
            adjustment = +5 if was_accurate else -5
            
            details = f"{'✅ ACERTADA' if was_accurate else '❌ FALLIDA'}: {predicted_direction} @ {predicted_price} (actual: {current_price})"
            
            return {
                'had_prediction': True,
                'was_accurate': was_accurate,
                'confidence_adjustment': adjustment,
                'details': details
            }
        
        except Exception as e:
            logger.error(f"Error verificando predicción anterior: {e}")
            return {
                'had_prediction': False,
                'was_accurate': None,
                'confidence_adjustment': 0,
                'details': f'Error: {e}'
            }
    
    def _get_prediction(self, symbol: str, recent_data: pd.DataFrame, 
                       current_analysis: dict) -> dict:
        """
        Genera pronóstico IA para próximas 3-5 velas M5 (15 min).
        
        TIMEOUT: 10 segundos para evitar congelamiento si Ollama no responde.
        
        Returns:
            {
                'prediction': str,
                'timeframe': str,
                'probability': int,
                'target_price': float,
                'rationale': str
            }
        """
        try:
            # Import AI query function (supports multiple providers: Ollama, Cloudflare)
            from sentiment_analysis import query_ai
            
            if recent_data is None or recent_data.empty:
                return self._get_default_prediction(recent_data)
            
            last_close = recent_data['close'].iloc[-1]
            
            # Obtener indicadores actuales
            rsi = current_analysis.get('paso3', {}).get('rsi', 50)
            macd_signal = current_analysis.get('paso3', {}).get('macd', 'NEUTRAL')
            trend = current_analysis.get('paso2', {}).get('tendencia', 'NEUTRAL')
            
            # Construir prompt
            prompt = f"""Eres un analista técnico experto en predicción de precios.

DATOS ACTUALES ({symbol}):
- Precio actual: {last_close}
- RSI: {rsi}
- MACD: {macd_signal}
- Tendencia macro: {trend}

TAREA:
Predice el movimiento del precio para las próximas 3-5 velas M5 (próximos 15 minutos).

Responde SOLO en formato JSON (sin markdown):
{{
    "prediction": "Spike alcista esperado" o "Corrección bajista" o "Consolidación lateral",
    "probability": 0-100,
    "target_price": precio objetivo numérico,
    "rationale": "razón técnica breve"
}}"""
            
            # Llamar Ollama con TIMEOUT de 10 segundos
            import threading
            
            response_container = {'text': None, 'error': None}
            
            def call_ollama():
                try:
                    response_container['text'] = query_ai(prompt)
                except Exception as e:
                    response_container['error'] = str(e)
            
            thread = threading.Thread(target=call_ollama)
            thread.daemon = True
            thread.start()
            thread.join(timeout=10.0)  # ← TIMEOUT 10 segundos
            
            if thread.is_alive():
                logger.warning("⚠️ Ollama timeout (10s), usando predicción por defecto")
                return self._get_default_prediction(recent_data)
            
            if response_container['error']:
                logger.error(f"Error en Ollama: {response_container['error']}")
                return self._get_default_prediction(recent_data)
            
            response_text = response_container['text']
            
            if response_text:
                import json
                # Limpiar markdown si existe
                clean_text = response_text.strip()
                if clean_text.startswith('```'):
                    clean_text = clean_text.split('```')[1]
                    if clean_text.startswith('json'):
                        clean_text = clean_text[4:]
                
                response = json.loads(clean_text)
                
                return {
                    'prediction': response.get('prediction', 'Consolidación'),
                    'timeframe': '15 minutos (3-5 velas M5)',
                    'probability': int(response.get('probability', 50)),
                    'target_price': float(response.get('target_price', last_close)),
                    'rationale': response.get('rationale', 'Análisis técnico')
                }
            
            return self._get_default_prediction(recent_data)
        
        except Exception as e:
            logger.error(f"Error en _get_prediction: {e}")
            return self._get_default_prediction(recent_data)
    
    def _get_default_prediction(self, recent_data: Optional[pd.DataFrame]) -> dict:
        """Retorna predicción por defecto si Ollama falla"""
        last_close = recent_data['close'].iloc[-1] if recent_data is not None and not recent_data.empty else 0
        
        return {
            'prediction': 'Consolidación lateral (Ollama no disponible)',
            'timeframe': '15 minutos (3-5 velas M5)',
            'probability': 50,
            'target_price': last_close,
            'rationale': 'Predicción neutral por timeout/error en IA'
        }
    
    def analyze_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Ejecuta el análisis completo de 5 pasos.
        
        Args:
            symbol: Símbolo a analizar
            
        Returns:
            Dict con el resultado completo del análisis
        """
        logger.info(f"="*70)
        logger.info(f" INICIANDO ANÁLISIS: {symbol}")
        logger.info(f"="*70)
        
        # Indicar si está en modo scalper
        scalper_mode = self.db.get_setting('scalper_mode', False)
        if scalper_mode:
            logger.info("🎯 MODO SCALPER ACTIVO - Enfoque en últimos 15 minutos M5")
            logger.info(f"="*70)
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now(),
        }
        
        # ==================== VERIFICACIÓN PREDICCIÓN ANTERIOR ====================
        recent_data = self._get_recent_data(symbol)
        
        if recent_data is not None and not recent_data.empty:
            current_price = recent_data['close'].iloc[-1]
            
            verification = self._verify_previous_prediction(symbol, current_price)
            
            if verification['had_prediction']:
                logger.info(f"\n📊 VERIFICACIÓN PREDICCIÓN ANTERIOR:")
                logger.info(f"   {verification['details']}")
                logger.info(f"   Ajuste confianza: {verification['confidence_adjustment']:+d}%")
                
                # Guardar resultado de verificación
                result['prediction_verification'] = verification
            else:
                result['prediction_verification'] = verification
        
        # ==================== PASO 1: Obtener Datos Recientes ====================
        result['error'] = None
        result['paso1'] = {}
        result['paso2'] = {}
        result['paso3'] = {}
        result['paso4'] = {}
        result['paso5'] = {}
        result['final_action'] = 'ESPERAR'
        result['confidence'] = 0
        result['reasoning'] = ''
        
        # Verificar conexión MT5
        if not self.mt5_conn.is_connected():
            result['error'] = "No conectado a MT5"
            logger.error("❌ No conectado a MT5")
            return result
        
        # ==================== PASO 1: Identificación del Activo ====================
        logger.info(f"\n[PASO 1] ACTIVO BAJO ANÁLISIS:")
        asset_type = self._detect_asset_type(symbol)
        
        result['paso1'] = {
            'symbol': symbol,
            'asset_type': asset_type,
            'market': 'Índices Sintéticos (Deriv)',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f" → SÍMBOLO: {symbol}")
        logger.info(f" → TIPO: {asset_type}")
        logger.info(f" → MERCADO: Índices Sintéticos (Deriv)")
        
        # Obtener datos (M5 con suficientes velas para indicadores)
        df_recent = self._get_recent_data(symbol, n=200)  # 200 velas M5 = ~16.7 horas
        df_history = self._get_history_data(symbol)  # 8640 velas M5 = 30 días
        
        if df_recent is None or df_history is None:
            result['error'] = "No se pudieron recuperar datos de MT5"
            logger.error("❌ No se pudieron recuperar datos suficientes de MT5")
            return result
        
        # ==================== PASO 2: Regresión Lineal ====================
        logger.info(f"\n[PASO 2] ANÁLISIS DE REGRESIÓN LINEAL (30 DÍAS):")
        
        try:
            reg_res = get_monthly_probability(df_history)
            result['paso2'] = reg_res if reg_res else {}
            
            if reg_res:
                logger.info(f" → Tendencia: {reg_res['tendencia']}")
                logger.info(f" → Confianza R²: {reg_res['confianza']}%")
                logger.info(f" → RECOMENDACIÓN: {reg_res['recomendacion']}")
        except Exception as e:
            logger.error(f"❌ Error en regresión: {e}")
            result['paso2'] = {'error': str(e)}
        
        # ==================== PASO 3: Panel de Expertos Técnicos ====================
        logger.info(f"\n[PASO 3] PANEL DE EXPERTOS TÉCNICOS (M5):")
        
        try:
            tech = get_technical_summary(df_recent)
            result['paso3'] = tech
            
            if "error" not in tech:
                exp_list = tech.get('experts', {})
                
                # Logging detallado de CADA experto
                logger.info(f" → [E1] RSI ({tech.get('rsi')}): {exp_list.get('RSI')}")
                logger.info(f" → [E2] EMA Cross: {exp_list.get('EMA_CROSS')}")
                logger.info(f" → [E3] MACD ({tech.get('macd')}): {exp_list.get('MACD')}")
                logger.info(f" → [E4] Bollinger: {exp_list.get('BOLLINGER')}")
                logger.info(f" → [E5] Heikin Ashi ({tech.get('heikin_ashi')}): {exp_list.get('HEIKIN_ASHI')}")
                logger.info(f" → [E6] Estocástico ({tech.get('stoch_k')}): {exp_list.get('STOCHASTIC')}")
                logger.info(f" → [E7] Micro S/R: {exp_list.get('MICRO_SR')}")
                logger.info(f" → [E8] Volatilidad: {exp_list.get('VOLATILITY')}")
                logger.info(f" → [E9] Volumen: {exp_list.get('VOLUME')}")
                
                # Conteo de votos
                buys = sum(1 for v in exp_list.values() if v == "COMPRA")
                sells = sum(1 for v in exp_list.values() if v == "VENTA")
                waits = sum(1 for v in exp_list.values() if v == "ESPERAR")
                
                logger.info(f" → Votos: COMPRA={buys}, VENTA={sells}, ESPERAR={waits}")
                logger.info(f" ═► VEREDICTO PANEL ({tech.get('confianza_matematica', 0)}%): {tech.get('veredicto_matematico')}")
            else:
                logger.warning(f"⚠️ Error en panel técnico: {tech.get('error')}")
                # Asegurar claves mínimas
                if 'veredicto_matematico' not in tech:
                    tech['veredicto_matematico'] = 'NEUTRAL'
                    tech['confianza_matematica'] = 0

        except Exception as e:
            logger.error(f"❌ Error crítico en panel técnico: {e}")
            result['paso3'] = {
                'error': str(e), 
                'veredicto_matematico': 'NEUTRAL',
                'confianza_matematica': 0
            }
        
        # ==================== PASO 4: Análisis con IA ====================
        logger.info(f"\n[PASO 4] ANÁLISIS DE IA:")
        
        try:
            # Construir contexto
            contexto_ia = f"""
            ESTADO DE CONFIANZA DEL SISTEMA:
            1. Regresión Macro: {result['paso2'].get('confianza', 0)}% - {result['paso2'].get('tendencia', 'N/A')}
            2. Panel Técnico: {tech.get('confianza_matematica', 0)}% - {tech.get('veredicto_matematico', 'N/A')}
            
            DETALLES TÉCNICOS:
            - RSI: {tech.get('rsi', 'N/A')}
            - MACD: {tech.get('macd', 'N/A')}
            - Heikin Ashi: {tech.get('heikin_ashi', 'N/A')}
            - EMA Strategy: {tech.get('experts', {}).get('EMA_CROSS', 'N/A')}
            - Estocástico: {tech.get('stoch_k', 'N/A')}
            """
            
            ai_res = analyze_price_action(symbol, contexto_ia)
            result['paso4'] = ai_res
            
            if "error" not in ai_res:
                logger.info(f" → SEÑAL IA: {ai_res.get('señal')}")
                logger.info(f" → CONFIANZA IA: {ai_res.get('confianza')}%")
                logger.info(f" → RAZÓN: {ai_res.get('razon')}")
            else:
                logger.warning(f" → IA NO DISPONIBLE: {ai_res.get('error')}")
        except Exception as e:
            logger.error(f"❌ Error en análisis IA: {e}")
            result['paso4'] = {'error': str(e), 'señal': 'ESPERAR', 'confianza': 0}
        
        # ==================== PASO 5: Veredicto Final ====================
        logger.info(f"\n[PASO 5] VEREDICTO FINAL CONSOLIDADO:")
        logger.info("="*70)
        
        reg_dir = result['paso2'].get('tendencia', 'NEUTRO')
        ai_signal = result['paso4'].get('señal', 'ESPERAR')
        panel_dir = result['paso3'].get('veredicto_matematico', 'NEUTRAL')
        # ==================== PASO 5: Decisión Final ====================
        logger.info(f"\n[PASO 5] DECISIÓN FINAL:")
        
        # Extraer señales
        reg_dir = result['paso2'].get('tendencia', 'NEUTRAL')
        reg_conf = result['paso2'].get('confianza', 0)
        
        # CRÍTICO: Soportar ambas claves (español e inglés) para compatibilidad
        paso4_data = result.get('paso4', {})
        ai_signal = paso4_data.get('signal', paso4_data.get('señal', 'ESPERAR'))
        ai_conf = paso4_data.get('confidence', paso4_data.get('confianza', 0))
        
        # VALIDACIÓN CRÍTICA: Umbral de confianza desde BD
        min_confidence = self.db.get_setting('min_confidence_ia', 70)
        logger.debug(f"[DEBUG] Confianza calculada: {ai_conf}% | Umbral requerido: {min_confidence}%")

        
        # ==================== VALIDACIÓN ESPECIAL: Dirección en Modo Scalper ====================
        scalper_mode = self.db.get_setting('scalper_mode', False)
        
        if scalper_mode:
            is_boom = self._is_boom_index(symbol)
            is_crash = self._is_crash_index(symbol)
            
            # Boom solo permite BUY
            if is_boom and ai_signal == "VENTA":
                final_action = "ESPERAR"
                razon_final = "[SCALPING] Señal bloqueada: Dirección contraria al spike del índice (Boom requiere BUY)"
                logger.warning(razon_final)
                
                result['paso5'] = {
                    'decision': final_action,
                    'razon': razon_final,
                    'regresion': f"{reg_dir} ({reg_conf}%)",
                    'ia': f"{ai_signal} ({ai_conf}%)"
                }
                
                logger.info(f"✋ DECISIÓN: {final_action}")
                logger.info(f"   RAZÓN: {razon_final}")
                logger.info(f"="*70)
                
                return result
            
            # Crash solo permite SELL
            if is_crash and ai_signal == "COMPRA":
                final_action = "ESPERAR"
                razon_final = "[SCALPING] Señal bloqueada: Dirección contraria al spike del índice (Crash requiere SELL)"
                logger.warning(razon_final)
                
                result['paso5'] = {
                    'decision': final_action,
                    'razon': razon_final,
                    'regresion': f"{reg_dir} ({reg_conf}%)",
                    'ia': f"{ai_signal} ({ai_conf}%)"
                }
                
                logger.info(f"✋ DECISIÓN: {final_action}")
                logger.info(f"   RAZÓN: {razon_final}")
                logger.info(f"="*70)
                
                return result
        
        # CRÍTICO: Inicializar variables ANTES de condicionales
        final_action = "ESPERAR"  # Default seguro
        razon_final = "Sin señal clara"  # Default
        
        # Regla 0: Validar confianza mínima (PRIORITARIA)
        if ai_conf < min_confidence:
            final_action = "ESPERAR"
            razon_final = f"BLOQUEADO: Confianza IA ({ai_conf}%) < Umbral configurado ({min_confidence}%)"
            logger.warning(f"⚠️ {razon_final}")
        
        # Regla 1: Oposición directa → BLOQUEO
        elif (reg_dir == "ALCISTA" and ai_signal == "VENTA") or \
           (reg_dir == "BAJISTA" and ai_signal == "COMPRA"):
            final_action = "ESPERAR"
            razon_final = "BLOQUEO: IA y Regresión en direcciones OPUESTAS."
        
        # Regla 2: Alta confianza IA + Regresión alineada
        elif ai_conf >= 70 and \
             ((ai_signal == "COMPRA" and reg_dir == "ALCISTA") or \
              (ai_signal == "VENTA" and reg_dir == "BAJISTA")):
            final_action = ai_signal
            razon_final = f"EJECUCIÓN: Alta confianza IA ({ai_conf}%) alineada con Macro."
        
        # Regla 3: Consenso IA + Panel
        elif ai_signal == "COMPRA" and panel_dir == "ALCISTA":
            final_action = "COMPRA"
            razon_final = "EJECUCIÓN: Consenso IA y Panel Técnico."
        elif ai_signal == "VENTA" and panel_dir == "BAJISTA":
            final_action = "VENTA"
            razon_final = "EJECUCIÓN: Consenso IA y Panel Técnico."
        
        # Default: Si no se cumple ninguna regla, mantener ESPERAR
        else:
            final_action = "ESPERAR"
            razon_final = f"Sin confluencia clara. IA: {ai_signal} ({ai_conf}%), Regresión: {reg_dir}, Panel: {panel_dir}"
        
        # Validación de compatibilidad con tipo de activo
        is_valid, validation_msg = self._validate_signal_compatibility(final_action, symbol)
        
        if not is_valid:
            final_action = "ESPERAR"
            razon_final = validation_msg
        
        # ==================== CALCULAR CONFIANZA FINAL ====================
        # CRÍTICO: Usar confianza base + ajuste de predicción anterior
        
        verification = result.get('prediction_verification', {})
        confidence_adjustment = verification.get('confidence_adjustment', 0)
        
        # Confianza base: priorizar IA, fallback a panel técnico
        paso3_data = result.get('paso3', {})
        panel_confidence = paso3_data.get('confianza_matematica', 0)
        
        base_confidence = ai_conf if ai_conf > 0 else panel_confidence
        
        # Aplicar ajuste (+5%/-5% según acierto de predicción anterior)
        final_confidence = max(0, min(100, base_confidence + confidence_adjustment))
        
        # Guardar en paso5
        result['paso5'] = {
            'decision': final_action,
            'reasoning': razon_final,
            'base_confidence': base_confidence,
            'adjustment': confidence_adjustment,
            'final_confidence': final_confidence,
            'validation': validation_msg
        }
        
        result['final_action'] = final_action
        result['confidence'] = final_confidence
        result['reasoning'] = razon_final
        
        logger.info(f"\n[PASO 5] VEREDICTO FINAL CONSOLIDADO:")
        logger.info(f"======================================================================")
        logger.info(f"[PASO 5] DECISIÓN FINAL:")
        
        # Logging de confianza detallado
        if confidence_adjustment != 0:
            logger.info(f" → CONFIANZA BASE: {base_confidence}% (desde {'IA' if ai_conf > 0 else 'Panel'})")
            logger.info(f" → AJUSTE PREDICCIÓN: {confidence_adjustment:+d}% ({'✅ Acertada' if confidence_adjustment > 0 else '❌ Fallida'})")
            logger.info(f" → CONFIANZA FINAL: {final_confidence}%")
        else:
            logger.info(f" → CONFIANZA: {final_confidence}%")
        
        # Validar umbral de confianza
        umbral = self.db.get_setting('confidence_threshold', 50)
        
        if final_confidence < umbral:
            logger.warning(f"⚠️ BLOQUEADO: Confianza IA ({final_confidence}%) < Umbral configurado ({umbral}%)")
            result['final_action'] = "ESPERAR"
            result['reasoning'] = f"BLOQUEADO: Confianza IA ({final_confidence}%) < Umbral configurado ({umbral}%)"
            final_action = "ESPERAR"
            razon_final = result['reasoning']
        
        logger.info(f" → ACCIÓN FINAL: >>> {final_action} <<<")
        logger.info(f" → MOTIVO: {razon_final}")
        logger.info(f"======================================================================")
        
        # ==================== PASO 6: PRONÓSTICO FUTURO ====================
        logger.info(f"\n[PASO 6] PRONÓSTICO FUTURO (próximos 15 min):")
        
        try:
            prediction = self._get_prediction(symbol, df_recent, result) # Use df_recent for recent_data
            result['prediction'] = prediction
            
            logger.info(f"🎯 Predicción: {prediction.get('prediction', 'N/A')}")
            logger.info(f"   Probabilidad: {prediction.get('probability', 0)}%")
            logger.info(f"   Precio objetivo: {prediction.get('target_price', 0)}")
            logger.info(f"   Timeframe: {prediction.get('timeframe', 'N/A')}")
            logger.info(f"   Rationale: {prediction.get('rationale', 'N/A')}")
        except Exception as e:
            logger.error(f"❌ Error en Paso 6: {e}")
            result['prediction'] = {
                'prediction': 'Error en predicción',
                'timeframe': '15 minutos',
                'probability': 0,
                'target_price': 0,
                'rationale': f'Error: {str(e)}'
            }
        
        logger.info(f"======================================================================")
        
        return result
    
    def get_sl_tp_params(self, symbol: str) -> tuple[int, int]:
        """
        Retorna SL y TP en pips según el tipo de activo y ratio R:R configurado.
        
        Args:
            symbol: Símbolo
            
        Returns:
            (sl_pips, tp_pips)
        """
        asset_type = self._detect_asset_type(symbol)
        
        # Obtener ratio Riesgo:Beneficio desde BD (default: 3.0 = 1:3)
        risk_reward_ratio = self.db.get_setting('risk_reward_ratio', 3.0)
        
        # SL base según activo
        if asset_type == "XAUUSD":
            sl_pips = 1500  # Oro
        else:
            sl_pips = 1500  # Índices sintéticos
        
        # TP = SL × Ratio (ej: 1500 × 3 = 4500 pips)
        tp_pips = int(sl_pips * risk_reward_ratio)
        
        logger.debug(f"📊 SL/TP Params: SL={sl_pips} pips, TP={tp_pips} pips (Ratio 1:{risk_reward_ratio})")
        
        return sl_pips, tp_pips
