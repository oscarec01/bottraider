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

def get_technical_summary(df_in):
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
        volume_signal = calculate_volume_analysis(df)
        
        # Recomendaciones individuales
        experts = {
            "RSI": "COMPRA" if rsi_val < 35 else "VENTA" if rsi_val > 65 else "ESPERAR",
            "EMA_CROSS": ema_signal if ema_signal else "ESPERAR",
            "MACD": "COMPRA" if macd_val > signal_val else "VENTA" if macd_val < signal_val else "ESPERAR",
            "BOLLINGER": "COMPRA" if c.iloc[-1] < bb_l.iloc[-1] else "VENTA" if c.iloc[-1] > bb_u.iloc[-1] else "ESPERAR",
            "HEIKIN_ASHI": "COMPRA" if ha_trend == "ALCISTA" else "VENTA" if ha_trend == "BAJISTA" else "ESPERAR",
            "STOCHASTIC": stoch_signal if stoch_signal else "ESPERAR",
            "MICRO_SR": sr_signal if sr_signal else "ESPERAR",
            "VOLATILITY": volatility_signal if volatility_signal else "ESPERAR",
            "VOLUME": volume_signal if volume_signal else "ESPERAR"
        }
        
        # Conteo para veredicto final
        buys = sum(1 for v in experts.values() if v == "COMPRA")
        sells = sum(1 for v in experts.values() if v == "VENTA")
        
        # Total voters = 9 now
        total_voters = 9
        threshold = 5 # Majority
        
        veredicto = "ALCISTA" if buys >= threshold else "BAJISTA" if sells >= threshold else "NEUTRAL"
        
        # Calcular confianza basada en el consenso
        votos_ganadores = max(buys, sells)
        confianza = round((votos_ganadores / total_voters) * 100, 1)
        
        return {
            "experts": experts,
            "veredicto_matematico": veredicto,
            "rsi": round(float(rsi_val), 1),
            "macd": "ALCISTA" if macd_val > signal_val else "BAJISTA",
            "heikin_ashi": ha_trend,
            "stoch_k": round(float(stoch_val), 1),
            "confianza_matematica": confianza
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
            "experts": {  # ← AGREGAR ESTO
                "RSI": "ESPERAR",
                "EMA_CROSS": "ESPERAR",
                "MACD": "ESPERAR",
                "BOLLINGER": "ESPERAR",
                "HEIKIN_ASHI": "ESPERAR",
                "STOCHASTIC": "ESPERAR",
                "MICRO_SR": "ESPERAR",
                "VOLATILITY": "ESPERAR",
                "VOLUME": "ESPERAR"
            },
            "rsi": 50.0,
            "macd": "NEUTRAL",
            "heikin_ashi": "NEUTRAL",
            "stoch_k": 50.0
        }

