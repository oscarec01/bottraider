"""
Gestión de posiciones orientada a: no regalar la ganancia, dejar correr winners.

Filosofía del usuario:
- Si está ganando y el trade sigue a favor → DEJARLO (no cerrar prematuro).
- Cuando ya hay ganancia suficiente → ASEGURARLA (SL a break-even+) y trail.
- Pérdidas: solo SL del broker (micro_loss OFF por defecto).
- Nadie garantiza "no perder nunca"; esto minimiza dar marcha atrás lo ganado.
"""

from __future__ import annotations

import time

import MetaTrader5 as mt5

from models.database import Database
from models.mt5_connection import MT5Connection
from utils.logger import get_logger

logger = get_logger(__name__)


class MicroProfitManager:
    def __init__(self):
        self.db = Database()
        self.mt5 = MT5Connection()
        # ticket -> ya se bloqueó profit (SL movido a BE+)
        self._locked = set()

    def check_and_close(self):
        if not self.db.get_setting("frequency_scalp_mode", False):
            return

        take_usd = float(self.db.get_setting("micro_profit_usd", 0.5) or 0.5)
        stop_usd = float(self.db.get_setting("micro_loss_usd", 0) or 0)
        # True (default): asegurar y dejar correr; False: cerrar al tocar take_usd
        let_run = bool(self.db.get_setting("let_winners_run", True))

        positions = self.mt5.get_positions()
        if not positions:
            return

        for pos in positions:
            ticket = pos["ticket"]
            profit = float(pos.get("profit") or 0.0)
            symbol = pos["symbol"]

            # Corte de pérdida opcional (casi siempre OFF)
            if stop_usd > 0 and profit <= -abs(stop_usd):
                logger.info(
                    f"[PROTECT] STOP ${profit:.4f} → cerrar {symbol} #{ticket}"
                )
                self.mt5.close_position(ticket, comment=f"Stop-{stop_usd}")
                self._record_result(symbol, won=False)
                self._locked.discard(ticket)
                continue

            if take_usd <= 0 or profit < take_usd:
                continue

            # Ya hay micro-ganancia
            if let_run:
                if ticket not in self._locked:
                    ok = self._lock_profit(ticket, pos)
                    if ok:
                        self._locked.add(ticket)
                        logger.info(
                            f"[PROTECT] +${profit:.2f} asegurado con SL BE+. "
                            f"Dejo CORRER {symbol} #{ticket} (let_winners_run)"
                        )
                    else:
                        # No se puede poner SL de BE por stops_level → cerrar para no regalar
                        logger.info(
                            f"[PROTECT] No cabe SL de BE (stops broker). "
                            f"Cierro para asegurar +${profit:.2f} {symbol} #{ticket}"
                        )
                        self.mt5.close_position(ticket, comment=f"Secure+{take_usd}")
                        self._record_result(symbol, won=True)
                        self._locked.discard(ticket)
                # Si ya está locked: no cerrar; el trailing sigue moviendo el SL
            else:
                logger.info(
                    f"[PROTECT] take-profit fijo +${profit:.2f} → cerrar {symbol} #{ticket}"
                )
                self.mt5.close_position(ticket, comment=f"Win+{take_usd}")
                self._record_result(symbol, won=True)
                self._locked.discard(ticket)

        # Limpieza de tickets cerrados
        open_tickets = {p["ticket"] for p in self.mt5.get_positions()}
        self._locked = {t for t in self._locked if t in open_tickets}

    def _lock_profit(self, ticket: int, pos: dict) -> bool:
        """
        Mueve SL a break-even + buffer (lado correcto), respetando stops_level.
        BUY: SL > open_price (protege ganancia).
        SELL: SL < open_price.
        """
        try:
            mt5_pos = mt5.positions_get(ticket=ticket)
            if not mt5_pos:
                return False
            p = mt5_pos[0]
            info = mt5.symbol_info(p.symbol)
            tick = mt5.symbol_info_tick(p.symbol)
            if not info or not tick:
                return False

            point = info.point
            digits = info.digits
            stops = int(info.trade_stops_level or 0)
            min_dist = stops * point * 1.05
            # Buffer mínimo de profit asegurado (~0.1% del precio o 2*point)
            buffer = max(point * 10, abs(p.price_open) * 0.00005)

            if p.type == mt5.ORDER_TYPE_BUY:
                # Ideal: SL por encima de la entrada
                target_sl = round(p.price_open + buffer, digits)
                # Debe quedar lejos del Bid
                max_sl_allowed = round(tick.bid - min_dist, digits)
                if target_sl > max_sl_allowed:
                    # Aún no hay recorrido suficiente para BE+ con stops del broker
                    return False
                new_sl = target_sl
                # Solo mejorar SL (subir)
                if p.sl > 0 and new_sl <= p.sl:
                    return True  # ya está igual o mejor
            else:
                target_sl = round(p.price_open - buffer, digits)
                min_sl_allowed = round(tick.ask + min_dist, digits)
                if target_sl < min_sl_allowed:
                    return False
                new_sl = target_sl
                if p.sl > 0 and new_sl >= p.sl:
                    return True

            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": p.symbol,
                "sl": new_sl,
                "tp": p.tp,
            }
            result = mt5.order_send(request)
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                err = result.comment if result else mt5.last_error()
                logger.warning(f"[PROTECT] No se pudo lock SL #{ticket}: {err}")
                return False

            logger.info(
                f"[PROTECT] SL locked #{ticket} {p.symbol}: {p.sl} → {new_sl} "
                f"(entrada {p.price_open})"
            )
            return True
        except Exception as e:
            logger.error(f"[PROTECT] lock_profit error: {e}")
            return False

    def _record_result(self, symbol: str, won: bool):
        key = f"loss_streak::{symbol}"
        if won:
            self.db.save_setting(key, 0)
            return
        streak = int(self.db.get_setting(key, 0) or 0) + 1
        self.db.save_setting(key, streak)
        max_streak = int(self.db.get_setting("max_loss_streak", 3) or 3)
        if streak >= max_streak:
            cooldown = int(self.db.get_setting("loss_streak_cooldown_sec", 300) or 300)
            self.db.save_setting(
                f"cooldown_until::{symbol}", int(time.time()) + cooldown
            )
            logger.warning(
                f"[PROTECT] {symbol}: {streak} pérdidas → pausa {cooldown}s"
            )
            self.db.save_setting(key, 0)
