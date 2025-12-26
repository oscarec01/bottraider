"""
TEST MT5 OPERATIONS - HERRAMIENTA DE DIAGNÓSTICO

Script para diagnosticar problemas de conexión y ejecución de órdenes en MT5.
Permite probar cada componente de forma aislada sin ejecutar el bot completo.
"""

import MetaTrader5 as mt5
import config
import logging
from datetime import datetime

# Configuración de logs detallados
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('mt5_diagnostic.log'),
        logging.StreamHandler()
    ]
)

def print_header(title):
    """Imprime un encabezado visual"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def print_section(title):
    """Imprime una sección"""
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}")

# ==================== TEST 1: CONEXIÓN MT5 ====================

def test_connection():
    """Prueba la conexión a MetaTrader 5"""
    print_header("TEST 1: CONEXIÓN A MT5")
    
    print("\n[1/3] Inicializando MT5...")
    if not mt5.initialize():
        error = mt5.last_error()
        logging.error(f"❌ Initialize() falló. Error: {error}")
        print(f"❌ FALLO: No se pudo inicializar MT5")
        print(f"   Código de error: {error}")
        return False
    
    print("✅ MT5 inicializado correctamente")
    
    print("\n[2/3] Conectando a cuenta...")
    print(f"   Cuenta: {config.MT5_ACCOUNT}")
    print(f"   Servidor: {config.MT5_SERVER}")
    
    authorized = mt5.login(
        config.MT5_ACCOUNT,
        password=config.MT5_PASSWORD,
        server=config.MT5_SERVER
    )
    
    if not authorized:
        error = mt5.last_error()
        logging.error(f"❌ Login falló. Error: {error}")
        print(f"❌ FALLO: No se pudo conectar")
        print(f"   Código de error: {error}")
        return False
    
    print("✅ Conectado exitosamente")
    
    print("\n[3/3] Información de la cuenta:")
    account_info = mt5.account_info()
    if account_info:
        print(f"   Nombre: {account_info.name}")
        print(f"   Servidor: {account_info.server}")
        print(f"   Balance: ${account_info.balance:.2f}")
        print(f"   Equity: ${account_info.equity:.2f}")
        print(f"   Margen libre: ${account_info.margin_free:.2f}")
        print(f"   Apalancamiento: 1:{account_info.leverage}")
    else:
        print("⚠️ No se pudo obtener información de cuenta")
    
    print("\n✅ TEST 1 COMPLETADO: Conexión exitosa")
    return True

# ==================== TEST 2: INFORMACIÓN DE SÍMBOLO ====================

def test_symbol_info(symbol):
    """Muestra información detallada de un símbolo"""
    print_header(f"TEST 2: INFORMACIÓN DEL SÍMBOLO '{symbol}'")
    
    print("\n[1/4] Verificando disponibilidad del símbolo...")
    symbol_info = mt5.symbol_info(symbol)
    
    if symbol_info is None:
        print(f"❌ FALLO: Símbolo '{symbol}' no encontrado")
        logging.error(f"Símbolo {symbol} no existe en MT5")
        return False
    
    print(f"✅ Símbolo encontrado: {symbol_info.name}")
    
    print("\n[2/4] Verificando visibilidad...")
    if not symbol_info.visible:
        print("⚠️ Símbolo NO visible en Market Watch")
        print("   Intentando agregar al Market Watch...")
        if mt5.symbol_select(symbol, True):
            print("✅ Símbolo agregado correctamente")
            # Actualizar info
            symbol_info = mt5.symbol_info(symbol)
        else:
            print("❌ FALLO: No se pudo agregar al Market Watch")
            return False
    else:
        print("✅ Símbolo visible en Market Watch")
    
    print("\n[3/4] Propiedades del símbolo:")
    print(f"   Descripción: {symbol_info.description}")
    print(f"   Tipo: {symbol_info.path}")
    print(f"   Dígitos: {symbol_info.digits}")
    print(f"   Point (tamaño): {symbol_info.point}")
    print(f"   Tick size: {symbol_info.trade_tick_size}")
    print(f"   Tick value: {symbol_info.trade_tick_value}")
    
    print(f"\n   📊 INFORMACIÓN CRÍTICA DE TRADING:")
    print(f"   ├─ Stops Level: {symbol_info.trade_stops_level} puntos")
    print(f"   ├─ Freeze Level: {symbol_info.trade_freeze_level} puntos")
    print(f"   ├─ Spread actual: {symbol_info.spread} puntos")
    print(f"   ├─ Volumen mínimo: {symbol_info.volume_min}")
    print(f"   ├─ Volumen máximo: {symbol_info.volume_max}")
    print(f"   └─ Step de volumen: {symbol_info.volume_step}")
    
    # Filling modes
    print(f"\n   🔧 MODOS DE EJECUCIÓN SOPORTADOS:")
    filling_mode = symbol_info.filling_mode
    
    # Flags para cada modo (bitmask)
    fok_supported = filling_mode & 1  # SYMBOL_FILLING_FOK
    ioc_supported = filling_mode & 2  # SYMBOL_FILLING_IOC
    return_supported = filling_mode & 4  # SYMBOL_FILLING_RETURN
    
    print(f"   ├─ FOK (Fill or Kill): {'✅ Soportado' if fok_supported else '❌ No soportado'}")
    print(f"   ├─ IOC (Immediate or Cancel): {'✅ Soportado' if ioc_supported else '❌ No soportado'}")
    print(f"   └─ RETURN (Market execution): {'✅ Soportado' if return_supported else '❌ No soportado'}")
    
    print("\n[4/4] Precio actual:")
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"   Bid: {tick.bid}")
        print(f"   Ask: {tick.ask}")
        print(f"   Spread: {tick.ask - tick.bid:.5f}")
        print(f"   Última actualización: {datetime.fromtimestamp(tick.time)}")
    else:
        print("⚠️ No se pudo obtener tick actual")
    
    print("\n✅ TEST 2 COMPLETADO")
    return symbol_info

# ==================== TEST 3: VALIDACIÓN DE STOPS ====================

def test_stops_validation(symbol, sl_pips, tp_pips):
    """Valida si los stops son válidos para un símbolo"""
    print_header(f"TEST 3: VALIDACIÓN DE STOPS ({symbol})")
    
    print(f"\n   Stops solicitados: SL={sl_pips} pips | TP={tp_pips} pips")
    
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print("❌ FALLO: No se pudo obtener información del símbolo")
        return False
    
    point = symbol_info.point
    stops_level = symbol_info.trade_stops_level
    
    print(f"\n[1/3] Información para cálculo:")
    print(f"   Point size: {point}")
    print(f"   Stops level mínimo: {stops_level} puntos")
    print(f"   Stops level en pips: {stops_level / 10} pips")
    
    # Obtener precio actual
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print("❌ FALLO: No se pudo obtener precio actual")
        return False
    
    price_buy = tick.ask
    price_sell = tick.bid
    
    print(f"\n[2/3] Precios actuales:")
    print(f"   Ask (para BUY): {price_buy}")
    print(f"   Bid (para SELL): {price_sell}")
    
    # Cálculo para COMPRA
    print(f"\n[3/3] Validación de cálculos:")
    print("\n   📈 OPERACIÓN DE COMPRA (BUY):")
    sl_buy = price_buy - sl_pips * 10 * point
    tp_buy = price_buy + tp_pips * 10 * point
    
    print(f"   ├─ Precio entrada: {price_buy}")
    print(f"   ├─ SL calculado: {sl_buy} (distancia: {abs(price_buy - sl_buy):.5f})")
    print(f"   └─ TP calculado: {tp_buy} (distancia: {abs(tp_buy - price_buy):.5f})")
    
    # Validación
    sl_distance_points = abs(price_buy - sl_buy) / point
    tp_distance_points = abs(tp_buy - price_buy) / point
    
    print(f"\n   🔍 Validación de distancias (en puntos):")
    print(f"   ├─ SL distancia: {sl_distance_points:.0f} puntos", end="")
    if sl_distance_points >= stops_level:
        print(" ✅ Válido")
    else:
        print(f" ❌ Inválido (mínimo: {stops_level})")
    
    print(f"   └─ TP distancia: {tp_distance_points:.0f} puntos", end="")
    if tp_distance_points >= stops_level:
        print(" ✅ Válido")
    else:
        print(f" ❌ Inválido (mínimo: {stops_level})")
    
    # Cálculo para VENTA
    print("\n   📉 OPERACIÓN DE VENTA (SELL):")
    sl_sell = price_sell + sl_pips * 10 * point
    tp_sell = price_sell - tp_pips * 10 * point
    
    print(f"   ├─ Precio entrada: {price_sell}")
    print(f"   ├─ SL calculado: {sl_sell} (distancia: {abs(sl_sell - price_sell):.5f})")
    print(f"   └─ TP calculado: {tp_sell} (distancia: {abs(price_sell - tp_sell):.5f})")
    
    all_valid = (sl_distance_points >= stops_level and tp_distance_points >= stops_level)
    
    if all_valid:
        print("\n✅ TEST 3 COMPLETADO: Todos los stops son válidos")
    else:
        print("\n⚠️ TEST 3 COMPLETADO: Algunos stops son INVÁLIDOS")
        print(f"   Recomendación: Usar SL >= {stops_level/10:.0f} pips y TP >= {stops_level/10:.0f} pips")
    
    return all_valid

# ==================== TEST 4: DRY-RUN DE ORDEN ====================

def test_order_dryrun(symbol, action_type="BUY", lot_size=0.35, sl_pips=500, tp_pips=1000):
    """Simula la creación de una orden sin enviarla"""
    print_header(f"TEST 4: DRY-RUN DE ORDEN ({action_type})")
    
    print(f"\n   Parámetros:")
    print(f"   ├─ Símbolo: {symbol}")
    print(f"   ├─ Tipo: {action_type}")
    print(f"   ├─ Lote: {lot_size}")
    print(f"   ├─ SL: {sl_pips} pips")
    print(f"   └─ TP: {tp_pips} pips")
    
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print("❌ FALLO: Símbolo no encontrado")
        return None
    
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print("❌ FALLO: No se pudo obtener precio")
        return None
    
    point = symbol_info.point
    price = tick.ask if action_type == 'BUY' else tick.bid
    
    # Cálculo de SL y TP
    if action_type == 'BUY':
        sl = price - sl_pips * 10 * point
        tp = price + tp_pips * 10 * point
        order_type = mt5.ORDER_TYPE_BUY
    else:
        sl = price + sl_pips * 10 * point
        tp = price - tp_pips * 10 * point
        order_type = mt5.ORDER_TYPE_SELL
    
    # Determinar filling mode (con fallback)
    filling_mode_value = symbol_info.filling_mode
    ioc_supported = filling_mode_value & 2
    fok_supported = filling_mode_value & 1
    return_supported = filling_mode_value & 4
    
    if ioc_supported:
        type_filling = mt5.ORDER_FILLING_IOC
        filling_name = "IOC"
    elif fok_supported:
        type_filling = mt5.ORDER_FILLING_FOK
        filling_name = "FOK"
    elif return_supported:
        type_filling = mt5.ORDER_FILLING_RETURN
        filling_name = "RETURN"
    else:
        print("❌ FALLO: No hay filling mode compatible")
        return None
    
    # Crear request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": 123456,
        "comment": "Bot Trader Test",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": type_filling,
    }
    
    print(f"\n   📋 REQUEST GENERADO:")
    print(f"   ├─ action: TRADE_ACTION_DEAL")
    print(f"   ├─ symbol: {request['symbol']}")
    print(f"   ├─ volume: {request['volume']}")
    print(f"   ├─ type: {'ORDER_TYPE_BUY' if action_type == 'BUY' else 'ORDER_TYPE_SELL'}")
    print(f"   ├─ price: {request['price']}")
    print(f"   ├─ sl: {request['sl']}")
    print(f"   ├─ tp: {request['tp']}")
    print(f"   ├─ magic: {request['magic']}")
    print(f"   ├─ comment: {request['comment']}")
    print(f"   ├─ type_time: ORDER_TIME_GTC")
    print(f"   └─ type_filling: ORDER_FILLING_{filling_name}")
    
    # Validaciones finales
    print(f"\n   ✅ Validaciones:")
    print(f"   ├─ Símbolo visible: {'Sí' if symbol_info.visible else 'No'}")
    print(f"   ├─ Lote válido: {symbol_info.volume_min} <= {lot_size} <= {symbol_info.volume_max}")
    
    sl_dist = abs(price - sl) / point
    tp_dist = abs(tp - price) / point
    print(f"   ├─ SL distance: {sl_dist:.0f} puntos (mín: {symbol_info.trade_stops_level})")
    print(f"   └─ TP distance: {tp_dist:.0f} puntos (mín: {symbol_info.trade_stops_level})")
    
    print("\n✅ TEST 4 COMPLETADO: Request generado correctamente")
    print("   ⚠️ NOTA: La orden NO fue enviada (dry-run)")
    
    return request

# ==================== TEST 5: ORDEN REAL (OPCIONAL) ====================

def test_real_order(symbol, action_type="BUY", lot_size=0.35, sl_pips=500, tp_pips=1000):
    """EJECUTA una orden real en MT5 - ¡USAR CON PRECAUCIÓN!"""
    print_header(f"TEST 5: ORDEN REAL ({action_type})")
    
    print("\n⚠️  ADVERTENCIA: Este test ejecutará una ORDEN REAL en MT5")
    confirm = input("   ¿Desea continuar? (escriba 'SI' para confirmar): ")
    
    if confirm != "SI":
        print("❌ Test cancelado por el usuario")
        return False
    
    # Obtener información del símbolo
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print(f"❌ FALLO: Símbolo '{symbol}' no encontrado")
        return False
    
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            print("❌ FALLO: No se pudo agregar símbolo al Market Watch")
            return False
    
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print("❌ FALLO: No se pudo obtener precio actual")
        return False
    
    point = symbol_info.point
    price = tick.ask if action_type == 'BUY' else tick.bid
    
    # Cálculo de SL y TP
    if action_type == 'BUY':
        sl = price - sl_pips * 10 * point
        tp = price + tp_pips * 10 * point
        order_type = mt5.ORDER_TYPE_BUY
    else:
        sl = price + sl_pips * 10 * point
        tp = price - tp_pips * 10 * point
        order_type = mt5.ORDER_TYPE_SELL
    
    # Determinar filling mode
    filling_mode_value = symbol_info.filling_mode
    if filling_mode_value & 2:
        type_filling = mt5.ORDER_FILLING_IOC
    elif filling_mode_value & 1:
        type_filling = mt5.ORDER_FILLING_FOK
    elif filling_mode_value & 4:
        type_filling = mt5.ORDER_FILLING_RETURN
    else:
        print("❌ FALLO: No hay filling mode compatible")
        return False
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": 123456,
        "comment": "Bot Trader Test REAL",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": type_filling,
    }
    
    print("\n   📤 Enviando orden a MT5...")
    logging.info(f"Enviando orden: {request}")
    
    result = mt5.order_send(request)
    
    print(f"\n   📨 Resultado de la orden:")
    print(f"   ├─ Retcode: {result.retcode}")
    print(f"   ├─ Descripción: {result.comment}")
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"   ├─ Orden: {result.order}")
        print(f"   ├─ Volumen: {result.volume}")
        print(f"   ├─ Precio: {result.price}")
        print(f"   └─ Ticket: {result.deal}")
        print("\n✅ ORDEN EJECUTADA EXITOSAMENTE")
        logging.info(f"Orden ejecutada: Ticket={result.deal}")
        return True
    else:
        print(f"   └─ Error: {result.comment}")
        print(f"\n❌ FALLO AL EJECUTAR ORDEN")
        logging.error(f"Error al ejecutar orden: Retcode={result.retcode}, Comment={result.comment}")
        
        # Códigos de error comunes
        error_codes = {
            10004: "Requote - precio cambió",
            10006: "Request rejected - solicitud rechazada",
            10013: "Invalid request - solicitud inválida",
            10014: "Invalid volume",
            10015: "Invalid price",
            10016: "Invalid stops - SL/TP inválidos",
            10018: "Market closed",
            10019: "Not enough money",
            10030: "Invalid request - parámetros inválidos",
            10031: "Order state error"
        }
        
        if result.retcode in error_codes:
            print(f"   💡 Significado: {error_codes[result.retcode]}")
        
        return False

# ==================== TEST 6: OBTENCIÓN DE DATOS ====================

def test_data_retrieval(symbol, timeframe=mt5.TIMEFRAME_M5, count=100):
    """Prueba la obtención de datos históricos"""
    print_header(f"TEST 6: OBTENCIÓN DE DATOS HISTÓRICOS")
    
    print(f"\n   Parámetros:")
    print(f"   ├─ Símbolo: {symbol}")
    print(f"   ├─ Timeframe: M5")
    print(f"   └─ Velas: {count}")
    
    print("\n   Obteniendo datos...")
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    
    if rates is None or len(rates) == 0:
        error = mt5.last_error()
        print(f"❌ FALLO: No se pudieron obtener datos")
        print(f"   Error: {error}")
        logging.error(f"Error obteniendo datos de {symbol}: {error}")
        return False
    
    print(f"\n   ✅ Datos obtenidos: {len(rates)} velas")
    print(f"\n   📊 Muestra de datos (últimas 3 velas):")
    
    for i in range(min(3, len(rates))):
        idx = len(rates) - 3 + i
        rate = rates[idx]
        time_str = datetime.fromtimestamp(rate['time']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"   [{i+1}] {time_str} | O:{rate['open']:.5f} H:{rate['high']:.5f} L:{rate['low']:.5f} C:{rate['close']:.5f} | Vol:{rate['tick_volume']}")
    
    print("\n✅ TEST 6 COMPLETADO: Datos históricos obtenidos correctamente")
    return True

# ==================== MENÚ PRINCIPAL ====================

def main():
    """Menú interactivo principal"""
    print_header("🔧 HERRAMIENTA DE DIAGNÓSTICO MT5")
    print("\nEsta herramienta te ayudará a identificar problemas con MT5")
    print("y validar que las órdenes se configuren correctamente.\n")
    
    while True:
        print("\n" + "─"*70)
        print("MENÚ DE TESTS:")
        print("─"*70)
        print("  1. Test de Conexión MT5")
        print("  2. Test de Información de Símbolo")
        print("  3. Test de Validación de Stops")
        print("  4. Test Dry-Run de Orden (simulado)")
        print("  5. Test de Obtención de Datos")
        print("  6. Test de Orden REAL ⚠️  (ejecuta orden real)")
        print("  7. Ejecutar TODOS los tests (excepto orden real)")
        print("  0. Salir")
        print("─"*70)
        
        choice = input("\nSeleccione una opción: ")
        
        if choice == "0":
            print("\n👋 Cerrando herramienta...")
            mt5.shutdown()
            break
        
        elif choice == "1":
            test_connection()
        
        elif choice == "2":
            symbol = input("\nIngrese símbolo (ej: Volatility 75 Index): ")
            if not symbol:
                symbol = "Volatility 75 Index"
            test_symbol_info(symbol)
        
        elif choice == "3":
            symbol = input("\nIngrese símbolo (ej: Volatility 75 Index): ")
            if not symbol:
                symbol = "Volatility 75 Index"
            
            try:
                sl = int(input("Ingrese SL en pips (ej: 500): ") or "500")
                tp = int(input("Ingrese TP en pips (ej: 1000): ") or "1000")
            except:
                print("⚠️ Valores inválidos, usando defaults: SL=500, TP=1000")
                sl, tp = 500, 1000
            
            test_stops_validation(symbol, sl, tp)
        
        elif choice == "4":
            symbol = input("\nIngrese símbolo (ej: Volatility 75 Index): ")
            if not symbol:
                symbol = "Volatility 75 Index"
            
            action = input("Tipo de orden (BUY/SELL): ").upper()
            if action not in ['BUY', 'SELL']:
                action = 'BUY'
            
            try:
                lot = float(input(f"Lote (ej: {config.LOT_SIZES.get(symbol, 0.35)}): ") or config.LOT_SIZES.get(symbol, 0.35))
                sl = int(input("SL en pips (ej: 500): ") or "500")
                tp = int(input("TP en pips (ej: 1000): ") or "1000")
            except:
                print("⚠️ Usando valores por defecto")
                lot = config.LOT_SIZES.get(symbol, 0.35)
                sl, tp = 500, 1000
            
            test_order_dryrun(symbol, action, lot, sl, tp)
        
        elif choice == "5":
            symbol = input("\nIngrese símbolo (ej: Volatility 75 Index): ")
            if not symbol:
                symbol = "Volatility 75 Index"
            
            test_data_retrieval(symbol)
        
        elif choice == "6":
            print("\n⚠️  ADVERTENCIA: Esta opción ejecuta una orden REAL")
            print("   Solo usar en cuenta DEMO o con extrema precaución")
            
            symbol = input("\nIngrese símbolo: ")
            if not symbol:
                print("❌ Debe ingresar un símbolo")
                continue
            
            action = input("Tipo (BUY/SELL): ").upper()
            if action not in ['BUY', 'SELL']:
                print("❌ Tipo inválido")
                continue
            
            try:
                lot = float(input("Lote: ") or "0.35")
                sl = int(input("SL pips: ") or "500")
                tp = int(input("TP pips: ") or "1000")
            except:
                print("❌ Valores inválidos")
                continue
            
            test_real_order(symbol, action, lot, sl, tp)
        
        elif choice == "7":
            print("\n🚀 Ejecutando suite completa de tests...")
            
            # Test 1
            if not test_connection():
                print("\n❌ Test de conexión falló. No se pueden ejecutar más tests.")
                continue
            
            # Test 2
            symbol = "Volatility 75 Index"
            info = test_symbol_info(symbol)
            
            if info:
                # Test 3
                test_stops_validation(symbol, 500, 1000)
                
                # Test 4
                test_order_dryrun(symbol, "BUY", config.LOT_SIZES.get(symbol, 0.35), 500, 1000)
                
                # Test 5
                test_data_retrieval(symbol)
            
            print_header("✅ SUITE DE TESTS COMPLETADA")
        
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupción del usuario (Ctrl+C)")
        mt5.shutdown()
    except Exception as e:
        logging.error(f"Error crítico: {str(e)}", exc_info=True)
        mt5.shutdown()
        raise
