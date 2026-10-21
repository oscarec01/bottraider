"""
Escáner de oportunidades: revisa todos los activos permitidos y recomienda
cuál abrir ahora (modo volátil / multi-símbolo).
"""

from __future__ import annotations

import time
from typing import List, Dict, Any

from PyQt6.QtCore import QThread, pyqtSignal
import MetaTrader5 as mt5

from models.mt5_connection import MT5Connection
from models.database import Database
from models.expert_reputation import ExpertReputation
from technical_indicators import get_technical_summary
from utils.logger import get_logger
import config

logger = get_logger(__name__)


class OpportunityScanner(QThread):
    recommendation = pyqtSignal(dict)  # {best, ranking, ts}
    status = pyqtSignal(str)

    def __init__(self, interval_sec: int = 45):
        super().__init__()
        self.interval_sec = interval_sec
        self._running = False
        self.mt5 = MT5Connection()
        self.db = Database()
        self.reputation = ExpertReputation(self.db)

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        logger.info("OpportunityScanner iniciado")
        while self._running:
            try:
                if not self.mt5.is_connected():
                    self.status.emit("Scanner: sin MT5")
                    time.sleep(10)
                    continue
                ranking = self._scan_all()
                best = ranking[0] if ranking else None
                payload = {
                    "best": best,
                    "ranking": ranking[:8],
                    "ts": time.time(),
                }
                self.recommendation.emit(payload)
                if best:
                    self.status.emit(
                        f"Mejor ahora: {best['symbol']} "
                        f"{best['action']} ({best['score']:.0f})"
                    )
                    self.db.save_setting("scanner_best_symbol", best["symbol"])
                    self.db.save_setting("scanner_best_action", best["action"])
                    self.db.save_setting("scanner_best_score", best["score"])
                else:
                    self.status.emit("Scanner: sin setup claro")
            except Exception as e:
                logger.error(f"Scanner error: {e}")
                self.status.emit(f"Scanner error: {e}")
            for _ in range(max(5, self.interval_sec)):
                if not self._running:
                    break
                time.sleep(1)
        logger.info("OpportunityScanner detenido")

    def _scan_all(self) -> List[Dict[str, Any]]:
        weights = self.reputation.get_weights()
        results = []
        symbols = list(getattr(config, "ACTIVOS_PERMITIDOS", []) or [])
        for symbol in symbols:
            try:
                info = self.mt5.get_symbol_info(symbol)
                if not info:
                    continue
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 120)
                if rates is None or len(rates) < 40:
                    continue
                import pandas as pd
                df = pd.DataFrame(rates)
                tech = get_technical_summary(df, consensus_threshold=5, expert_weights=weights)
                if tech.get("error"):
                    continue
                verdict = tech.get("veredicto_matematico", "NEUTRAL")
                conf = float(tech.get("confianza_matematica", 0) or 0)
                rsi = float(tech.get("rsi", 50) or 50)
                # Score de oportunidad
                score = conf
                action = "ESPERAR"
                if "BOOM" in symbol.upper() and rsi <= 40:
                    action = "COMPRA"
                    score = conf + (40 - rsi)
                elif "CRASH" in symbol.upper() and rsi >= 60:
                    action = "VENTA"
                    score = conf + (rsi - 60)
                elif verdict == "ALCISTA" and conf >= 45:
                    action = "COMPRA"
                    score = conf
                elif verdict == "BAJISTA" and conf >= 45:
                    action = "VENTA"
                    score = conf
                else:
                    continue
                # Spread penalty
                _, _, spread_pct = self.mt5.get_current_spread(symbol)
                if spread_pct > 0.2:
                    score -= 15
                results.append({
                    "symbol": symbol,
                    "action": action,
                    "score": round(score, 1),
                    "confidence": conf,
                    "panel": verdict,
                    "rsi": rsi,
                    "spread_pct": round(spread_pct, 4),
                })
            except Exception as e:
                logger.debug(f"Scan skip {symbol}: {e}")
                continue
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
