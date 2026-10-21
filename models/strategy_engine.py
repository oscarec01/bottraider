"""
Motor de decisión de trading orientado a edge realista en índices sintéticos Deriv.

Principios (basados en mecánica Boom/Crash + evidencia en Volatility):
- Boom: drift bajista + spike alcista. No mezclar "compra spike" con bloqueo por
  regresión bajista (eso deja el bot paralizado).
- Crash: espejo (drift alcista + spike bajista).
- Volatility: seguir tendencia (pullback EMA), no invertir solo por RSI extremo.
- La IA es confirmación, no autoridad absoluta.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class DecisionResult:
    action: str  # COMPRA | VENTA | ESPERAR
    confidence: float
    reason: str
    setup_score: int = 0
    mode: str = "generic"


def _rsi_from_panel(paso3: Dict[str, Any]) -> float:
    try:
        return float(paso3.get("rsi", 50) or 50)
    except (TypeError, ValueError):
        return 50.0


def _count_consecutive_candles(df, direction: str) -> int:
    """Cuenta velas consecutivas al cierre: 'down' (roja) o 'up' (verde)."""
    if df is None or df.empty or len(df) < 2:
        return 0
    closes = df["close"].values
    opens = df["open"].values
    count = 0
    for i in range(len(closes) - 1, -1, -1):
        is_down = closes[i] < opens[i]
        is_up = closes[i] > opens[i]
        if direction == "down" and is_down:
            count += 1
        elif direction == "up" and is_up:
            count += 1
        else:
            break
    return count


def score_boom_spike_setup(paso3: Dict[str, Any], df_recent) -> int:
    """
    Puntuación 0-100 para cazar spike alcista en Boom (comprar el dip del drift).
    Requiere confluencia: no comprar en cualquier momento.
    """
    score = 0
    rsi = _rsi_from_panel(paso3)
    experts = paso3.get("experts", {}) or {}

    # Drift prolongado (más velas rojas = más "maduro" el setup, no certeza)
    reds = _count_consecutive_candles(df_recent, "down")
    if reds >= 5:
        score += 25
    elif reds >= 3:
        score += 15

    # RSI sobrevendido (filtro, no trigger solo)
    if rsi <= 30:
        score += 30
    elif rsi <= 40:
        score += 15

    # Micro soporte / panel
    if experts.get("MICRO_SR") == "COMPRA":
        score += 15
    if experts.get("BOLLINGER") == "COMPRA":
        score += 10
    if experts.get("STOCHASTIC") == "COMPRA":
        score += 10

    buys = sum(1 for v in experts.values() if v == "COMPRA")
    if buys >= 5:
        score += 15
    elif buys >= 4:
        score += 8

    return min(100, score)


def score_crash_spike_setup(paso3: Dict[str, Any], df_recent) -> int:
    """Puntuación 0-100 para cazar spike bajista en Crash (vender el rally del drift)."""
    score = 0
    rsi = _rsi_from_panel(paso3)
    experts = paso3.get("experts", {}) or {}

    greens = _count_consecutive_candles(df_recent, "up")
    if greens >= 5:
        score += 25
    elif greens >= 3:
        score += 15

    if rsi >= 70:
        score += 30
    elif rsi >= 60:
        score += 15

    if experts.get("MICRO_SR") == "VENTA":
        score += 15
    if experts.get("BOLLINGER") == "VENTA":
        score += 10
    if experts.get("STOCHASTIC") == "VENTA":
        score += 10

    sells = sum(1 for v in experts.values() if v == "VENTA")
    if sells >= 5:
        score += 15
    elif sells >= 4:
        score += 8

    return min(100, score)


def score_volatility_trend_setup(
    paso2: Dict[str, Any],
    paso3: Dict[str, Any],
    df_recent,
) -> tuple[str, int]:
    """
    Setup de continuación de tendencia (EMA pullback style).
    Retorna (dirección_sugerida, score).
    """
    experts = paso3.get("experts", {}) or {}
    panel = paso3.get("veredicto_matematico", "NEUTRAL")
    reg = paso2.get("tendencia", "NEUTRAL")
    reg_conf = float(paso2.get("confianza", 0) or 0)
    rsi = _rsi_from_panel(paso3)
    ema = experts.get("EMA_CROSS", "ESPERAR")

    # Dirección dominante: panel + regresión + EMA
    buy_votes = 0
    sell_votes = 0
    if panel == "ALCISTA":
        buy_votes += 2
    if panel == "BAJISTA":
        sell_votes += 2
    if reg == "ALCISTA" and reg_conf >= 40:
        buy_votes += 2
    if reg == "BAJISTA" and reg_conf >= 40:
        sell_votes += 2
    if ema == "COMPRA":
        buy_votes += 2
    if ema == "VENTA":
        sell_votes += 2
    if experts.get("MACD") == "COMPRA":
        buy_votes += 1
    if experts.get("MACD") == "VENTA":
        sell_votes += 1
    if experts.get("HEIKIN_ASHI") == "COMPRA":
        buy_votes += 1
    if experts.get("HEIKIN_ASHI") == "VENTA":
        sell_votes += 1

    # Pullback: precio cerca de EMA rápida (aprox con micro S/R / bollinger)
    pullback_buy = experts.get("MICRO_SR") == "COMPRA" or experts.get("BOLLINGER") == "COMPRA"
    pullback_sell = experts.get("MICRO_SR") == "VENTA" or experts.get("BOLLINGER") == "VENTA"

    score = 0
    direction = "ESPERAR"

    if buy_votes >= sell_votes + 2 and buy_votes >= 4:
        direction = "COMPRA"
        score = min(100, buy_votes * 12)
        # RSI filtro: en uptrend no comprar sobrecomprado extremo
        if rsi > 75:
            score -= 25
        elif 45 <= rsi <= 65:
            score += 10
        if pullback_buy:
            score += 15
    elif sell_votes >= buy_votes + 2 and sell_votes >= 4:
        direction = "VENTA"
        score = min(100, sell_votes * 12)
        if rsi < 25:
            score -= 25
        elif 35 <= rsi <= 55:
            score += 10
        if pullback_sell:
            score += 15
    else:
        return "ESPERAR", 0

    return direction, max(0, min(100, score))


def decide(
    symbol: str,
    asset_type: str,
    paso2: Dict[str, Any],
    paso3: Dict[str, Any],
    paso4: Dict[str, Any],
    df_recent,
    settings: Dict[str, Any],
) -> DecisionResult:
    """
    Decide acción final consolidando capas técnicas + IA + reglas por activo.
    """
    ai_signal = paso4.get("signal", paso4.get("señal", "ESPERAR"))
    ai_conf = float(paso4.get("confidence", paso4.get("confianza", 0)) or 0)
    min_ai = float(settings.get("min_confidence_ia", 70))
    min_setup = int(settings.get("min_setup_score", 55))
    require_ai = bool(settings.get("require_ai_alignment", True))
    enable_ia = bool(settings.get("enable_ia", True))
    capital = bool(settings.get("capital_preservation", False))

    panel = paso3.get("veredicto_matematico", "NEUTRAL")
    panel_conf = float(paso3.get("confianza_matematica", 0) or 0)
    reg = paso2.get("tendencia", "NEUTRAL")
    reg_conf = float(paso2.get("confianza", 0) or 0)

    # Modo NO PERDER: umbrales altos; preferir horas sin ops a ops dudosas
    if capital:
        if asset_type in ("BOOM", "CRASH"):
            min_setup = max(min_setup, 75)
        else:
            min_setup = max(min_setup, 70)

    # ---------- BOOM: solo COMPRA en setups de dip de calidad ----------
    if asset_type == "BOOM":
        setup = score_boom_spike_setup(paso3, df_recent)
        if setup < min_setup:
            return DecisionResult(
                "ESPERAR",
                float(setup),
                f"Boom: setup débil ({setup}/{min_setup}). Esperar más drift/RSI.",
                setup,
                "boom_spike_hunt",
            )
        # IA: si está activa, debe estar alineada o ser ESPERAR con baja confianza
        if enable_ia and require_ai and ai_signal == "VENTA" and ai_conf >= min_ai:
            return DecisionResult(
                "ESPERAR",
                ai_conf,
                f"Boom: IA advierte VENTA ({ai_conf}%). No forzar compra.",
                setup,
                "boom_spike_hunt",
            )
        if enable_ia and ai_signal not in ("COMPRA", "ESPERAR") and ai_conf >= 60:
            return DecisionResult(
                "ESPERAR",
                ai_conf,
                "Boom: IA no alineada con caza de spike.",
                setup,
                "boom_spike_hunt",
            )
        # Confianza final = setup + bonus IA
        conf = setup * 0.7 + (ai_conf * 0.3 if ai_signal == "COMPRA" else setup * 0.3)
        return DecisionResult(
            "COMPRA",
            round(conf, 1),
            f"Boom spike-hunt: setup={setup}, panel={panel}, IA={ai_signal}({ai_conf}%).",
            setup,
            "boom_spike_hunt",
        )

    # ---------- CRASH: solo VENTA en setups de rally de calidad ----------
    if asset_type == "CRASH":
        setup = score_crash_spike_setup(paso3, df_recent)
        if setup < min_setup:
            return DecisionResult(
                "ESPERAR",
                float(setup),
                f"Crash: setup débil ({setup}/{min_setup}). Esperar más rally/RSI.",
                setup,
                "crash_spike_hunt",
            )
        if enable_ia and require_ai and ai_signal == "COMPRA" and ai_conf >= min_ai:
            return DecisionResult(
                "ESPERAR",
                ai_conf,
                f"Crash: IA advierte COMPRA ({ai_conf}%). No forzar venta.",
                setup,
                "crash_spike_hunt",
            )
        if enable_ia and ai_signal not in ("VENTA", "ESPERAR") and ai_conf >= 60:
            return DecisionResult(
                "ESPERAR",
                ai_conf,
                "Crash: IA no alineada con caza de spike.",
                setup,
                "crash_spike_hunt",
            )
        conf = setup * 0.7 + (ai_conf * 0.3 if ai_signal == "VENTA" else setup * 0.3)
        return DecisionResult(
            "VENTA",
            round(conf, 1),
            f"Crash spike-hunt: setup={setup}, panel={panel}, IA={ai_signal}({ai_conf}%).",
            setup,
            "crash_spike_hunt",
        )

    # ---------- VOLATILITY / STEP / XAU / GENERIC: trend continuation ----------
    direction, setup = score_volatility_trend_setup(paso2, paso3, df_recent)
    if direction == "ESPERAR" or setup < min_setup:
        return DecisionResult(
            "ESPERAR",
            float(setup),
            f"Trend setup insuficiente ({setup}/{min_setup}). Panel={panel}.",
            setup,
            "trend_follow",
        )

    # Capital first: nada de operar contra panel/regresión fuerte (ej. COMPRA + BAJISTA)
    if capital:
        if direction == "COMPRA" and panel != "ALCISTA":
            return DecisionResult(
                "ESPERAR",
                panel_conf,
                f"NO PERDER: COMPRA requiere panel ALCISTA (ahora {panel}).",
                setup,
                "trend_follow",
            )
        if direction == "VENTA" and panel != "BAJISTA":
            return DecisionResult(
                "ESPERAR",
                panel_conf,
                f"NO PERDER: VENTA requiere panel BAJISTA (ahora {panel}).",
                setup,
                "trend_follow",
            )
        if panel_conf < 50:
            return DecisionResult(
                "ESPERAR",
                panel_conf,
                f"NO PERDER: panel débil ({panel_conf:.0f}% < 50%). Esperar.",
                setup,
                "trend_follow",
            )
        if direction == "COMPRA" and reg == "BAJISTA" and reg_conf >= 55:
            return DecisionResult(
                "ESPERAR",
                reg_conf,
                f"NO PERDER: conflicto COMPRA vs regresión BAJISTA ({reg_conf:.0f}%).",
                setup,
                "trend_follow",
            )
        if direction == "VENTA" and reg == "ALCISTA" and reg_conf >= 55:
            return DecisionResult(
                "ESPERAR",
                reg_conf,
                f"NO PERDER: conflicto VENTA vs regresión ALCISTA ({reg_conf:.0f}%).",
                setup,
                "trend_follow",
            )

    # Bloqueo: IA fuerte en contra
    if enable_ia and ai_conf >= min_ai:
        if direction == "COMPRA" and ai_signal == "VENTA":
            return DecisionResult(
                "ESPERAR",
                ai_conf,
                "BLOQUEO: setup alcista pero IA fuerte en VENTA.",
                setup,
                "trend_follow",
            )
        if direction == "VENTA" and ai_signal == "COMPRA":
            return DecisionResult(
                "ESPERAR",
                ai_conf,
                "BLOQUEO: setup bajista pero IA fuerte en COMPRA.",
                setup,
                "trend_follow",
            )

    # Bonus si IA confirma
    conf = setup * 0.65 + panel_conf * 0.15
    if enable_ia and ai_signal == direction:
        conf += ai_conf * 0.2
    else:
        conf += setup * 0.2

    return DecisionResult(
        direction,
        round(min(100, conf), 1),
        f"Trend-follow {direction}: setup={setup}, panel={panel}({panel_conf}%), "
        f"IA={ai_signal}({ai_conf}%).",
        setup,
        "trend_follow",
    )
