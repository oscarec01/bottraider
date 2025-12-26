"""
AUTO TRADER QUICK TEST - 10 MINUTOS

Versión optimizada para pruebas rápidas:
- Duración: 10 minutos
- Análisis cada 30 segundos
- Solo un símbolo: Volatility 10 Index
"""

import time
import datetime
import logging
import MetaTrader5 as mt5
import config
from mt5_executor import connect_mt5
from synthetic_trader import run_synthetic_analysis

# ==================== CONFIGURACIÓN ====================
SYMBOL = "Volatility 10 Index"  # Símbolo más volátil para pruebas
DURATION_MINUTES = 10            # Duración total de la sesión
INTERVAL_SECONDS = 30            # Análisis cada 30 segundos
CHECK_ORDERS_INTERVAL = 5        # Revisar órdenes cada 5 segundos

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [QUICK-TEST] - %(message)s',
    handlers=[
        logging.FileHandler('quick_test_log.txt'),
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
        print("\n  ℹ️  No hay posiciones abiertas.")
        return
    
    print(f"\n  {'─'*60}")
    print(f"  📊 POSICIONES ABIERTAS: {len(positions)}")
    print(f"  {'─'*60}")
    
    for i, pos in enumerate(positions, 1):
        position_type = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
        profit_emoji = "🟢" if pos.profit >= 0 else "🔴"
        
        print(f"  [{i}] {pos.symbol}")
        print(f"      {position_type} | Lote: {pos.volume} | P/L: {profit_emoji} ${pos.profit:.2f}")
        print(f"      Precio: {pos.price_open} → {pos.price_current}")

def wait_for_positions_to_close(max_wait_minutes=30):
    """
    Espera hasta que todas las posiciones se cierren.
    Retorna True si todas se cerraron, False si se excedió el tiempo.
    """
    start_wait = datetime.datetime.now()
    max_wait_time = datetime.timedelta(minutes=max_wait_minutes)
    
    print("\n" + "⏳"*60)
    print(" ⏰ ESPERANDO CIERRE DE POSICIONES ABIERTAS ")
    print("⏳"*60)
    
    while True:
        positions = get_open_positions()
        elapsed = datetime.datetime.now() - start_wait
        
        if not positions:
            print("\n✅ Todas las posiciones han sido cerradas.")
            return True
        
        if elapsed > max_wait_time:
            print(f"\n⚠️ Tiempo máximo de espera ({max_wait_minutes} min) alcanzado.")
            print(f"   Quedan {len(positions)} posición(es) abierta(s).")
            return False
        
        # Mostrar estado cada 5 segundos
        remaining = max_wait_time - elapsed
        print(f"\r⏳ Esperando... {len(positions)} posición(es) | "
              f"Tiempo restante: {int(remaining.total_seconds()/60)} min", end="")
        
        time.sleep(CHECK_ORDERS_INTERVAL)

# ==================== FUNCIÓN PRINCIPAL ====================

def start_quick_test():
    """
    Ejecuta el sistema de trading automático por 10 minutos.
    Optimizado para pruebas rápidas con un solo símbolo.
    """
    print("\n" + "="*70)
    print(" 🚀 QUICK TEST - AUTO TRADER (10 MIN) 🚀 ")
    print("="*70)
    print(f" Símbolo: {SYMBOL}")
    print(f" Duración: {DURATION_MINUTES} minutos")
    print(f" Intervalo: {INTERVAL_SECONDS} segundos")
    print("="*70)
    
    # Conectar a MT5
    if not connect_mt5():
        print("❌ ERROR: No se pudo establecer conexión con MetaTrader 5.")
        return
    
    print("✅ Conectado a MetaTrader 5")
    
    # Mostrar configuración
    lot = config.LOT_SIZES.get(SYMBOL, 0.35)
    print(f"\n📋 CONFIGURACIÓN:")
    print(f"   Activo: {SYMBOL}")
    print(f"   Lote: {lot}")
    print(f"   SL: 500 pips | TP: 1000 pips")
    
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
        
        print("\n" + "!"*70)
        print(f"!!! CICLO {cycle} | HORA: {current_time} | RESTANTE: {remaining:.1f} min !!!")
        print("!"*70)
        
        try:
            # Ejecutar análisis estratégico completo
            result = run_synthetic_analysis(SYMBOL)
            
            if result in ["COMPRA", "VENTA"]:
                logging.info(f"✅ Señal ejecutada: {result}")
            else:
                logging.info(f"⏸️ Sin señal: {result}")
                
        except Exception as e:
            logging.error(f"❌ Error en ciclo {cycle}: {str(e)}")
        
        # Mostrar posiciones abiertas después de cada ciclo
        positions = get_open_positions()
        display_open_positions(positions)
        
        # Determinar si hay tiempo para otro ciclo
        if datetime.datetime.now() + datetime.timedelta(seconds=INTERVAL_SECONDS) < end_time:
            print(f"\n💤 Esperando {INTERVAL_SECONDS} segundos para el próximo análisis...")
            time.sleep(INTERVAL_SECONDS)
        else:
            print("\n⏰ No hay tiempo suficiente para otro ciclo completo.")
            break
        
        cycle += 1
    
    # ==================== FINALIZACIÓN ====================
    print("\n" + "="*70)
    print(" ⏰ SESIÓN DE 10 MINUTOS COMPLETADA ")
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
            print("   Recomendación: Revisar manualmente en MT5.")
            final_positions = get_open_positions()
            display_open_positions(final_positions)
    else:
        print("\n✅ No hay posiciones abiertas. Sesión finalizada limpiamente.")
    
    # Cerrar conexión MT5
    mt5.shutdown()
    print("\n" + "="*70)
    print(" 🏁 QUICK TEST FINALIZADO - MT5 DESCONECTADO 🏁 ")
    print("="*70)

# ==================== PUNTO DE ENTRADA ====================

if __name__ == "__main__":
    try:
        start_quick_test()
    except KeyboardInterrupt:
        print("\n\n⚠️ INTERRUPCIÓN DEL USUARIO (Ctrl+C)")
        print("Cerrando conexión MT5...")
        mt5.shutdown()
        print("✅ Sesión terminada por el usuario.")
    except Exception as e:
        logging.error(f"❌ ERROR CRÍTICO: {str(e)}")
        mt5.shutdown()
        raise
