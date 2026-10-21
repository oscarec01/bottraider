"""
Prueba de conexión MT5 + un análisis sin ejecutar órdenes.
Usa venv del proyecto. No abre la GUI.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5
import config


def main():
    path = r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
    if not mt5.initialize(path=path):
        print("INIT_FAIL", mt5.last_error())
        # reintento sin path
        if not mt5.initialize():
            print("INIT_FAIL2", mt5.last_error())
            return 1

    ok = mt5.login(
        int(config.MT5_ACCOUNT),
        password=str(config.MT5_PASSWORD),
        server=str(config.MT5_SERVER),
    )
    print("LOGIN", ok, mt5.last_error())
    info = mt5.account_info()
    if not info:
        print("NO_ACCOUNT")
        mt5.shutdown()
        return 1

    print(
        f"CONNECTED account={info.login} server={info.server} "
        f"balance={info.balance:.2f} equity={info.equity:.2f}"
    )

    # Guardar settings en BD para la GUI
    from models.database import Database

    db = Database()
    db.save_setting("mt5_account", int(config.MT5_ACCOUNT))
    db.save_setting("mt5_password", str(config.MT5_PASSWORD))
    db.save_setting("mt5_server", str(config.MT5_SERVER))
    db.save_setting("enable_auto_trading", False)  # solo análisis en esta prueba
    db.save_setting("risk_reward_ratio", 2.0)
    db.save_setting("use_atr_stops", True)
    db.save_setting("min_setup_score", 55)
    db.save_setting("confidence_threshold", 55)
    print("SETTINGS_SAVED enable_auto_trading=False")

    # Conectar capa del bot
    from models.mt5_connection import MT5Connection

    mt5.shutdown()  # la capa propia re-inicializa
    conn = MT5Connection()
    # Forzar reinicio del singleton
    conn._connected = False
    if not conn.connect(config.MT5_ACCOUNT, config.MT5_PASSWORD, config.MT5_SERVER):
        print("BOT_CONNECT_FAIL")
        return 1
    print("BOT_CONNECT_OK")

    symbol = "Volatility 75 Index"
    mt5.symbol_select(symbol, True)
    from models.trading_algorithm import TradingAlgorithm

    algo = TradingAlgorithm()
    result = algo.analyze_symbol(symbol)
    print("--- ANALYSIS ---")
    print("symbol", result.get("symbol"))
    print("error", result.get("error"))
    print("final_action", result.get("final_action"))
    print("confidence", result.get("confidence"))
    print("reasoning", result.get("reasoning"))
    p5 = result.get("paso5") or {}
    print("mode", p5.get("mode"), "setup_score", p5.get("setup_score"))
    print("paso2", result.get("paso2"))
    print(
        "paso3_veredicto",
        (result.get("paso3") or {}).get("veredicto_matematico"),
        "rsi",
        (result.get("paso3") or {}).get("rsi"),
    )
    print(
        "paso4",
        (result.get("paso4") or {}).get("señal")
        or (result.get("paso4") or {}).get("signal"),
        (result.get("paso4") or {}).get("confianza")
        or (result.get("paso4") or {}).get("confidence"),
    )
    sl, tp = algo.get_sl_tp_params(symbol)
    print(f"SL_TP {sl}/{tp}")
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
