import MetaTrader5 as mt5
import pandas as pd
import logging
import config
from sentiment_analysis import analyze_price_action
from mt5_executor import connect_mt5
from technical_indicators import get_technical_summary
from prediction_models import get_monthly_probability
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SYNTHETIC] - %(message)s')

def get_recent_data(symbol, n=100):
    """
    Obtiene datos recientes para análisis técnico.
    Por defecto: 100 velas de M5 = ~8 horas de datos
    Esto proporciona suficiente contexto para indicadores técnicos confiables
    """
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, n)
    if rates is None: return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def get_history_data(symbol, days=30):
    n = days * 24
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, n)
    if rates is None: return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def run_synthetic_analysis(symbol):
    print("\n" + "="*70)
    print(" INICIO DE ANALISIS ESTRATEGICO V5 (PASO A PASO) ")
    print("="*70)

    if not connect_mt5():
        print("[!] ERROR: No se pudo establecer conexion con MetaTrader 5.")
        return

    # PASO 1: Valor a predecir / Activo
    print(f"\n[PASO 1] ACTIVO BAJO ANALISIS:")
    print(f" -> SIMBOLO: {symbol}")
    print(f" -> MERCADO: Indices Sinteticos (Deriv)")
    print(f" -> HORA LOCAL: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Obtencion de datos
    df_recent = get_recent_data(symbol)
    df_history = get_history_data(symbol)
    
    if df_recent is None or df_history is None:
        print("[!] ERROR: No se pudieron recuperar datos suficientes de MT5.")
        mt5.shutdown()
        return

    # PASO 2: Regresion Lineal (30 dias)
    print(f"\n[PASO 2] ANALISIS DE REGRESION LINEAL (30 DIAS):")
    reg_res = get_monthly_probability(df_history)
    if reg_res:
        print(f" -> Tendencia: {reg_res['tendencia']}")
        print(f" -> Confianza R2: {reg_res['confianza']}%")
        print(f" -> RECOMENDACION REGRESION: {reg_res['recomendacion']}")
    else:
        print(" -> Sin datos suficientes para regresion.")

    # PASO 3: Panel de Expertos Tecnicos (análisis de ~8 horas de datos M5)
    print(f"\n[PASO 3] PANEL DE EXPERTOS TECNICOS (M5 - 100 velas):") 
    tech = get_technical_summary(df_recent)
    if "error" not in tech:
        exp_list = tech['experts']
        print(f" -> [E1] RSI ({tech['rsi']}): {exp_list['RSI']}")
        print(f" -> [E2] Cruce de Medias: {exp_list['EMA_CROSS']}")
        print(f" -> [E3] MACD ({tech['macd']}): {exp_list['MACD']}")
        print(f" -> [E4] Bandas Bollinger: {exp_list['BOLLINGER']}")
        print(f" -> [E5] Heikin Ashi ({tech['heikin_ashi']}): {exp_list['HEIKIN_ASHI']}")
        print(f" -> [E6] Estocástico ({tech['stoch_k']}): {exp_list['STOCHASTIC']}")
        print(f" -> [E7] Micro S/R: {exp_list['MICRO_SR']}")
        print(f" -> [E8] Volatilidad: {exp_list['VOLATILITY']}")
        print(f" -> [E9] Volumen: {exp_list['VOLUME']}")
        print(f" ==> RESULTADO PANEL (Confianza: {tech['confianza_matematica']}%): {tech['verdicto_matematico']}")
    else:
        print(f" -> Error en panel: {tech['error']}")

    # PASO 4: Analisis con IA (Ollama - Trader Senior)
    print(f"\n[PASO 4] ANALISIS DE IA (TRADER SENIOR - {config.OLLAMA_MODEL}):")
    
    # Detección de tipo de símbolo para mostrar al usuario
    symbol_upper = symbol.upper()
    if symbol_upper.startswith('B') or 'BOOM' in symbol_upper:
        tipo_detectado = "BOOM → Solo señales de COMPRA permitidas"
    elif symbol_upper.startswith('C') or 'CRASH' in symbol_upper:
        tipo_detectado = "CRASH → Solo señales de VENTA permitidas"
    elif 'STEP' in symbol_upper and 'RISE' in symbol_upper:
        tipo_detectado = "STEP RISE → Prioridad COMPRA"
    elif 'STEP' in symbol_upper and 'DROP' in symbol_upper:
        tipo_detectado = "STEP DROP → Prioridad VENTA"
    elif symbol_upper.startswith('V') or 'VOLATILITY' in symbol_upper:
        tipo_detectado = "VOLATILITY → Permite COMPRA/VENTA según tendencia"
    elif 'XAU' in symbol_upper or 'GOLD' in symbol_upper:
        tipo_detectado = "XAUUSD → Permite COMPRA/VENTA (requiere alta confirmación)"
    else:
        tipo_detectado = "GENÉRICO → Análisis completo"
    
    print(f" -> TIPO DE ACTIVO DETECTADO: {tipo_detectado}")
    
    # Construcción de contexto técnico integrando confianzas previas
    contexto_ia = f"""
    ESTADO DE CONFIANZA DEL SISTEMA:
    1. Regresion Macro (H1): {reg_res['confianza'] if reg_res else 0}% con direccion {reg_res['tendencia'] if reg_res else 'N/A'}
    2. Panel Tecnico (M5): {tech['confianza_matematica']}% con direccion {tech['verdicto_matematico']}
    
    DETALLES TECNICOS:
    - RSI: {tech['rsi']} (Sobrecompra > 65, Sobreventa < 35)
    - MACD: {tech['macd']}
    - Heikin Ashi: {tech['heikin_ashi']}
    - EMA Strategy (4 EMAs): {tech['experts']['EMA_CROSS']}
    - Estocastico (K5, D4, S2): {tech['stoch_k']} ({tech['experts']['STOCHASTIC']})
    - Micro Soporte/Resistencia: {tech['experts']['MICRO_SR']}
    - Volatilidad: {tech['experts']['VOLATILITY']}
    - Volumen: {tech['experts']['VOLUME']}
    """
    
    ai_res = analyze_price_action(symbol, contexto_ia)
    
    if "error" not in ai_res:
        print(f" -> SEÑAL IA: {ai_res.get('señal')}")
        print(f" -> CONFIANZA IA: {ai_res.get('confianza')}%")
        print(f" -> RAZON: {ai_res.get('razon')}")
    else:
        print(f" -> IA NO DISPONIBLE: {ai_res['error']}")

    # PASO 5: Resultado Final Consolidado (Lógica Flexible + Validación de Tipo de Activo)
    print(f"\n[PASO 5] VERDICTO FINAL CONSOLIDADO:")
    print("="*70)
    
    reg_dir = reg_res['tendencia'] if reg_res else "NEUTRO"
    ai_signal = ai_res.get('señal', 'ESPERAR')
    
    # Extracción segura de confianza (evitar errores si la IA manda texto)
    try:
        conf_raw = str(ai_res.get('confianza', '0'))
        # Extraer solo dígitos de la respuesta
        ai_conf = int(''.join(filter(str.isdigit, conf_raw)))
    except:
        ai_conf = 0
        
    panel_dir = tech.get('veredicto_matematico', 'NEUTRAL')
    
    final_action = "ESPERAR"
    razon_final = "Sin confluencia clara."

    # Regla 1: Oposición Directa (Filtro de Seguridad)
    if (reg_dir == "ALCISTA" and ai_signal == "VENTA") or (reg_dir == "BAJISTA" and ai_signal == "COMPRA"):
        final_action = "ESPERAR"
        razon_final = "BLOQUEO: IA y Regresion en direcciones OPUESTAS."
    
    # Regla 2: Prioridad IA + Regresion (Incluso con Panel Neutral)
    elif ai_conf >= 70 and ((ai_signal == "COMPRA" and reg_dir == "ALCISTA") or (ai_signal == "VENTA" and reg_dir == "BAJISTA")):
        final_action = ai_signal
        razon_final = f"EJECUCION: Alta confianza IA ({ai_conf}%) alineada con Macro."
    
    # Regla 3: Consenso Tradicional (IA + Panel)
    elif ai_signal == "COMPRA" and panel_dir == "ALCISTA":
        final_action = "COMPRA"
        razon_final = "EJECUCION: Consenso IA y Panel Tecnico."
    elif ai_signal == "VENTA" and panel_dir == "BAJISTA":
        final_action = "VENTA"
        razon_final = "EJECUCION: Consenso IA y Panel Tecnico."

    # VALIDACIÓN ADICIONAL: Verificar que la señal sea compatible con el tipo de activo
    symbol_upper = symbol.upper()
    validacion_tipo = True
    
    if final_action == "COMPRA":
        # Bloques de VENTA solamente (CRASH)
        if symbol_upper.startswith('C') or 'CRASH' in symbol_upper:
            final_action = "ESPERAR"
            razon_final = "⚠️ BLOQUEADO: Señal de COMPRA NO permitida en activo CRASH."
            validacion_tipo = False
    elif final_action == "VENTA":
        # Bloques de COMPRA solamente (BOOM)
        if symbol_upper.startswith('B') or 'BOOM' in symbol_upper:
            final_action = "ESPERAR"
            razon_final = "⚠️ BLOQUEADO: Señal de VENTA NO permitida en activo BOOM."
            validacion_tipo = False

    print(f" -> ACCION FINAL: >>> {final_action} <<<")
    print(f" -> MOTIVO: {razon_final}")
    
    # 📊 REGISTRAR ANÁLISIS EN EXCEL
    try:
        from excel_logger import log_analysis
        
        # Obtener precio actual para el registro (mt5 ya está importado globalmente)
        tick = mt5.symbol_info_tick(symbol)
        precio_actual = tick.ask if final_action == "COMPRA" else tick.bid if final_action == "VENTA" else 0
        
        # Calcular SL y TP para el registro
        if 'XAU' in symbol_upper or 'GOLD' in symbol_upper:
            sl_pips_calc = 300
            tp_pips_calc = 600
        else:
            sl_pips_calc = 500
            tp_pips_calc = 1000
        
        # Helper para convertir valores a numéricos de forma segura
        def safe_float(value, decimals=2):
            """Convierte a float y redondea, maneja strings y None"""
            try:
                if value is None or value == '':
                    return 0
                return round(float(value), decimals)
            except (ValueError, TypeError):
                return 0
        
        log_data = {
            'timestamp': datetime.datetime.now(),
            'symbol': symbol,
            'tipo_activo': tipo_detectado if 'tipo_detectado' in locals() else 'N/A',
            
            # Paso 2: Regresión
            'reg_tendencia': reg_res['tendencia'] if reg_res else 'N/A',
            'reg_confianza': safe_float(reg_res['confianza'], 2) if reg_res else 0,
            'reg_recomendacion': reg_res['recomendacion'] if reg_res else 'N/A',
            
            # Paso 3: Expertos
            'rsi_valor': safe_float(tech.get('rsi', 0), 2) if 'error' not in tech else 0,
            'rsi_senal': tech['experts'].get('RSI', 'N/A') if 'error' not in tech else 'N/A',
            'macd_valor': safe_float(tech.get('macd', 0), 4) if 'error' not in tech else 0,
            'macd_senal': tech['experts'].get('MACD', 'N/A') if 'error' not in tech else 'N/A',
            'heikin_ashi': tech.get('heikin_ashi', 'N/A') if 'error' not in tech else 'N/A',
            'ema_cross': tech['experts'].get('EMA_CROSS', 'N/A') if 'error' not in tech else 'N/A',
            'bollinger': tech['experts'].get('BOLLINGER', 'N/A') if 'error' not in tech else 'N/A',
            'panel_veredicto': tech.get('veredicto_matematico', 'N/A') if 'error' not in tech else 'N/A',
            'panel_confianza': safe_float(tech.get('confianza_matematica', 0), 2) if 'error' not in tech else 0,
            
            # Paso 4: IA
            'ia_senal': ai_res.get('señal', 'N/A'),
            'ia_confianza': safe_float(ai_conf, 0),
            'ia_razon': str(ai_res.get('razon', 'N/A'))[:200],  # Limitar a 200 chars
            
            # Paso 5: Veredicto
            'veredicto_final': final_action,
            'razon_final': str(razon_final)[:100],  # Limitar a 100 chars
            'accion_ejecutada': final_action if validacion_tipo else f'BLOQUEADO ({final_action})',
            
            # Datos de trading (si aplica)
            'precio_entrada': safe_float(precio_actual, 2) if final_action in ['COMPRA', 'VENTA'] and validacion_tipo else 0,
            'sl': sl_pips_calc if final_action in ['COMPRA', 'VENTA'] and validacion_tipo else 0,
            'tp': tp_pips_calc if final_action in ['COMPRA', 'VENTA'] and validacion_tipo else 0,
        }
        
        log_analysis(log_data)
    except Exception as e:
        print(f"⚠️ No se pudo registrar en Excel: {str(e)}")
    
    # EJECUCIÓN DIRECTA SOLICITADA (Solo si pasa validación de tipo)
    if final_action in ["COMPRA", "VENTA"] and validacion_tipo:
        print(f"\n[!] INICIANDO EJECUCION REAL EN MT5...")
        from mt5_executor import open_trade
        
        # Obtener el lote mínimo correspondiente al símbolo
        lot_size = config.LOT_SIZES.get(symbol, 0.35)  # Default 0.35 si no está configurado
        
        # Determinar SL y TP según tipo de activo
        if 'XAU' in symbol_upper or 'GOLD' in symbol_upper:
            sl_pips = 300  # Oro requiere menos por su spread
            tp_pips = 600
        else:
            sl_pips = 500  # Sintéticos estándar
            tp_pips = 1000
        
        print(f" -> Símbolo: {symbol}")
        print(f" -> Lote: {lot_size}")
        print(f" -> SL: {sl_pips} pips | TP: {tp_pips} pips")
        
        success = open_trade(final_action, symbol, lot_size=lot_size, sl_pips=sl_pips, tp_pips=tp_pips)
        if success:
            print(f" ✅ SUCCESS: Operacion de {final_action} abierta para {symbol}.")
        else:
            print(f" ❌ ERROR: No se pudo ejecutar la orden en MT5.")

    print("="*70 + "\n")
    return final_action

if __name__ == "__main__":
    symbol_to_test = "Volatility 75 Index"
    run_synthetic_analysis(symbol_to_test)
    mt5.shutdown()
