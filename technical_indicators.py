"""
Indicadores técnicos optimizados para análisis en timeframe M5.

Periodos de indicadores validados para M5:
- RSI: 14 períodos
- EMA: 9, 15, 28, 37 períodos
- MACD: 17, 35, 9 períodos
- Bollinger Bands: 20 períodos
- Stochastic: 5, 4, 2 períodos
- ATR: 14 períodos

Todos los cálculos asumen que el DataFrame contiene velas M5.
Mínimo requerido: 40 velas para EMA37.
"""

import pandas as pd
import numpy as np

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(prices, period=20):
    return prices.ewm(span=period, adjust=False).mean()

def calculate_macd(prices):
    ema12 = prices.ewm(span=17, adjust=False).mean()
    ema26 = prices.ewm(span=35, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal_line

def calculate_bollinger_bands(prices, period=20):
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    return sma + (std * 2), sma - (std * 2)

def calculate_atr(df, period=14):
    h = df.get('high')
    l = df.get('low')
    c_prev = df.get('close').shift(1)
    tr = pd.concat([(h - l), (h - c_prev).abs(), (l - c_prev).abs()], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calculate_heikin_ashi(df):
    h, l, o, c = df['high'], df['low'], df['open'], df['close']
    ha_c = (o + h + l + c) / 4
    ha_o = (o + c) / 2
    return "ALCISTA" if ha_c.iloc[-1] > ha_o.iloc[-1] else "BAJISTA"

def calculate_ema_alignment(prices):
    ema9 = prices.ewm(span=9, adjust=False).mean()
    ema15 = prices.ewm(span=15, adjust=False).mean()
    ema28 = prices.ewm(span=28, adjust=False).mean()
    ema37 = prices.ewm(span=37, adjust=False).mean()
    
    c9, c15, c28, c37 = ema9.iloc[-1], ema15.iloc[-1], ema28.iloc[-1], ema37.iloc[-1]
    
    if c9 > c15 > c28 > c37:
        return "COMPRA"
    elif c9 < c15 < c28 < c37:
        return "VENTA"
    else:
        return "ESPERAR"

def calculate_stochastic(df, k_period=5, d_period=4, slowing=2):
    # Lowest Low and Highest High for K period
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    
    # Raw %K
    denom = high_max - low_min
    # Replace 0 with NaN to avoid division by zero
    denom = denom.replace(0, 0.00001)
    
    k_raw = 100 * ((df['close'] - low_min) / denom)
    
    # Smooth %K (Slowing)
    k_line = k_raw.rolling(window=slowing).mean()
    
    # %D (Signal line)
    d_line = k_line.rolling(window=d_period).mean()
    
    k_val = k_line.iloc[-1]
    
    if k_val < 20:
        return "COMPRA", k_val
    elif k_val > 80:
        return "VENTA", k_val
    else:
        return "ESPERAR", k_val

def calculate_micro_sr(df, window=10):
    # Micro Support/Resistance based on recent local min/max
    recent_low = df['low'].rolling(window=window).min().iloc[-1]
    recent_high = df['high'].rolling(window=window).max().iloc[-1]
    current_close = df['close'].iloc[-1]
    
    # Using a small percentage of price (0.05%) or ATR could be better, but simple percentage for now
    threshold = current_close * 0.0005 
    
    status = "ESPERAR"
    
    # If price is near support (within threshold)
    if abs(current_close - recent_low) <= threshold:
        status = "COMPRA" # Bounce off support
        
    # If price is near resistance
    elif abs(current_close - recent_high) <= threshold:
        status = "VENTA" # Rejection at resistance
        
    return status

def calculate_volatility_analysis(df, atr_period=14):
    atr = calculate_atr(df, atr_period)
    current_atr = atr.iloc[-1]
    avg_atr = atr.rolling(window=20).mean().iloc[-1]
    
    is_high_vol = current_atr > avg_atr
    
    # If high volatility, we follow the trend defined by SMA20
    sma20 = df['close'].rolling(window=20).mean().iloc[-1]
    current_close = df['close'].iloc[-1]
    
    if is_high_vol:
        if current_close > sma20:
            return "COMPRA"
        else:
            return "VENTA"
    else:
        # Low volatility -> Wait for breakout
        return "ESPERAR"

def calculate_volume_analysis(df, window=20):
    # Check for volume column
    vol_col = 'tick_volume' if 'tick_volume' in df.columns else 'volume' if 'volume' in df.columns else None
    
    if not vol_col:
        return "ESPERAR"
        
    df_subset = df.iloc[-window:].copy()
    
    green_candles = df_subset[df_subset['close'] > df_subset['open']]
    red_candles = df_subset[df_subset['close'] < df_subset['open']]
    
    avg_vol_green = green_candles[vol_col].mean() if not green_candles.empty else 0
    avg_vol_red = red_candles[vol_col].mean() if not red_candles.empty else 0
    
    if avg_vol_green > avg_vol_red * 1.1: # 10% more volume on green candles
        return "COMPRA"
    elif avg_vol_red > avg_vol_green * 1.1:
        return "VENTA"
    else:
        return "ESPERAR"

def calculate_cci(df, period=20):
    tp = (df['high'] + df['low'] + df['close']) / 3
    sma = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    mad = mad.replace(0, 1e-8)
    cci = (tp - sma) / (0.015 * mad)
    val = float(cci.iloc[-1]) if not pd.isna(cci.iloc[-1]) else 0.0
    if val < -100:
        return "COMPRA", val
    if val > 100:
        return "VENTA", val
    return "ESPERAR", val


def calculate_momentum(prices, period=10):
    mom = prices.diff(period)
    val = float(mom.iloc[-1]) if not pd.isna(mom.iloc[-1]) else 0.0
    # Umbral relativo al precio
    px = float(prices.iloc[-1]) or 1.0
    thr = px * 0.0008
    if val > thr:
        return "COMPRA", val
    if val < -thr:
        return "VENTA", val
    return "ESPERAR", val


def calculate_adx_trend(df, period=14):
    """ADX simplificado + dirección DI."""
    high, low, close = df['high'], df['low'], df['close']
    up = high.diff()
    down = -low.diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr = pd.concat([
        (high - low),
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    atr = pd.Series(tr).rolling(window=period).mean()
    plus_di = 100 * pd.Series(plus_dm).rolling(window=period).mean() / atr.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm).rolling(window=period).mean() / atr.replace(0, np.nan)
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan) * 100
    adx = dx.rolling(window=period).mean().iloc[-1]
    pdi = plus_di.iloc[-1]
    mdi = minus_di.iloc[-1]
    if pd.isna(adx) or adx < 20:
        return "ESPERAR", float(adx) if not pd.isna(adx) else 0.0
    if pdi > mdi:
        return "COMPRA", float(adx)
    if mdi > pdi:
        return "VENTA", float(adx)
    return "ESPERAR", float(adx)


def get_technical_summary(df_in, consensus_threshold: int = 5, expert_weights=None):
    if df_in is None or df_in.empty: 
        return {"error": "Datos vacios", "veredicto_matematico": "NEUTRAL", "confianza_matematica": 0}
    
    df = df_in.copy()
    df.columns = [str(c).lower() for c in df.columns]
    
    try:
        c = df['close']
        
        # Verificar que hay suficientes datos
        if len(c) < 40:  # Necesitamos al menos 40 velas para EMA37
            return {
                "error": "Datos insuficientes (necesita mínimo 40 velas)",
                "veredicto_matematico": "NEUTRAL",
                "confianza_matematica": 0
            }
        
        rsi_val = calculate_rsi(c).iloc[-1]
        
        # Manejar NaN en RSI
        if pd.isna(rsi_val):
            rsi_val = 50  # Valor neutral si es NaN
        
        # Estrategia 4 EMAs
        ema_signal = calculate_ema_alignment(c)
        
        ml, ms = calculate_macd(c)
        macd_val, signal_val = ml.iloc[-1], ms.iloc[-1]
        
        # Manejar NaN en MACD
        if pd.isna(macd_val) or pd.isna(signal_val):
            macd_val = 0
            signal_val = 0
        
        bb_u, bb_l = calculate_bollinger_bands(c)
        ha_trend = calculate_heikin_ashi(df)
        
        # New Experts
        stoch_signal, stoch_val = calculate_stochastic(df)
        
        # Manejar NaN en estocástico
        if pd.isna(stoch_val):
            stoch_val = 50
            stoch_signal = "ESPERAR"
        
        sr_signal = calculate_micro_sr(df)
        volatility_signal = calculate_volatility_analysis(df)
        # En sintéticos Deriv el "volumen" es tick_volume sintético: ruido.
        # Neutralizamos este voto para no contaminar el consenso.
        volume_signal = "ESPERAR"
        cci_signal, cci_val = calculate_cci(df)
        mom_signal, _ = calculate_momentum(c)
        adx_signal, adx_val = calculate_adx_trend(df)
        
        # Recomendaciones individuales
        # RSI: umbrales un poco más estrictos (menos señales prematuras)
        experts = {
            "RSI": "COMPRA" if rsi_val < 30 else "VENTA" if rsi_val > 70 else "ESPERAR",
            "EMA_CROSS": ema_signal if ema_signal else "ESPERAR",
            "MACD": "COMPRA" if macd_val > signal_val else "VENTA" if macd_val < signal_val else "ESPERAR",
            "BOLLINGER": "COMPRA" if c.iloc[-1] < bb_l.iloc[-1] else "VENTA" if c.iloc[-1] > bb_u.iloc[-1] else "ESPERAR",
            "HEIKIN_ASHI": "COMPRA" if ha_trend == "ALCISTA" else "VENTA" if ha_trend == "BAJISTA" else "ESPERAR",
            "STOCHASTIC": stoch_signal if stoch_signal else "ESPERAR",
            "MICRO_SR": sr_signal if sr_signal else "ESPERAR",
            "VOLATILITY": volatility_signal if volatility_signal else "ESPERAR",
            "VOLUME": volume_signal,
            "CCI": cci_signal,
            "MOMENTUM": mom_signal,
            "ADX_TREND": adx_signal,
        }
        
        weights = expert_weights or {}
        buy_w = 0.0
        sell_w = 0.0
        total_w = 0.0
        for name, vote in experts.items():
            w = float(weights.get(name, 1.0))
            total_w += w
            if vote == "COMPRA":
                buy_w += w
            elif vote == "VENTA":
                sell_w += w

        buys = sum(1 for v in experts.values() if v == "COMPRA")
        sells = sum(1 for v in experts.values() if v == "VENTA")
        total_voters = max(1, len(experts))
        threshold = max(4, min(int(consensus_threshold), total_voters - 1))

        # Consenso ponderado (reputación) con fallback a conteo simple
        if total_w > 0 and weights:
            buy_pct = buy_w / total_w
            sell_pct = sell_w / total_w
            need = threshold / total_voters
            veredicto = (
                "ALCISTA" if buy_pct >= need
                else "BAJISTA" if sell_pct >= need
                else "NEUTRAL"
            )
            confianza = round(max(buy_pct, sell_pct) * 100, 1)
        else:
            veredicto = "ALCISTA" if buys >= threshold else "BAJISTA" if sells >= threshold else "NEUTRAL"
            votos_ganadores = max(buys, sells)
            confianza = round((votos_ganadores / total_voters) * 100, 1)
        
        return {
            "experts": experts,
            "expert_weights_used": {k: round(float(weights.get(k, 1.0)), 2) for k in experts},
            "veredicto_matematico": veredicto,
            "rsi": round(float(rsi_val), 1),
            "macd": "ALCISTA" if macd_val > signal_val else "BAJISTA",
            "heikin_ashi": ha_trend,
            "stoch_k": round(float(stoch_val), 1),
            "cci": round(float(cci_val), 1),
            "adx": round(float(adx_val), 1) if adx_val else 0.0,
            "confianza_matematica": confianza,
            "votes_raw": {"buys": buys, "sells": sells},
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        
        # CRÍTICO: Siempre retornar estructura completa aunque haya error
        return {
            "error": str(e),
            "error_details": error_details,
            "veredicto_matematico": "NEUTRAL",
            "confianza_matematica": 0,
            "experts": {
                "RSI": "ESPERAR",
                "EMA_CROSS": "ESPERAR",
                "MACD": "ESPERAR",
                "BOLLINGER": "ESPERAR",
                "HEIKIN_ASHI": "ESPERAR",
                "STOCHASTIC": "ESPERAR",
                "MICRO_SR": "ESPERAR",
                "VOLATILITY": "ESPERAR",
                "VOLUME": "ESPERAR",
                "CCI": "ESPERAR",
                "MOMENTUM": "ESPERAR",
                "ADX_TREND": "ESPERAR",
            },
            "rsi": 50.0,
            "macd": "NEUTRAL",
            "heikin_ashi": "NEUTRAL",
            "stoch_k": 50.0
        }

