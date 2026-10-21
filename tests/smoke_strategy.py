"""Smoke test del motor de estrategia (sin MT5 ni PyQt)."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

# Cargar strategy_engine sin pasar por models/__init__.py (PyQt6)
_path = ROOT / "models" / "strategy_engine.py"
_spec = importlib.util.spec_from_file_location("strategy_engine", _path)
se = importlib.util.module_from_spec(_spec)
sys.modules["strategy_engine"] = se
_spec.loader.exec_module(se)

import technical_indicators as ti


def main():
    n = 80
    o = np.linspace(110, 100, n)
    c = o - 0.4
    df = pd.DataFrame(
        {
            "open": o,
            "high": o + 0.2,
            "low": c - 0.2,
            "close": c,
            "tick_volume": np.ones(n),
        }
    )
    tech = ti.get_technical_summary(df, 5)
    score = se.score_boom_spike_setup(tech, df)
    d = se.decide(
        "Boom 1000 Index",
        "BOOM",
        {"tendencia": "BAJISTA", "confianza": 90},
        tech,
        {"signal": "COMPRA", "confidence": 80},
        df,
        {
            "min_setup_score": 40,
            "min_confidence_ia": 70,
            "enable_ia": True,
            "require_ai_alignment": True,
        },
    )
    print("panel", tech.get("veredicto_matematico"), "rsi", tech.get("rsi"))
    print("boom_score", score)
    print("decision", d.action, d.mode, "setup", d.setup_score)
    assert d.action in ("COMPRA", "ESPERAR"), d
    # Regresión bajista NO debe bloquear Boom (bug antiguo)
    assert "OPUEST" not in d.reason.upper()
    print("OK")


if __name__ == "__main__":
    main()
