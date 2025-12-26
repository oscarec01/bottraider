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
    Abre una operación en MT5.
    action_type: 'BUY' o 'SELL'
    """
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logging.error(f"{symbol} no encontrado.")
        return False

    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            logging.error(f"symbol_select({symbol}) falló")
            return False

    point = mt5.symbol_info(symbol).point
    price = mt5.symbol_info_tick(symbol).ask if action_type == 'BUY' else mt5.symbol_info_tick(symbol).bid
    
    # Cálculo de SL y TP
    if action_type == 'BUY':
        sl = price - sl_pips * 10 * point
        tp = price + tp_pips * 10 * point
        order_type = mt5.ORDER_TYPE_BUY
    else:
        sl = price + sl_pips * 10 * point
        tp = price - tp_pips * 10 * point
        order_type = mt5.ORDER_TYPE_SELL

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
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"Error al enviar orden: {result.retcode}")
        return False
    
    logging.info(f"Orden de {action_type} ejecutada exitosamente para {symbol}")
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
