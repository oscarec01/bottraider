import numpy as np
import pandas as pd

def calculate_linear_regression(df):
    if df is None or len(df) < 10: return None
    y = df['close'].values
    X = np.arange(len(y))
    coeffs = np.polyfit(X, y, 1)
    slope = coeffs[0]
    intercept = coeffs[1]
    
    # R²
    p = np.poly1d(coeffs)
    y_pred = p(X)
    r_sq = 1 - (np.sum((y - y_pred)**2) / np.sum((y - np.mean(y))**2))
    
    # Recomendación basada en pendiente y fuerza
    recomendacion = "ESPERAR"
    if r_sq > 0.4: # Solo recomendamos si hay un ajuste mínimo
        recomendacion = "COMPRAR" if slope > 0 else "VENDER"
        
    return {
        "tendencia": "ALCISTA" if slope > 0 else "BAJISTA",
        "confianza": round(r_sq * 100, 2),
        "recomendacion": recomendacion
    }

def get_monthly_probability(df_30d):
    if df_30d is None or df_30d.empty: return None
    res = calculate_linear_regression(df_30d)
    return res
