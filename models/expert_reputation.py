"""
Reputación de expertos técnicos (premio/castigo).

Se inicializa con semilla ACE (priores de credibilidad) para no empezar en cero.
Cada ciclo se registra el voto de cada experto; al evaluar predicción/trade
se premia o castiga. El consenso ponderado usa estos pesos.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from models.database import Database
from utils.logger import get_logger

logger = get_logger(__name__)

# Semilla ACE: credibilidad inicial 0–100 (no partir de cero)
ACE_SEED: Dict[str, float] = {
    "RSI": 58.0,
    "EMA_CROSS": 62.0,
    "MACD": 60.0,
    "BOLLINGER": 55.0,
    "HEIKIN_ASHI": 57.0,
    "STOCHASTIC": 52.0,
    "MICRO_SR": 54.0,
    "VOLATILITY": 50.0,
    "VOLUME": 40.0,  # tick volume sintético: poca fe inicial
    "CCI": 53.0,
    "MOMENTUM": 56.0,
    "ADX_TREND": 61.0,
}

SETTINGS_KEY = "expert_reputation_v1"
PENDING_VOTES_PREFIX = "expert_votes_pending::"


class ExpertReputation:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self._ensure_seeded()

    def _ensure_seeded(self) -> None:
        raw = self.db.get_setting(SETTINGS_KEY, None)
        if raw:
            return
        scores = {k: {"score": v, "hits": 0, "misses": 0} for k, v in ACE_SEED.items()}
        self.db.save_setting(SETTINGS_KEY, json.dumps(scores))
        logger.info("Semilla ACE de reputación de expertos aplicada")

    def _load(self) -> Dict[str, Dict[str, Any]]:
        raw = self.db.get_setting(SETTINGS_KEY, None)
        if not raw:
            self._ensure_seeded()
            raw = self.db.get_setting(SETTINGS_KEY, "{}")
        data = json.loads(raw) if isinstance(raw, str) else raw
        # Fusionar expertos nuevos de ACE_SEED
        changed = False
        for k, v in ACE_SEED.items():
            if k not in data:
                data[k] = {"score": v, "hits": 0, "misses": 0}
                changed = True
        if changed:
            self.db.save_setting(SETTINGS_KEY, json.dumps(data))
        return data

    def _save(self, data: Dict[str, Dict[str, Any]]) -> None:
        self.db.save_setting(SETTINGS_KEY, json.dumps(data))

    def get_weights(self) -> Dict[str, float]:
        """Peso 0.2–2.0 a partir del score 0–100."""
        data = self._load()
        weights = {}
        for name, info in data.items():
            score = float(info.get("score", 50))
            # 50 → 1.0; 100 → 2.0; 0 → 0.2
            weights[name] = max(0.2, min(2.0, 0.2 + (score / 100.0) * 1.8))
        return weights

    def get_scores(self) -> Dict[str, float]:
        data = self._load()
        return {k: float(v.get("score", 50)) for k, v in data.items()}

    def snapshot_votes(self, symbol: str, experts: Dict[str, str], reference_price: float) -> None:
        """Guarda votos actuales para evaluarlos cuando toque el check de predicción."""
        if not experts or reference_price <= 0:
            return
        payload = {
            "experts": experts,
            "reference_price": float(reference_price),
            "created_at": __import__("datetime").datetime.now().isoformat(),
        }
        self.db.save_setting(f"{PENDING_VOTES_PREFIX}{symbol}", json.dumps(payload))

    def evaluate_pending(self, symbol: str, current_price: float, min_move_pct: float = 0.015) -> Optional[dict]:
        """
        Premia/castiga expertos según si su voto coincidió con el movimiento real.
        COMPRA acierta si precio sube; VENTA si baja; ESPERAR si lateral.
        """
        key = f"{PENDING_VOTES_PREFIX}{symbol}"
        raw = self.db.get_setting(key, None)
        if not raw:
            return None
        pending = json.loads(raw) if isinstance(raw, str) else raw
        ref = float(pending.get("reference_price") or 0)
        if ref <= 0:
            return None

        move_pct = ((current_price - ref) / ref) * 100.0
        if abs(move_pct) < min_move_pct:
            observed = "ESPERAR"
        elif move_pct > 0:
            observed = "COMPRA"
        else:
            observed = "VENTA"

        data = self._load()
        rewarded = []
        punished = []
        for name, vote in (pending.get("experts") or {}).items():
            if name not in data:
                data[name] = {"score": ACE_SEED.get(name, 50.0), "hits": 0, "misses": 0}
            info = data[name]
            score = float(info.get("score", 50))
            if vote == "ESPERAR":
                # Neutral: pequeño castigo solo si hubo movimiento fuerte
                if observed != "ESPERAR" and abs(move_pct) >= min_move_pct * 2:
                    score = max(5, score - 0.5)
                    info["misses"] = int(info.get("misses", 0)) + 1
                    punished.append(name)
                else:
                    continue
            elif vote == observed:
                score = min(98, score + 2.5)
                info["hits"] = int(info.get("hits", 0)) + 1
                rewarded.append(name)
            else:
                score = max(5, score - 3.0)
                info["misses"] = int(info.get("misses", 0)) + 1
                punished.append(name)
            info["score"] = round(score, 2)
            data[name] = info

        self._save(data)
        self.db.save_setting(key, None)
        return {
            "observed": observed,
            "move_pct": round(move_pct, 5),
            "rewarded": rewarded,
            "punished": punished,
            "scores": self.get_scores(),
        }

    def reward_trade_outcome(self, experts_at_entry: Dict[str, str], side: str, profit: float) -> None:
        """Al cerrar trade: side COMPRA/VENTA, profit >0 gana."""
        if not experts_at_entry or side not in ("COMPRA", "VENTA"):
            return
        won = profit > 0
        data = self._load()
        for name, vote in experts_at_entry.items():
            if vote not in ("COMPRA", "VENTA"):
                continue
            if name not in data:
                data[name] = {"score": ACE_SEED.get(name, 50.0), "hits": 0, "misses": 0}
            info = data[name]
            score = float(info.get("score", 50))
            aligned = vote == side
            if won and aligned:
                score = min(98, score + 3.0)
                info["hits"] = int(info.get("hits", 0)) + 1
            elif won and not aligned:
                score = max(5, score - 1.0)
            elif (not won) and aligned:
                score = max(5, score - 3.5)
                info["misses"] = int(info.get("misses", 0)) + 1
            else:
                score = min(98, score + 1.0)  # votó en contra y el trade perdió
            info["score"] = round(score, 2)
            data[name] = info
        self._save(data)
