"""
Análisis paralelo lento: revisa si las decisiones recientes fueron buenas,
actualiza reputación de expertos y deja un resumen en BD/settings.
No ejecuta trades — solo aprendizaje.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta

from PyQt6.QtCore import QThread, pyqtSignal

from models.database import Database
from models.mt5_connection import MT5Connection
from models.expert_reputation import ExpertReputation
from utils.logger import get_logger

logger = get_logger(__name__)


class QualityReviewWorker(QThread):
    review_done = pyqtSignal(dict)
    status = pyqtSignal(str)

    def __init__(self, interval_sec: int = 180):
        super().__init__()
        self.interval_sec = interval_sec
        self._running = False
        self.db = Database()
        self.mt5 = MT5Connection()
        self.reputation = ExpertReputation(self.db)

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        logger.info("QualityReviewWorker iniciado (análisis paralelo lento)")
        while self._running:
            try:
                summary = self._review_cycle()
                self.review_done.emit(summary)
                self.db.save_setting("quality_review_last", json.dumps(summary))
                self.status.emit(
                    f"Calidad: {summary.get('ok', 0)} ok / "
                    f"{summary.get('bad', 0)} mal | top {summary.get('top_expert', '?')}"
                )
            except Exception as e:
                logger.error(f"Quality review error: {e}")
            for _ in range(max(30, self.interval_sec)):
                if not self._running:
                    break
                time.sleep(1)
        logger.info("QualityReviewWorker detenido")

    def _review_cycle(self) -> dict:
        ok = 0
        bad = 0
        checked = 0
        # Evaluar predicciones pendientes vencidas en símbolos activos
        symbols = []
        try:
            symbols = [
                s.get("symbol") for s in (self.db.get_active_symbols() or [])
                if s.get("symbol")
            ]
        except Exception:
            symbols = []
        if not symbols:
            try:
                rows = self.db.get_analysis_history(limit=30)
                symbols = list({r.get("symbol") for r in rows if r.get("symbol")})
            except Exception:
                symbols = []

        for symbol in symbols[:20]:
            try:
                tick = self.mt5.get_current_price(symbol)
                if not tick:
                    continue
                price = float(tick.get("bid") or tick.get("last") or 0)
                if price <= 0:
                    continue
                # Forzar evaluación de votos de expertos si la predicción ya venció
                pending_key = f"pending_prediction::{symbol}"
                raw = self.db.get_setting(pending_key, None)
                if raw:
                    pred = json.loads(raw) if isinstance(raw, str) else raw
                    created = pred.get("created_at")
                    if created:
                        age = (datetime.now() - datetime.fromisoformat(created)).total_seconds()
                        check_sec = int(self.db.get_setting("prediction_check_sec", 180) or 180)
                        if age >= check_sec:
                            result = self.reputation.evaluate_pending(symbol, price)
                            checked += 1
                            if result:
                                if len(result.get("rewarded", [])) >= len(result.get("punished", [])):
                                    ok += 1
                                else:
                                    bad += 1
                else:
                    # Sin pending de predicción: igual intentar evaluar votos huérfanos
                    result = self.reputation.evaluate_pending(symbol, price)
                    if result:
                        checked += 1
            except Exception as e:
                logger.debug(f"quality skip {symbol}: {e}")

        scores = self.reputation.get_scores()
        top = max(scores.items(), key=lambda x: x[1]) if scores else ("?", 0)
        bottom = min(scores.items(), key=lambda x: x[1]) if scores else ("?", 0)
        return {
            "ts": datetime.now().isoformat(),
            "checked": checked,
            "ok": ok,
            "bad": bad,
            "top_expert": f"{top[0]} ({top[1]:.0f})",
            "weak_expert": f"{bottom[0]} ({bottom[1]:.0f})",
            "scores": scores,
        }
