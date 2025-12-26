import MetaTrader5 as mt5
import config
import logging

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_mt5():
    """Inicia conexión con MetaTrader 5."""
    if not mt5.initialize():
        logging.error("Inizialize() falló, error code =", mt5.last_error())
        return False
    
    # Login
    authorized = mt5.login(config.MT5_ACCOUNT, password=config.MT5_PASSWORD, server=config.MT5_SERVER)
    if authorized:
        logging.info("Conectado exitosamente a la cuenta MT5")
        return True
    else:
        logging.error(f"Fallo al conectar a la cuenta {config.MT5_ACCOUNT}, error code = {mt5.last_error()}")
        return False

def open_trade(action_type, symbol, lot_size, sl_pips, tp_pips):
    """
    Abre una operación en MT5 con validaciones completas.
    action_type: 'BUY' o 'SELL'
    """
    logging.info(f"=== INICIANDO APERTURA DE ORDEN ===")
    logging.info(f"Símbolo: {symbol} | Tipo: {action_type} | Lote: {lot_size}")
    logging.info(f"SL: {sl_pips} pips | TP: {tp_pips} pips")
    
    # Validar símbolo
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logging.error(f"❌ {symbol} no encontrado en MT5.")
        return False

    # Asegurar visibilidad en Market Watch
    if not symbol_info.visible:
        logging.warning(f"Símbolo {symbol} no visible, agregando a Market Watch...")
        if not mt5.symbol_select(symbol, True):
            logging.error(f"❌ symbol_select({symbol}) falló")
            return False
        # Actualizar symbol_info después de hacerlo visible
        symbol_info = mt5.symbol_info(symbol)

    # Obtener información crítica
    point = symbol_info.point
    stops_level = symbol_info.trade_stops_level
    
    logging.info(f"Point: {point} | Stops Level: {stops_level} puntos ({stops_level/10} pips)")
    
    # Obtener precio actual
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        logging.error(f"❌ No se pudo obtener precio actual para {symbol}")
        return False
    
    price = tick.ask if action_type == 'BUY' else tick.bid
    logging.info(f"Precio actual: {price} (Ask: {tick.ask}, Bid: {tick.bid})")
    
    # Cálculo de SL y TP
    if action_type == 'BUY':
        sl = price - sl_pips * 10 * point
        tp = price + tp_pips * 10 * point
        order_type = mt5.ORDER_TYPE_BUY
    else:
        sl = price + sl_pips * 10 * point
        tp = price - tp_pips * 10 * point
        order_type = mt5.ORDER_TYPE_SELL
    
    logging.info(f"SL calculado: {sl} | TP calculado: {tp}")
    
    # Validar distancia de stops
    sl_distance = abs(price - sl) / point
    tp_distance = abs(tp - price) / point
    
    logging.info(f"SL distancia: {sl_distance:.0f} puntos | TP distancia: {tp_distance:.0f} puntos")
    
    if sl_distance < stops_level:
        logging.error(f"❌ SL demasiado cerca: {sl_distance:.0f} puntos < {stops_level} mínimo")
        logging.error(f"   Recomendación: Usar al menos {stops_level/10:.0f} pips")
        return False
    
    if tp_distance < stops_level:
        logging.error(f"❌ TP demasiado cerca: {tp_distance:.0f} puntos < {stops_level} mínimo")
        logging.error(f"   Recomendación: Usar al menos {stops_level/10:.0f} pips")
        return False
    
    logging.info(f"✅ Stops validados correctamente")
    
    # Determinar filling mode con fallback
    filling_mode = symbol_info.filling_mode
    
    if filling_mode & 2:  # IOC soportado
        type_filling = mt5.ORDER_FILLING_IOC
        filling_name = "IOC"
    elif filling_mode & 1:  # FOK soportado
        type_filling = mt5.ORDER_FILLING_FOK
        filling_name = "FOK"
    elif filling_mode & 4:  # RETURN soportado
        type_filling = mt5.ORDER_FILLING_RETURN
        filling_name = "RETURN"
    else:
        logging.error(f"❌ No hay filling mode compatible para {symbol}")
        return False
    
    logging.info(f"Filling mode seleccionado: {filling_name}")

    # Construir request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": 123456,
        "comment": "Bot Trader News IA",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": type_filling,
    }
    
    logging.info(f"Request completo: {request}")
    logging.info(f"Enviando orden a MT5...")

    # Enviar orden
    result = mt5.order_send(request)
    
    logging.info(f"Resultado: retcode={result.retcode}, comment='{result.comment}'")
    
    # Códigos de error comunes para debugging
    error_messages = {
        10004: "Requote - el precio cambió",
        10006: "Request rejected - solicitud rechazada por el broker",
        10013: "Invalid request - solicitud inválida",
        10014: "Invalid volume - volumen inválido",
        10015: "Invalid price - precio inválido",
        10016: "Invalid stops - SL/TP inválidos",
        10018: "Market closed - mercado cerrado",
        10019: "Not enough money - fondos insuficientes",
        10030: "Invalid request parameters - parámetros de solicitud inválidos",
        10031: "Order state error - error de estado de orden"
    }
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        error_desc = error_messages.get(result.retcode, "Error desconocido")
        logging.error(f"❌ Error al enviar orden: {result.retcode}")
        logging.error(f"   Descripción: {error_desc}")
        logging.error(f"   Comentario MT5: {result.comment}")
        return False
    
    logging.info(f"✅ Orden de {action_type} ejecutada exitosamente")
    logging.info(f"   Ticket: {result.deal} | Precio: {result.price} | Volumen: {result.volume}")
    return True

def get_market_data(symbol, count=20):
    """Obtiene los últimos precios de un símbolo."""
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, count)
    if rates is None:
        logging.error(f"Error obteniendo tasas para {symbol}: {mt5.last_error()}")
        return None
    return rates

if __name__ == "__main__":
    if connect_mt5():
        print(f"Bot conectado a MT5 (Cuenta: {config.MT5_ACCOUNT})")
        mt5.shutdown()
