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
                
                # Verificar conexión MT5
                if not self.mt5_conn.is_connected():
                    self.error_occurred.emit(
                        self.symbol,
                        "No conectado a MT5. Worker en espera..."
                    )
                    time.sleep(10)
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
                # Dormir en intervalos pequeños para poder detenerse rápido
                for _ in range(self.interval):
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
            
            # ==================== PARÁMETROS DE TRADING ====================
            # Obtener parámetros de gestión de riesgo desde BD
            risk_percentage = self.db.get_setting('risk_percentage', 1.0)
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
            
            # Obtener precio actual
            price_data = self.mt5_conn.get_current_price(self.symbol)
            if not price_data:
                return False, {'error': 'No se pudo obtener precio actual'}
            
            price = price_data['ask'] if action == 'COMPRA' else price_data['bid']
            
            # Obtener info del símbolo para calcular SL/TP
            symbol_info = self.mt5_conn.get_symbol_info(self.symbol)
            if not symbol_info:
                return False, {'error': 'No se pudo obtener info del símbolo'}
            
            point = symbol_info['point']
            digits = symbol_info.get('digits', 5)  # Por defecto 5 decimales
            
            # Verificar stops level del broker
            symbol_info_mt5 = mt5.symbol_info(self.symbol)
            if symbol_info_mt5:
                stops_level = symbol_info_mt5.trade_stops_level
                logger.info(f"   ⚠️ STOPS LEVEL del broker: {stops_level} puntos")
                
                # Ajustar pips con margen de seguridad generoso (20-30% sobre el mínimo)
                # Esto evita errores por variaciones de precio entre fetch y ejecución
                if sl_pips < stops_level:
                    logger.warning(f"   ⚠️ sl_pips ({sl_pips}) < stops_level ({stops_level}). Ajustando...")
                    sl_pips = int(stops_level * 1.2)  # 20% de margen de seguridad
                
                if tp_pips < stops_level:
                    logger.warning(f"   ⚠️ tp_pips ({tp_pips}) < stops_level ({stops_level}). Ajustando...")
                    tp_pips = int(stops_level * 1.3)  # 30% de margen (TP más lejos que SL)
            
            logger.info(f"📤 [{self.symbol}] Preparando orden {action}:")
            logger.info(f"   ⚙️ PARÁMETROS FINALES:")
            logger.info(f"   - sl_pips: {sl_pips}")
            logger.info(f"   - tp_pips: {tp_pips}")
            logger.info(f"   - point: {point}")
            logger.info(f"   - digits: {digits}")
            logger.info(f"   - precio: {price}")
            
            # Calcular SL y TP
            if action == 'COMPRA':
                sl = price - (sl_pips * point)
                tp = price + (tp_pips * point)
            else:  # VENTA
                sl = price + (sl_pips * point)
                tp = price - (tp_pips * point)
            
            logger.info(f"   🧮 CÁLCULO:")
            if action == 'COMPRA':
                logger.info(f"   - SL = {price} - ({sl_pips} * {point}) = {price} - {sl_pips * point} = {sl}")
                logger.info(f"   - TP = {price} + ({tp_pips} * {point}) = {price} + {tp_pips * point} = {tp}")
            else:  # VENTA
                logger.info(f"   - SL = {price} + ({sl_pips} * {point}) = {price} + {sl_pips * point} = {sl}")
                logger.info(f"   - TP = {price} - ({tp_pips} * {point}) = {price} - {tp_pips * point} = {tp}")
            
            logger.info(f"   [PASO 1] Valores calculados:")
            logger.info(f"   - Precio: {price}")
            logger.info(f"   - SL inicial: {sl}")
            logger.info(f"   - TP inicial: {tp}")
            logger.info(f"   - Parámetros: SL_pips={sl_pips}, TP_pips={tp_pips}, Point={point}, Dígitos={digits}")
            
            # NORMALIZACIÓN SIMPLE - Exactamente como en el script de diagnóstico que FUNCIONÓ
            price = round(price, digits)
            sl = round(sl, digits)
            tp = round(tp, digits)
            
            logger.info(f"   [PASO FINAL] Valores normalizados con round():")
            logger.info(f"   - Precio: {price}")
            logger.info(f"   - SL: {sl}")
            logger.info(f"   - TP: {tp}")
            logger.info(f"   - Distancia SL: {abs(price - sl):.3f} ({abs(price - sl) / point:.0f} puntos)")
            logger.info(f"   - Distancia TP: {abs(tp - price):.3f} ({abs(tp - price) / point:.0f} puntos)")

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
