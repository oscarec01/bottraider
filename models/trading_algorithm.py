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
from models.strategy_engine import decide as strategy_decide
from models.expert_reputation import ExpertReputation
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
    
    def _prediction_direction(self, text: str) -> str:
        """Normaliza texto de predicción a ALCISTA | BAJISTA | LATERAL."""
        t = (text or "").lower()
        if any(k in t for k in ("omitido", "error", "n/a")):
            return "LATERAL"
        if any(k in t for k in ("bajista", "corrección", "correccion", "caída", "caida", "drop", "venta")):
            return "BAJISTA"
        if any(k in t for k in ("alcista", "spike", "subida", "rally", "compra", "rise")):
            return "ALCISTA"
        return "LATERAL"

    def _verify_previous_prediction(self, symbol: str, current_price: float) -> dict:
        """
        Evalúa la predicción pendiente cada 5–10 min según movimiento real del precio
        (desde reference_price), no contra un target absoluto. Autocorrije bias del símbolo.
        """
        import json
        from datetime import datetime as dt

        empty = {
            'had_prediction': False,
            'was_accurate': None,
            'confidence_adjustment': 0,
            'status': 'SIN_PREVIA',
            'details': 'Sin predicción previa',
        }
        try:
            key = f"pending_prediction::{symbol}"
            raw = self.db.get_setting(key, None)
            if not raw:
                return empty

            pred = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(pred, dict):
                return empty

            ref = float(pred.get('reference_price') or 0)
            if ref <= 0:
                return empty

            created = pred.get('created_at')
            try:
                created_dt = dt.fromisoformat(created) if created else None
            except ValueError:
                created_dt = None
            if not created_dt:
                return empty

            age_sec = (dt.now() - created_dt).total_seconds()
            check_sec = int(self.db.get_setting('prediction_check_sec', 420) or 420)  # ~7 min
            horizon_sec = int(pred.get('horizon_sec') or self.db.get_setting('prediction_horizon_sec', 600) or 600)

            direction = pred.get('direction') or self._prediction_direction(pred.get('prediction', ''))
            move_pct = ((current_price - ref) / ref) * 100.0 if ref else 0.0
            # Umbral mínimo de movimiento para no marcar ruido como acierto/fallo
            min_move = float(self.db.get_setting('prediction_min_move_pct', 0.015) or 0.015)

            # Aún temprano: informar progreso, sin castigar confianza
            if age_sec < check_sec:
                left = int(check_sec - age_sec)
                return {
                    'had_prediction': True,
                    'was_accurate': None,
                    'confidence_adjustment': 0,
                    'status': 'EVALUANDO',
                    'details': (
                        f"Evaluando {direction}: {int(age_sec)}s / {check_sec}s "
                        f"(queda {left}s) | move={move_pct:+.4f}%"
                    ),
                    'age_sec': int(age_sec),
                    'move_pct': round(move_pct, 5),
                    'direction': direction,
                }

            # Dirección real observada
            if abs(move_pct) < min_move:
                observed = "LATERAL"
            elif move_pct > 0:
                observed = "ALCISTA"
            else:
                observed = "BAJISTA"

            if direction == "LATERAL":
                was_accurate = observed == "LATERAL"
            else:
                was_accurate = observed == direction

            # Peso: más ajuste si ya pasó el horizonte o el move es claro
            strength = min(15, max(5, int(abs(move_pct) / max(min_move, 1e-6) * 3)))
            if age_sec >= horizon_sec:
                strength = min(15, strength + 3)
            adjustment = strength if was_accurate else -strength

            # Autocorrección: bias del símbolo hacia lo que el mercado hizo
            bias_key = f"pred_bias::{symbol}"
            streak_key = f"pred_streak::{symbol}"
            bias = int(self.db.get_setting(bias_key, 0) or 0)
            streak = int(self.db.get_setting(streak_key, 0) or 0)
            if was_accurate:
                streak = streak + 1 if streak > 0 else 1
                if direction == "ALCISTA":
                    bias = min(20, bias + 2)
                elif direction == "BAJISTA":
                    bias = max(-20, bias - 2)
            else:
                streak = streak - 1 if streak < 0 else -1
                # Mercado contradijo → empujar bias hacia lo observado
                if observed == "ALCISTA":
                    bias = min(20, bias + 4)
                elif observed == "BAJISTA":
                    bias = max(-20, bias - 4)
                else:
                    bias = int(bias * 0.5)
            self.db.save_setting(bias_key, bias)
            self.db.save_setting(streak_key, streak)

            # Premiar/castigar expertos con el mismo movimiento
            try:
                ExpertReputation(self.db).evaluate_pending(symbol, current_price, min_move)
            except Exception as rep_err:
                logger.debug(f"reputación expertos: {rep_err}")

            # Cerrar predicción pendiente (se creará una nueva en Paso 6)
            self.db.save_setting(key, None)

            label = "ACERTADA" if was_accurate else "FALLIDA"
            details = (
                f"{label}: pred={direction} obs={observed} "
                f"ref={ref:.5f}→{current_price:.5f} ({move_pct:+.4f}%) "
                f"edad={int(age_sec)}s bias={bias:+d}"
            )
            return {
                'had_prediction': True,
                'was_accurate': was_accurate,
                'confidence_adjustment': adjustment,
                'status': label,
                'details': details,
                'age_sec': int(age_sec),
                'move_pct': round(move_pct, 5),
                'direction': direction,
                'observed': observed,
                'bias': bias,
            }
        except Exception as e:
            logger.error(f"Error verificando predicción anterior: {e}")
            return {
                'had_prediction': False,
                'was_accurate': None,
                'confidence_adjustment': 0,
                'status': 'ERROR',
                'details': f'Error: {e}',
            }

    def _build_technical_prediction(self, symbol: str, recent_data: pd.DataFrame,
                                    current_analysis: dict) -> dict:
        """
        Pronóstico técnico corto (5–10 min) sin IA. Usa RSI/tendencia/panel + bias autocorregido.
        """
        from datetime import datetime as dt

        last_close = float(recent_data['close'].iloc[-1]) if recent_data is not None and not recent_data.empty else 0.0
        rsi = float(current_analysis.get('paso3', {}).get('rsi', 50) or 50)
        trend = current_analysis.get('paso2', {}).get('tendencia', 'NEUTRAL')
        trend_conf = float(current_analysis.get('paso2', {}).get('confianza', 0) or 0)
        panel = current_analysis.get('paso3', {}).get('veredicto_matematico', 'NEUTRAL')
        asset = self._detect_asset_type(symbol)
        bias = int(self.db.get_setting(f"pred_bias::{symbol}", 0) or 0)

        score = 0  # + alcista, - bajista
        reasons = []

        if trend == "ALCISTA" and trend_conf >= 40:
            score += 2
            reasons.append(f"reg ALCISTA {trend_conf:.0f}%")
        elif trend == "BAJISTA" and trend_conf >= 40:
            score -= 2
            reasons.append(f"reg BAJISTA {trend_conf:.0f}%")

        if panel == "ALCISTA":
            score += 2
            reasons.append("panel ALCISTA")
        elif panel == "BAJISTA":
            score -= 2
            reasons.append("panel BAJISTA")

        if rsi >= 70:
            score -= 2
            reasons.append(f"RSI sobrecompra {rsi:.1f}")
        elif rsi <= 30:
            score += 2
            reasons.append(f"RSI sobreventa {rsi:.1f}")
        elif rsi >= 55:
            score += 1
        elif rsi <= 45:
            score -= 1

        # Mecánica Boom/Crash: sesgo de spike, no de drift
        if asset == "BOOM" and rsi <= 40:
            score += 2
            reasons.append("Boom dip→spike")
        if asset == "CRASH" and rsi >= 60:
            score -= 2
            reasons.append("Crash rally→spike")

        # Autocorrección del bias aprendido
        if bias >= 6:
            score += 1
            reasons.append(f"bias mercado +{bias}")
        elif bias <= -6:
            score -= 1
            reasons.append(f"bias mercado {bias}")

        if score >= 2:
            direction = "ALCISTA"
            label = "Continuación alcista" if asset != "BOOM" else "Spike alcista esperado"
        elif score <= -2:
            direction = "BAJISTA"
            label = "Corrección bajista" if asset != "CRASH" else "Spike bajista esperado"
        else:
            direction = "LATERAL"
            label = "Consolidación lateral"

        # Target aproximado ~0.05% (sintéticos) / 0.02% oro
        move = 0.0005 if asset != "XAUUSD" else 0.0002
        if direction == "ALCISTA":
            target = last_close * (1 + move)
        elif direction == "BAJISTA":
            target = last_close * (1 - move)
        else:
            target = last_close

        horizon = int(self.db.get_setting('prediction_horizon_sec', 600) or 600)
        probability = min(85, max(40, 50 + abs(score) * 8 + min(10, abs(bias))))

        return {
            'prediction': label,
            'direction': direction,
            'timeframe': f'{horizon // 60} min (auto-check ~5-10 min)',
            'probability': int(probability),
            'target_price': float(round(target, 5)),
            'reference_price': float(last_close),
            'created_at': dt.now().isoformat(),
            'horizon_sec': horizon,
            'rationale': '; '.join(reasons) if reasons else 'Señales mixtas',
            'source': 'technical',
        }

    def _store_pending_prediction(self, symbol: str, prediction: dict) -> None:
        """Guarda predicción pendiente solo si no hay una en evaluación."""
        import json
        key = f"pending_prediction::{symbol}"
        existing = self.db.get_setting(key, None)
        if existing:
            # Mantener la pendiente hasta que se evalúe (5–10 min)
            return
        # No guardar predicciones vacías / omitidas
        if not prediction or not prediction.get('direction'):
            return
        if prediction.get('probability', 0) <= 0 and 'Omitido' in str(prediction.get('prediction', '')):
            return
        self.db.save_setting(key, json.dumps(prediction))
    
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
        """Fallback mínimo; preferir _build_technical_prediction cuando haya análisis."""
        from datetime import datetime as dt
        last_close = recent_data['close'].iloc[-1] if recent_data is not None and not recent_data.empty else 0
        return {
            'prediction': 'Consolidación lateral',
            'direction': 'LATERAL',
            'timeframe': '10 min',
            'probability': 45,
            'target_price': float(last_close),
            'reference_price': float(last_close),
            'created_at': dt.now().isoformat(),
            'horizon_sec': 600,
            'rationale': 'Fallback neutral',
            'source': 'default',
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
        
        # Obtener datos (periodos desde BD si están configurados)
        freq_fast = bool(self.db.get_setting('frequency_scalp_mode', False))
        tech_bars = int(self.db.get_setting('technical_period', 200))
        # Modo volátil: menos velas = ciclos más rápidos (sin IA)
        tech_bars = max(80, min(tech_bars, 120 if freq_fast else 500))
        regression_days = int(self.db.get_setting('regression_period', 30))
        # En frecuencia: regresión corta (3 días) — suficiente y mucho más rápida
        if freq_fast:
            regression_days = min(regression_days, 3)
        regression_days = max(2, min(regression_days, 90))

        df_recent = self._get_recent_data(symbol, n=tech_bars)
        df_history = self._get_history_data(symbol, days=regression_days)
        
        if df_recent is None or df_history is None:
            result['error'] = "No se pudieron recuperar datos de MT5"
            logger.error("❌ No se pudieron recuperar datos suficientes de MT5")
            return result
        
        # ==================== PASO 2: Regresión Lineal ====================
        logger.info(f"\n[PASO 2] ANÁLISIS DE REGRESIÓN LINEAL ({regression_days} DÍAS M5):")
        
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
            expert_consensus = int(self.db.get_setting('expert_consensus', 5))
            expert_consensus = max(4, min(expert_consensus, 10))
            rep = ExpertReputation(self.db)
            tech = get_technical_summary(
                df_recent,
                consensus_threshold=expert_consensus,
                expert_weights=rep.get_weights(),
            )
            result['paso3'] = tech
            
            if "error" not in tech:
                exp_list = tech.get('experts', {})
                # Snapshot para premio/castigo cuando se evalúe la predicción
                try:
                    px = float(df_recent['close'].iloc[-1])
                    rep.snapshot_votes(symbol, exp_list, px)
                except Exception:
                    pass
                
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
        skip_ia = bool(self.db.get_setting('frequency_scalp_mode', False)) and bool(
            self.db.get_setting('frequency_skip_ia', True)
        )
        if skip_ia:
            result['paso4'] = {
                'señal': 'ESPERAR', 'signal': 'ESPERAR',
                'confianza': 0, 'confidence': 0,
                'razon': 'IA omitida (modo frecuencia — más ops/minuto)',
            }
            logger.info(" → IA omitida (modo frecuencia)")
        else:
            try:
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
        
        # ==================== PASO 5: Motor de estrategia (edge por tipo de activo) ====================
        logger.info(f"\n[PASO 5] DECISIÓN FINAL (strategy_engine):")
        logger.info("=" * 70)

        paso4_data = result.get('paso4', {})
        ai_signal = paso4_data.get('signal', paso4_data.get('señal', 'ESPERAR'))
        ai_conf = float(paso4_data.get('confidence', paso4_data.get('confianza', 0)) or 0)
        reg_dir = result['paso2'].get('tendencia', 'NEUTRAL')
        reg_conf = result['paso2'].get('confianza', 0)
        panel_dir = result['paso3'].get('veredicto_matematico', 'NEUTRAL')

        freq_mode = bool(self.db.get_setting('frequency_scalp_mode', False))
        capital = bool(self.db.get_setting('capital_preservation', False))
        # Si "no perder" está ON, anula la agresividad del modo frecuencia
        if capital:
            freq_mode = False
        strategy_settings = {
            'min_confidence_ia': self.db.get_setting('min_confidence_ia', 70),
            # Modo frecuencia: umbrales más bajos → más operaciones
            'min_setup_score': self.db.get_setting(
                'min_setup_score', 35 if freq_mode else (70 if capital else 55)
            ),
            'require_ai_alignment': self.db.get_setting(
                'require_ai_alignment', False if freq_mode else True
            ),
            # En frecuencia la IA ralentiza: opcionalmente se puede dejar OFF
            'enable_ia': self.db.get_setting('enable_ia', not freq_mode),
            'frequency_scalp_mode': freq_mode,
            'capital_preservation': capital,
        }
        if capital:
            strategy_settings['min_setup_score'] = max(
                int(strategy_settings['min_setup_score']), 70
            )
            strategy_settings['require_ai_alignment'] = False
        elif freq_mode:
            strategy_settings['min_setup_score'] = min(
                int(strategy_settings['min_setup_score']), 40
            )
            strategy_settings['require_ai_alignment'] = False
            if bool(self.db.get_setting('frequency_skip_ia', True)):
                strategy_settings['enable_ia'] = False

        # Si IA deshabilitada, no bloquear por señales IA
        if not strategy_settings['enable_ia']:
            result['paso4'] = {
                'señal': 'ESPERAR', 'signal': 'ESPERAR',
                'confianza': 0, 'confidence': 0,
                'razon': 'IA deshabilitada en configuración',
            }
            paso4_data = result['paso4']

        decision = strategy_decide(
            symbol=symbol,
            asset_type=asset_type,
            paso2=result.get('paso2', {}),
            paso3=result.get('paso3', {}),
            paso4=paso4_data,
            df_recent=df_recent,
            settings=strategy_settings,
        )

        final_action = decision.action
        razon_final = decision.reason
        base_confidence = float(decision.confidence)

        # Compatibilidad Boom/Crash (doble red de seguridad)
        is_valid, validation_msg = self._validate_signal_compatibility(final_action, symbol)
        if not is_valid:
            final_action = "ESPERAR"
            razon_final = validation_msg

        verification = result.get('prediction_verification', {})
        confidence_adjustment = verification.get('confidence_adjustment', 0)
        final_confidence = max(0, min(100, base_confidence + confidence_adjustment))

        result['paso5'] = {
            'decision': final_action,
            'reasoning': razon_final,
            'mode': decision.mode,
            'setup_score': decision.setup_score,
            'base_confidence': base_confidence,
            'adjustment': confidence_adjustment,
            'final_confidence': final_confidence,
            'validation': validation_msg,
            'regresion': f"{reg_dir} ({reg_conf}%)",
            'panel': panel_dir,
            'ia': f"{ai_signal} ({ai_conf}%)",
        }

        result['final_action'] = final_action
        result['confidence'] = final_confidence
        result['reasoning'] = razon_final

        logger.info(f" → MODO: {decision.mode} | SETUP: {decision.setup_score}")
        logger.info(f" → Regresión: {reg_dir} ({reg_conf}%) | Panel: {panel_dir}")
        logger.info(f" → IA: {ai_signal} ({ai_conf}%)")
        if confidence_adjustment != 0:
            logger.info(f" → CONFIANZA BASE: {base_confidence}% | AJUSTE: {confidence_adjustment:+d}%")
        logger.info(f" → CONFIANZA FINAL: {final_confidence}%")

        capital = bool(self.db.get_setting('capital_preservation', False))
        freq_for_umbral = bool(self.db.get_setting('frequency_scalp_mode', False)) and not capital
        umbral = float(
            self.db.get_setting(
                'confidence_threshold',
                40 if freq_for_umbral else (65 if capital else 55),
            )
        )
        if capital:
            umbral = max(umbral, 65.0)
        if final_action in ("COMPRA", "VENTA") and final_confidence < umbral:
            logger.warning(
                f"⚠️ BLOQUEADO: Confianza ({final_confidence}%) < umbral ({umbral}%)"
            )
            final_action = "ESPERAR"
            razon_final = (
                f"BLOQUEADO: Confianza ({final_confidence}%) < umbral ({umbral}%)"
            )
            result['final_action'] = final_action
            result['reasoning'] = razon_final
            result['paso5']['decision'] = final_action
            result['paso5']['reasoning'] = razon_final

        logger.info(f" → ACCIÓN FINAL: >>> {final_action} <<<")
        logger.info(f" → MOTIVO: {razon_final}")
        logger.info("=" * 70)
        
        # ==================== PASO 6: PRONÓSTICO FUTURO (técnico 5–10 min) ====================
        logger.info(f"\n[PASO 6] PRONÓSTICO FUTURO (auto-check 5–10 min):")
        try:
            # Siempre técnico (rápido, autocorregible). IA opcional solo si no hay skip.
            prediction = self._build_technical_prediction(symbol, df_recent, result)
            if not skip_ia:
                try:
                    ai_pred = self._get_prediction(symbol, df_recent, result)
                    # Fusionar: dirección técnica manda; IA solo enriquece texto si coincide
                    ai_dir = self._prediction_direction(ai_pred.get('prediction', ''))
                    if ai_dir == prediction.get('direction') and ai_dir != 'LATERAL':
                        prediction['probability'] = min(
                            90, int(prediction['probability']) + 5
                        )
                        prediction['rationale'] = (
                            f"{prediction.get('rationale')}; IA confirma"
                        )
                except Exception:
                    pass
            result['prediction'] = prediction
            self._store_pending_prediction(symbol, prediction)
            logger.info(f" Predicción: {prediction.get('prediction', 'N/A')} [{prediction.get('direction')}]")
            logger.info(f"   Probabilidad: {prediction.get('probability', 0)}%")
            logger.info(f"   Ref/Target: {prediction.get('reference_price')} → {prediction.get('target_price')}")
            logger.info(f"   Rationale: {prediction.get('rationale', '')}")
        except Exception as e:
            logger.error(f"Error en Paso 6: {e}")
            result['prediction'] = self._get_default_prediction(df_recent)

        logger.info(f"======================================================================")
        
        return result
    
    def _compute_atr_sl_pips(self, symbol: str, multiplier: float = 1.8) -> Optional[int]:
        """Calcula SL en pips = ATR(14) M5 × multiplier (adaptativo a volatilidad)."""
        try:
            from technical_indicators import calculate_atr
            df = self._get_recent_data(symbol, n=80)
            if df is None or df.empty or len(df) < 20:
                return None
            atr = calculate_atr(df, 14).iloc[-1]
            if atr is None or float(atr) <= 0:
                return None
            info = self.mt5_conn.get_symbol_info(symbol)
            if not info:
                return None
            point = info.get('point') or 0.00001
            sl_pips = int((float(atr) * multiplier) / point)
            # En Boom/Crash el point es tiny (0.0001): un SL útil son decenas de miles
            # de points. No capar a 2500 (eso provoca 10016 Invalid stops).
            asset_type = self._detect_asset_type(symbol)
            stops_level = 0
            try:
                import MetaTrader5 as mt5
                si = mt5.symbol_info(symbol)
                if si:
                    stops_level = int(si.trade_stops_level or 0)
            except Exception:
                pass

            min_pts = max(stops_level, 1)
            if asset_type in ("BOOM", "CRASH"):
                sl_pips = max(min_pts, min(sl_pips, 200000))
            elif asset_type == "XAUUSD":
                sl_pips = max(200, min(sl_pips, 15000))
            else:
                sl_pips = max(min_pts, min(sl_pips, 100000))
            return sl_pips
        except Exception as e:
            logger.warning(f"No se pudo calcular ATR SL: {e}")
            return None

    def get_sl_tp_params(self, symbol: str) -> tuple[int, int]:
        """
        Retorna SL y TP en pips según settings BD + ATR opcional + R:R.
        
        Defaults realistas (el 1500 fijo anterior hacía TP inalcanzable en M5):
        - Sintéticos: sl_synthetics (500)
        - XAUUSD: sl_xauusd (300)
        - R:R default 2.0
        """
        asset_type = self._detect_asset_type(symbol)
        risk_reward_ratio = float(self.db.get_setting('risk_reward_ratio', 2.0))
        risk_reward_ratio = max(1.2, min(risk_reward_ratio, 4.0))

        if asset_type == "XAUUSD":
            sl_pips = int(self.db.get_setting('sl_xauusd', 300))
        else:
            sl_pips = int(self.db.get_setting('sl_synthetics', 500))

        use_atr = bool(self.db.get_setting('use_atr_stops', True))
        if use_atr:
            atr_sl = self._compute_atr_sl_pips(symbol)
            if atr_sl:
                # Mezcla: no dejar SL más estrecho que el configurado / 1.5
                sl_pips = max(int(sl_pips / 1.5), atr_sl)
                logger.info(f"📏 SL adaptativo ATR: {atr_sl} → usando {sl_pips} pips")

        # TP siempre derivado del R:R (más coherente que TP fijo desconectado del SL)
        tp_pips = int(sl_pips * risk_reward_ratio)

        # Modo frecuencia: SL/TP lo más cerca que permita el broker; el monitor
        # cierra por micro_$ mucho antes del TP lejano.
        if bool(self.db.get_setting('frequency_scalp_mode', False)):
            try:
                import MetaTrader5 as mt5
                si = mt5.symbol_info(symbol)
                if si and si.trade_stops_level:
                    min_pts = int(si.trade_stops_level * 1.15)
                    sl_pips = max(sl_pips, min_pts)
                    # TP corto (~1:1) para salidas rápidas si no actúa el micro-close
                    tp_pips = max(min_pts, int(sl_pips * 1.0))
                    logger.info(
                        f"Modo frecuencia: SL/TP apretados a stops broker "
                        f"SL={sl_pips} TP={tp_pips}"
                    )
            except Exception as e:
                logger.warning(f"No se pudo ajustar SL/TP frecuencia: {e}")

        logger.info(
            f"📊 SL/TP: SL={sl_pips} TP={tp_pips} (R:R 1:{risk_reward_ratio}, tipo={asset_type})"
        )
        return sl_pips, tp_pips
