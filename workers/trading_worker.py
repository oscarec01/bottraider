"""
Worker (QThread) para ejecutar análisis de trading de forma asíncrona.
Cada símbolo tiene su propio worker que corre independientemente.
"""

from PyQt6.QtCore import QThread, pyqtSignal
import time
import traceback
from typing import Dict, Any
import MetaTrader5 as mt5

from models.trading_algorithm import TradingAlgorithm
from models.mt5_connection import MT5Connection
from models.database import Database
from utils.logger import get_logger
import config

logger = get_logger(__name__)


class TradingWorker(QThread):
    """
    Worker thread para análisis y ejecución de trading.
    Cada instancia maneja un símbolo específico.
    """
    
    # Señales para comunicación con la UI
    analysis_started = pyqtSignal(str)  # symbol
    analysis_complete = pyqtSignal(str, dict)  # symbol, result
    trade_executed = pyqtSignal(str, dict)  # symbol, trade_data
    error_occurred = pyqtSignal(str, str)  # symbol, error_message
    status_update = pyqtSignal(str, str)  # symbol, status_message
    progress_update = pyqtSignal(str, int)  # symbol, percentage
    
    def __init__(self, symbol: str, interval: int = 120):
        """
        Args:
            symbol: Símbolo a analizar
            interval: Intervalo entre análisis en segundos (default: 120)
        """
        super().__init__()
        self.symbol = symbol
        self.interval = interval
        self._is_running = False
        self._is_paused = False
        
        # Instancias de modelo
        self.algorithm = TradingAlgorithm()
        self.mt5_conn = MT5Connection()
        self.db = Database()
        
        logger.info(f"TradingWorker creado para {symbol} (intervalo: {interval}s)")
    
    def run(self):
        """Método principal del thread"""
        self._is_running = True
        logger.info(f"🚀 Worker iniciado para {self.symbol}")
        
        self.status_update.emit(self.symbol, "Iniciando...")
        
        while self._is_running:
            try:
                # Si está pausado, esperar
                if self._is_paused:
                    time.sleep(1)
                    continue

                # Intervalo efectivo (modo frecuencia = ciclos cortos)
                freq_mode = bool(self.db.get_setting("frequency_scalp_mode", False))
                effective_interval = int(
                    self.db.get_setting(
                        "analysis_interval",
                        15 if freq_mode else self.interval,
                    )
                )
                if freq_mode:
                    # Sin IA: ciclos agresivos (8–15s)
                    effective_interval = max(
                        8,
                        min(
                            int(self.db.get_setting("analysis_interval", 10) or 10),
                            15,
                        ),
                    )
                
                # Verificar conexión MT5
                if not self.mt5_conn.is_connected():
                    self.error_occurred.emit(
                        self.symbol,
                        "No conectado a MT5. Worker en espera..."
                    )
                    time.sleep(10)
                    continue

                # Si hay posición abierta, en modo frecuencia: gestionar + tick predicción
                # (antes se saltaba el análisis y las cards quedaban en "Pendiente")
                open_here = self.mt5_conn.get_positions(self.symbol)
                if open_here and freq_mode:
                    self.status_update.emit(
                        self.symbol,
                        f"Gestionando pos #{open_here[0]['ticket']} "
                        f"(${open_here[0]['profit']:.2f})",
                    )
                    try:
                        self._tick_prediction_while_managing()
                    except Exception as tick_err:
                        logger.debug(f"tick predicción: {tick_err}")
                    time.sleep(2)
                    continue

                # Freno por racha de pérdidas (evita martingala accidental)
                cooldown_until = int(
                    self.db.get_setting(f"cooldown_until::{self.symbol}", 0) or 0
                )
                if cooldown_until and time.time() < cooldown_until:
                    left = int(cooldown_until - time.time())
                    self.status_update.emit(
                        self.symbol, f"Pausa anti-racha ({left}s)"
                    )
                    time.sleep(min(5, max(1, left)))
                    continue
                
                # ==================== ANÁLISIS ====================
                self.analysis_started.emit(self.symbol)
                self.status_update.emit(self.symbol, "Analizando...")
                self.progress_update.emit(self.symbol, 10)
                
                logger.info(f"📊 [{self.symbol}] Iniciando análisis...")
                
                # Ejecutar análisis de 5 pasos
                result = self.algorithm.analyze_symbol(self.symbol)
                
                self.progress_update.emit(self.symbol, 80)
                
                if result.get('error'):
                    self.error_occurred.emit(self.symbol, result['error'])
                    self.status_update.emit(self.symbol, f"Error: {result['error']}")
                else:
                    # Análisis completado
                    final_action = result['final_action']
                    confidence = result['confidence']
                    
                    logger.info(f"✅ [{self.symbol}] Análisis completo: {final_action} ({confidence}%)")
                    
                    # Guardar análisis en BD
                    self._save_analysis_to_db(result)
                    
                    # Emitir señal de análisis completo
                    self.analysis_complete.emit(self.symbol, result)
                    
                    # ==================== EJECUCIÓN ====================
                    if final_action in ["COMPRA", "VENTA"]:
                        if not self.db.get_setting('enable_auto_trading', True):
                            logger.info(
                                f"⏸ [{self.symbol}] Señal {final_action} pero "
                                f"auto-trading DESACTIVADO (solo análisis)"
                            )
                            self.status_update.emit(
                                self.symbol,
                                f"Señal {final_action} (auto-trading off)"
                            )
                            self.progress_update.emit(self.symbol, 100)
                            for _ in range(self.interval):
                                if not self._is_running or self._is_paused:
                                    break
                                time.sleep(1)
                            continue

                        # NO PERDER: solo 1 posición en toda la cuenta
                        if bool(self.db.get_setting('capital_preservation', False)):
                            all_pos = self.mt5_conn.get_positions() or []
                            max_total = int(
                                self.db.get_setting('max_total_positions', 1) or 1
                            )
                            if len(all_pos) >= max_total:
                                self.status_update.emit(
                                    self.symbol,
                                    f"NO PERDER: ya hay {len(all_pos)} pos abierta(s)",
                                )
                                self.progress_update.emit(self.symbol, 100)
                                time.sleep(self.interval)
                                continue

                        self.status_update.emit(
                            self.symbol,
                            f"Ejecutando {final_action}..."
                        )
                        
                        # Ejecutar orden
                        success, trade_data = self._execute_trade(final_action)
                        
                        if success:
                            logger.info(f"✅ [{self.symbol}] Orden ejecutada: {trade_data}")
                            self.trade_executed.emit(self.symbol, trade_data)
                            self.status_update.emit(
                                self.symbol,
                                f"✅ {final_action} ejecutada"
                            )
                            
                            # Guardar trade en BD
                            self._save_trade_to_db(trade_data)
                        else:
                            error_msg = trade_data.get('error', 'Error desconocido')
                            logger.error(f"❌ [{self.symbol}] Error en ejecución: {error_msg}")
                            self.error_occurred.emit(self.symbol, error_msg)
                            self.status_update.emit(
                                self.symbol,
                                f"❌ Error: {error_msg}"
                            )
                    else:
                        # ESPERAR
                        self.status_update.emit(
                            self.symbol,
                            f"⏸ Sin señal ({confidence}%)"
                        )
                
                self.progress_update.emit(self.symbol, 100)
                
                # ==================== ESPERA ====================
                # En modo frecuencia: pausa corta para encadenar muchas operaciones
                for _ in range(effective_interval):
                    if not self._is_running or self._is_paused:
                        break
                    time.sleep(1)
                
            except Exception as e:
                error_msg = f"Excepción en worker: {str(e)}"
                stack = traceback.format_exc()
                
                logger.error(f"❌ [{self.symbol}] {error_msg}")
                logger.error(stack)
                
                self.error_occurred.emit(self.symbol, error_msg)
                self.status_update.emit(self.symbol, f"❌ Error crítico")
                
                # Guardar error en BD
                self.db.log_error(
                    error_type="WorkerException",
                    error_message=error_msg,
                    symbol=self.symbol,
                    stack_trace=stack
                )
                
                # Esperar antes de reintentar
                time.sleep(30)
        
        logger.info(f"🛑 Worker detenido para {self.symbol}")
        self.status_update.emit(self.symbol, "Detenido")
    
    def _execute_trade(self, action: str) -> tuple[bool, Dict[str, Any]]:
        """
        Ejecuta una orden de trading.
        
        Args:
            action: 'COMPRA' o 'VENTA'
            
        Returns:
            (success, trade_data_or_error)
        """
        try:
            # ==================== VALIDACIÓN: Ganancia Diaria ====================
            daily_target = self.db.get_setting('daily_profit_target', 0)
            if daily_target > 0:
                today_profit = self.mt5_conn.get_today_profit()
                logger.info(f"💵 Profit del día: ${today_profit:.2f} / Objetivo: ${daily_target:.2f}")
                
                if today_profit >= daily_target:
                    logger.info(f"🎯 ¡META DIARIA ALCANZADA! (${today_profit:.2f} >= ${daily_target:.2f})")
                    logger.info("⏸️ Deteniendo trading por hoy...")
                    return False, {'error': f'Meta diaria alcanzada: ${today_profit:.2f}'}

            # Una sola posición abierta por símbolo (evita sobreexposición)
            open_positions = self.mt5_conn.get_positions(self.symbol)
            if open_positions:
                logger.info(
                    f"⏸ [{self.symbol}] Ya hay {len(open_positions)} posición(es) abierta(s). "
                    f"No se abre otra."
                )
                return False, {'error': f'Posición ya abierta en {self.symbol}'}

            # Límite de pérdidas diarias (protección de capital)
            max_daily_loss = float(self.db.get_setting('max_daily_loss', 0) or 0)
            if max_daily_loss > 0:
                today_profit = self.mt5_conn.get_today_profit()
                if today_profit <= -abs(max_daily_loss):
                    logger.warning(
                        f"🛑 Pérdida diaria límite alcanzada: ${today_profit:.2f} "
                        f"(máx -${abs(max_daily_loss):.2f})"
                    )
                    return False, {'error': f'Límite de pérdida diaria: ${today_profit:.2f}'}
            
            # ==================== PARÁMETROS DE TRADING ====================
            # Obtener parámetros de gestión de riesgo desde BD
            risk_percentage = float(self.db.get_setting('risk_percentage', 1.0))
            # Boom/Crash: cola de spike → arriesgar la mitad
            sym_u = self.symbol.upper()
            if 'BOOM' in sym_u or 'CRASH' in sym_u:
                risk_percentage = max(0.25, risk_percentage * 0.5)
                logger.info(f"⚠️ Boom/Crash: riesgo reducido a {risk_percentage}%")
            sl_pips, tp_pips = self.algorithm.get_sl_tp_params(self.symbol)
            
            
            # ==================== MONEY MANAGEMENT: Lotaje Dinámico ====================
            # Calcular lotaje basado en balance, riesgo y distancia SL
            lot_size, warning = self.mt5_conn.calculate_lot_size(
                self.symbol,
                risk_percentage,
                sl_pips
            )
            
            if warning:
                logger.warning(warning)
            
            # Obtener info del símbolo para calcular SL/TP
            symbol_info = self.mt5_conn.get_symbol_info(self.symbol)
            if not symbol_info:
                return False, {'error': 'No se pudo obtener info del símbolo'}
            
            point = symbol_info['point']
            digits = symbol_info.get('digits', 5)

            # Tick fresco: MT5 valida stops vs Bid (BUY) / Ask (SELL), NO vs precio de entrada.
            # Si SL se calcula solo desde Ask en COMPRA, el spread se "come" la distancia → 10016.
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return False, {'error': 'No se pudo obtener tick actual'}

            symbol_info_mt5 = mt5.symbol_info(self.symbol)
            stops_level = int(symbol_info_mt5.trade_stops_level) if symbol_info_mt5 else 0
            spread_points = int(round((tick.ask - tick.bid) / point)) if point else 0
            # Distancia mínima en points: stops_level + spread + margen 30%
            min_stop_points = int(max(stops_level, 1) + spread_points)
            min_stop_points = int(min_stop_points * 1.3)

            if sl_pips < min_stop_points:
                logger.warning(
                    f"   sl_pips ({sl_pips}) < min_stop_points ({min_stop_points}). Ajustando..."
                )
                sl_pips = min_stop_points
            if tp_pips < min_stop_points:
                logger.warning(
                    f"   tp_pips ({tp_pips}) < min_stop_points ({min_stop_points}). Ajustando..."
                )
                tp_pips = max(tp_pips, int(sl_pips * float(self.db.get_setting('risk_reward_ratio', 2.0))))
                tp_pips = max(tp_pips, min_stop_points)

            logger.info(f"   STOPS LEVEL={stops_level} spread_pts={spread_points} min_pts={min_stop_points}")
            logger.info(f"📤 [{self.symbol}] Preparando orden {action}:")
            logger.info(f"   sl_pts={sl_pips} tp_pts={tp_pips} point={point} digits={digits}")
            logger.info(f"   bid={tick.bid} ask={tick.ask}")

            if action == 'COMPRA':
                price = tick.ask
                # SL debe quedar por debajo del Bid al menos stops_level points
                sl_from_entry = price - (sl_pips * point)
                sl_from_bid = tick.bid - (stops_level * point * 1.2) if stops_level else sl_from_entry
                sl = min(sl_from_entry, sl_from_bid)
                tp = price + (tp_pips * point)
                # TP también respeta distancia mínima desde Ask
                if (tp - tick.ask) < (stops_level * point):
                    tp = tick.ask + (min_stop_points * point)
            else:  # VENTA
                price = tick.bid
                sl_from_entry = price + (sl_pips * point)
                sl_from_ask = tick.ask + (stops_level * point * 1.2) if stops_level else sl_from_entry
                sl = max(sl_from_entry, sl_from_ask)
                tp = price - (tp_pips * point)
                if (tick.bid - tp) < (stops_level * point):
                    tp = tick.bid - (min_stop_points * point)

            price = round(price, digits)
            sl = round(sl, digits)
            tp = round(tp, digits)

            # Validación final local (evita 10016 obvio)
            if action == 'COMPRA':
                dist_sl_vs_bid = tick.bid - sl
                if dist_sl_vs_bid < stops_level * point:
                    sl = round(tick.bid - (min_stop_points * point), digits)
                if tp <= price:
                    tp = round(price + (min_stop_points * point), digits)
            else:
                dist_sl_vs_ask = sl - tick.ask
                if dist_sl_vs_ask < stops_level * point:
                    sl = round(tick.ask + (min_stop_points * point), digits)
                if tp >= price:
                    tp = round(price - (min_stop_points * point), digits)

            logger.info(f"   FINAL price={price} SL={sl} TP={tp}")
            logger.info(
                f"   Dist SL vs entry={abs(price - sl):.5f} "
                f"({abs(price - sl) / point:.0f} pts)"
            )

            # Enviar orden
            result = self.mt5_conn.send_order(
                symbol=self.symbol,
                order_type=action,
                volume=lot_size,
                price=price,
                sl=sl,
                tp=tp,
                comment="PyQt Bot"
            )
            
            if result['success']:
                trade_data = {
                    'action': action,
                    'symbol': self.symbol,
                    'ticket': result['ticket'],
                    'volume': result['volume'],
                    'price': result['price'],
                    'sl': sl,
                    'tp': tp,
                    'sl_pips': sl_pips,
                    'tp_pips': tp_pips
                }
                return True, trade_data
            else:
                # GUARDAR ERROR EN BASE DE DATOS
                error_msg = result.get('error', 'Error desconocido')
                logger.error(f"❌ [{self.symbol}] Fallo al enviar orden: {error_msg}")
                
                try:
                    import traceback
                    # Formato detallado del error
                    error_details = f"""
Símbolo: {self.symbol}
Acción: {action}
Precio: {price}
SL: {sl} (calculado: {price - (sl_pips * point) if action == 'COMPRA' else price + (sl_pips * point)})
TP: {tp} (calculado: {price + (tp_pips * point) if action == 'COMPRA' else price - (tp_pips * point)})
Lote: {lot_size}
Dígitos: {digits}
Point: {point}
Error MT5: {error_msg}
"""
                    self.db.log_error(
                        error_type="MT5_ORDER_FAILED",
                        error_message=error_msg,
                        symbol=self.symbol,
                        stack_trace=error_details
                    )
                    logger.info(f"💾 Error guardado en BD")
                except Exception as db_err:
                    logger.error(f"No se pudo guardar error en BD: {db_err}")
                
                return False, result
        
        except Exception as e:
            logger.error(f"❌ Excepción al ejecutar trade: {e}")
            
            # Guardar excepción en BD
            try:
                import traceback
                self.db.log_error(
                    error_type="TRADE_EXCEPTION",
                    error_message=str(e),
                    symbol=self.symbol,
                    stack_trace=traceback.format_exc()
                )
            except:
                pass
            
            return False, {'error': str(e)}
    
    def _save_analysis_to_db(self, result: Dict[str, Any]):
        """Guarda el análisis en la base de datos"""
        if not self.db:
            logger.error(f"❌ [{self.symbol}] Error: Objeto DB no inicializado")
            return

        try:
            # La nueva firma solo necesita symbol y analysis_result completo
            self.db.save_analysis(
                symbol=self.symbol,
                analysis_result=result
            )
            logger.info(f"✅ [{self.symbol}] Análisis guardado en BD")
        except Exception as e:
            logger.error(f"❌ [{self.symbol}] CRÍTICO: Error guardando análisis en BD: {e}")
            traceback.print_exc()

    def _save_trade_to_db(self, trade_data: Dict[str, Any]):
        """Guarda la operación en la base de datos"""
        if not self.db:
            return

        try:
            self.db.add_trade(
                symbol=self.symbol,
                trade_type=trade_data['action'],
                entry_price=trade_data['price'],
                stop_loss=trade_data['sl'],
                take_profit=trade_data['tp'],
                lot_size=trade_data['volume'],
                ticket=trade_data.get('ticket')
            )
            logger.info(f"💾 [{self.symbol}] Trade guardado en BD correctamente")
        except Exception as e:
            logger.error(f"❌ [{self.symbol}] CRÍTICO: Error guardando trade: {e}")
            traceback.print_exc()
    
    def _tick_prediction_while_managing(self):
        """Actualiza predicción/reputación aunque haya posición abierta (modo volátil)."""
        price_data = self.mt5_conn.get_current_price(self.symbol)
        if not price_data:
            return
        price = float(price_data.get("bid") or price_data.get("last") or 0)
        if price <= 0:
            return
        verification = self.algorithm._verify_previous_prediction(self.symbol, price)
        # Si se cerró la pendiente, crear una nueva predicción liviana
        if verification.get("status") in ("ACERTADA", "FALLIDA", "SIN_PREVIA"):
            df = self.algorithm._get_recent_data(self.symbol, n=80)
            if df is not None and not df.empty:
                light = {
                    "paso2": {"tendencia": "NEUTRAL", "confianza": 0},
                    "paso3": {"rsi": 50, "veredicto_matematico": "NEUTRAL"},
                }
                # Reusar último análisis en BD si existe
                last = self.db.get_last_analysis(self.symbol)
                if last and last.get("details"):
                    d = last["details"]
                    light["paso2"] = d.get("paso2", light["paso2"])
                    light["paso3"] = d.get("paso3", light["paso3"])
                pred = self.algorithm._build_technical_prediction(self.symbol, df, light)
                self.algorithm._store_pending_prediction(self.symbol, pred)
                # Snapshot expertos del último panel
                try:
                    from models.expert_reputation import ExpertReputation
                    experts = (light.get("paso3") or {}).get("experts") or {}
                    if experts:
                        ExpertReputation(self.db).snapshot_votes(
                            self.symbol, experts, price
                        )
                except Exception:
                    pass
                result = {
                    "symbol": self.symbol,
                    "prediction_tick_only": True,
                    "final_action": "ESPERAR",
                    "confidence": 0,
                    "reasoning": "Gestionando posición — tick predicción",
                    "prediction": pred,
                    "prediction_verification": verification,
                    "paso2": light.get("paso2", {}),
                    "paso3": light.get("paso3", {}),
                }
                self.analysis_complete.emit(self.symbol, result)
        elif verification.get("status") == "EVALUANDO":
            result = {
                "symbol": self.symbol,
                "prediction_tick_only": True,
                "final_action": "ESPERAR",
                "confidence": 0,
                "reasoning": "Gestionando posición — evaluando predicción",
                "prediction_verification": verification,
                "paso2": {},
                "paso3": {},
            }
            self.analysis_complete.emit(self.symbol, result)

    def stop(self):
        """Detiene el worker"""
        logger.info(f"🛑 Deteniendo worker para {self.symbol}...")
        self._is_running = False
        self.wait(5000)  # Esperar máx 5 segundos
    
    def pause(self):
        """Pausa el worker"""
        logger.info(f"⏸ Pausando worker para {self.symbol}")
        self._is_paused = True
        self.status_update.emit(self.symbol, "Pausado")
    
    def resume(self):
        """Reanuda el worker"""
        logger.info(f"▶️ Reanudando worker para {self.symbol}")
        self._is_paused = False
        self.status_update.emit(self.symbol, "Activo")
    
    def is_running(self) -> bool:
        """Verifica si el worker está corriendo"""
        return self._is_running and self.isRunning()
    
    def is_paused(self) -> bool:
        """Verifica si el worker está pausado"""
        return self._is_paused
