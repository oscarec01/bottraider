"""
AUTO TRADER 10 MINUTOS - DERIV SYNTHETIC INDICES BOT

Sistema de trading automatizado con validación inteligente de señales.
- Ejecuta análisis completo cada 2 minutos
- Duración: 10 minutos
- Si hay órdenes abiertas al finalizar, espera hasta que se cierren
"""

import time
import datetime
import logging
import MetaTrader5 as mt5
import config
from mt5_executor import connect_mt5
from synthetic_trader import run_synthetic_analysis

# ==================== CONFIGURACIÓN ====================
DURATION_MINUTES = 10       # Duración total de la sesión
INTERVAL_SECONDS = 120      # Análisis cada 2 minutos
CHECK_ORDERS_INTERVAL = 10  # Revisar órdenes cada 10 segundos

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [AUTO-TRADER] - %(message)s',
    handlers=[
        logging.FileHandler('auto_trader_log.txt'),
        logging.StreamHandler()
    ]
)

# ==================== FUNCIONES AUXILIARES ====================

def get_open_positions():
    """Obtiene todas las posiciones abiertas de la cuenta"""
    positions = mt5.positions_get()
    if positions is None:
        return []
    return list(positions)

def display_open_positions(positions):
    """Muestra información de las posiciones abiertas"""
    if not positions:
        print("\n  No hay posiciones abiertas.")
        return
    
    print(f"\n  {'='*60}")
    print(f"  POSICIONES ABIERTAS: {len(positions)}")
    print(f"  {'='*60}")
    
    for i, pos in enumerate(positions, 1):
        position_type = "COMPRA" if pos.type == mt5.POSITION_TYPE_BUY else "VENTA"
        profit_emoji = "🟢" if pos.profit >= 0 else "🔴"
        
        print(f"  [{i}] {pos.symbol}")
        print(f"      Tipo: {position_type} | Lote: {pos.volume}")
        print(f"      Precio: {pos.price_open} -> {pos.price_current}")
        print(f"      Ganancia: {profit_emoji} ${pos.profit:.2f}")
        print(f"      Ticket: {pos.ticket}")
        print(f"  {'-'*60}")

def wait_for_positions_to_close(max_wait_minutes=30):
    """
    Espera hasta que todas las posiciones se cierren.
    Retorna True si todas se cerraron, False si se excedió el tiempo.
    """
    start_wait = datetime.datetime.now()
    max_wait_time = datetime.timedelta(minutes=max_wait_minutes)
    
    print("\n" + "⏳"*35)
    print(" ESPERANDO CIERRE DE POSICIONES ABIERTAS ")
    print("⏳"*35)
    
    while True:
        positions = get_open_positions()
        elapsed = datetime.datetime.now() - start_wait
        
        if not positions:
            print("\n✅ Todas las posiciones han sido cerradas.")
            return True
        
        if elapsed > max_wait_time:
            print(f"\n⚠️ Tiempo máximo de espera ({max_wait_minutes} min) alcanzado.")
            print(f"   Quedan {len(positions)} posiciones abiertas.")
            return False
        
        # Mostrar estado cada 10 segundos
        remaining = max_wait_time - elapsed
        print(f"\r⏳ Esperando... {len(positions)} posición(es) abierta(s) | "
              f"Tiempo restante: {int(remaining.total_seconds()/60)} min", end="")
        
        time.sleep(CHECK_ORDERS_INTERVAL)

def display_session_header(cycle, current_time, remaining_minutes):
    """Muestra el encabezado de cada ciclo"""
    print("\n" + "!"*70)
    print(f"!!! CICLO {cycle} | HORA: {current_time} | RESTANTE: {remaining_minutes:.1f} min !!!")
    print("!"*70)

def display_symbol_header(symbol):
    """Muestra el encabezado para cada símbolo"""
    print(f"\n{'>'*70}")
    print(f">>> ESCANEANDO: {symbol}")
    print(f"{'>'*70}")

# ==================== FUNCIÓN PRINCIPAL ====================

def start_auto_trading():
    """
    Ejecuta el sistema de trading automático por 10 minutos.
    Analiza múltiples activos cada 2 minutos.
    Si hay posiciones abiertas al final, espera hasta que se cierren.
    """
    print("\n" + "="*70)
    print(" 🚀 INICIANDO AUTO TRADER - DERIV SYNTHETIC INDICES BOT 🚀 ")
    print("="*70)
    print(f" Duración: {DURATION_MINUTES} minutos")
    print(f" Intervalo de análisis: {INTERVAL_SECONDS} segundos")
    print(f" Activos a analizar: {len(config.ACTIVOS_PERMITIDOS)}")
    print("="*70)
    
    # Conectar a MT5
    if not connect_mt5():
        print("❌ ERROR: No se pudo establecer conexión con MetaTrader 5.")
        return
    
    print("✅ Conectado a MetaTrader 5")
    
    # Mostrar activos configurados
    print(f"\n📋 ACTIVOS CONFIGURADOS:")
    for i, symbol in enumerate(config.ACTIVOS_PERMITIDOS, 1):
        lot = config.LOT_SIZES.get(symbol, 'N/A')
        print(f"   {i}. {symbol:30} (Lote: {lot})")
    
    # Configurar tiempo de sesión
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(minutes=DURATION_MINUTES)
    
    print(f"\n⏰ INICIO: {start_time.strftime('%H:%M:%S')}")
    print(f"⏰ FIN PROGRAMADO: {end_time.strftime('%H:%M:%S')}")
    
    cycle = 1
    
    # ==================== BUCLE PRINCIPAL ====================
    while datetime.datetime.now() < end_time:
        current_time = datetime.datetime.now().strftime('%H:%M:%S')
        remaining = (end_time - datetime.datetime.now()).total_seconds() / 60
        
        display_session_header(cycle, current_time, remaining)
        
        # Iterar sobre la lista de activos permitidos
        for symbol in config.ACTIVOS_PERMITIDOS:
            display_symbol_header(symbol)
            
            try:
                # Ejecutar análisis estratégico completo (Pasos 1-5)
                result = run_synthetic_analysis(symbol)
                
                if result in ["COMPRA", "VENTA"]:
                    logging.info(f"✅ Señal ejecutada para {symbol}: {result}")
                else:
                    logging.info(f"⏸️ Sin señal para {symbol}: {result}")
                    
            except Exception as e:
                logging.error(f"❌ Error analizando {symbol}: {str(e)}")
            
            # Pequeña pausa entre activos
            time.sleep(1)
        
        # Mostrar posiciones abiertas después de cada ciclo
        positions = get_open_positions()
        display_open_positions(positions)
        
        # Determinar si hay tiempo para otro ciclo
        if datetime.datetime.now() + datetime.timedelta(seconds=INTERVAL_SECONDS) < end_time:
            print(f"\n💤 Durmiendo {INTERVAL_SECONDS} segundos hasta el próximo ciclo...")
            time.sleep(INTERVAL_SECONDS)
        else:
            print("\n⏰ No hay tiempo suficiente para otro ciclo completo.")
            break
        
        cycle += 1
    
    # ==================== FINALIZACIÓN ====================
    print("\n" + "="*70)
    print(" ⏰ TIEMPO DE SESIÓN COMPLETADO ")
    print("="*70)
    
    # Verificar si hay posiciones abiertas
    final_positions = get_open_positions()
    
    if final_positions:
        print(f"\n⚠️ Hay {len(final_positions)} posición(es) abierta(s).")
        display_open_positions(final_positions)
        
        # Esperar hasta que se cierren (máximo 30 minutos adicionales)
        all_closed = wait_for_positions_to_close(max_wait_minutes=30)
        
        if not all_closed:
            print("\n⚠️ ADVERTENCIA: Algunas posiciones siguen abiertas.")
            print("   Se recomienda cerrarlas manualmente o esperar más tiempo.")
            final_positions = get_open_positions()
            display_open_positions(final_positions)
    else:
        print("\n✅ No hay posiciones abiertas. Sesión finalizada limpiamente.")
    
    # Cerrar conexión MT5
    mt5.shutdown()
    print("\n" + "="*70)
    print(" 🏁 BOT FINALIZADO - MT5 DESCONECTADO 🏁 ")
    print("="*70)

# ==================== PUNTO DE ENTRADA ====================

if __name__ == "__main__":
    try:
        start_auto_trading()
    except KeyboardInterrupt:
        print("\n\n⚠️ INTERRUPCIÓN DEL USUARIO (Ctrl+C)")
        print("Cerrando conexión MT5...")
        mt5.shutdown()
        print("✅ Sesión terminada por el usuario.")
    except Exception as e:
        logging.error(f"❌ ERROR CRÍTICO: {str(e)}")
        mt5.shutdown()
        raise
