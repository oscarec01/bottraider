# Mejoras de estrategia (v2 edge) — Qué cambió y cómo validar

## Honestidad primero

Ningún bot **garantiza** ganancias. Los índices sintéticos de Deriv (sobre todo Boom/Crash) tienen un componente aleatorio diseñado para castigar estrategias ingenuas. Lo que sí se puede hacer —y es lo que se implementó— es:

1. Eliminar contradicciones lógicas que **impedían** operar bien.
2. Exigir **calidad de setup** en vez de operar por “confianza de IA” sola.
3. Ajustar riesgo (SL/TP, lotaje, trailing, límites diarios) para **sobrevivir** y dejar que un edge pequeño se acumule.

Si tras 2–4 semanas en **demo** el expectancy es negativo, hay que endurecer filtros o dejar de operar ese símbolo — no subir el lote.

---

## Diagnóstico: por qué el bot “viejo” no podía ganar de forma consistente

### 1. Contradicción Boom/Crash (bug estructural)

- En **Boom**, el precio **deriva hacia abajo** y el spike va **arriba**.
- La regresión de 30 días suele marcar **BAJISTA** (el drift).
- La IA estaba forzada a decir **COMPRA**.
- La Regla 1 antigua: *si regresión e IA se oponen → ESPERAR*.

Resultado: en Boom/Crash el bot se **auto-bloqueaba** justo cuando la idea (comprar dip / vender rally) tenía sentido.

Fuentes de contexto: [Boom/Crash mechanics](https://www.derivsharks.com/blog/boom-crash-spike-strategy), [spike risk](https://www.binarypro.app/guides/boom-crash-strategy).

### 2. SL/TP irreales

`get_sl_tp_params()` usaba **1500 pips** fijos × R:R **1:3** → TP ~4500. En M5 eso casi nunca se alcanza; el SL sí. Expectancy negativo por construcción.

Los valores de la GUI (`sl_synthetics`, etc.) **no se leían**.

### 3. IA como autoridad

La IA no tiene edge intrínseco sobre un proceso sintético. Debe ser **filtro**, no motor.

### 4. Volumen tick en sintéticos

El “volumen” de MT5 en sintéticos es ruido. Contaba como voto y ensuciaba el panel.

### 5. Trailing stop muerto

`MT5MonitorWorker` existía pero **nunca se arrancaba**.

### 6. Sobreexposición

Podía abrir varias órdenes del mismo símbolo sin límite de pérdida diaria.

---

## Qué se implementó

| Cambio | Archivo |
|--------|---------|
| Motor de decisión por tipo de activo | `models/strategy_engine.py` |
| Boom: solo COMPRA si score de dip ≥ umbral | setup RSI + velas rojas + S/R |
| Crash: solo VENTA si score de rally ≥ umbral | espejo |
| Volatility: trend-follow (no RSI reversal solo) | EMA/panel/regresión |
| Regresión/panel/consenso leen BD | `trading_algorithm.py` |
| SL desde BD + ATR opcional; TP = SL × R:R (default 2) | `get_sl_tp_params()` |
| `enable_auto_trading` respetado | `trading_worker.py` |
| 1 posición por símbolo | `trading_worker.py` |
| Riesgo ×0.5 en Boom/Crash | `trading_worker.py` |
| Límite `max_daily_loss` | `trading_worker.py` |
| Trailing monitor arranca con MT5 | `main_controller.py` |
| Nuevos controles en Ajustes | `settings_dialog.py` |
| Volumen neutralizado en panel | `technical_indicators.py` |

---

## Configuración recomendada (demo)

En **Ajustes → Gestión de Riesgo**:

| Parámetro | Valor sugerido |
|-----------|----------------|
| % Riesgo | 0.5–1.0 (Boom/Crash se reduce a la mitad solo) |
| R:R | **1:2** |
| SL sintéticos | 500 (ATR puede ampliarlo) |
| Stops ATR | **ON** |
| Score mínimo setup | **55–65** (más alto = menos trades, mejor calidad) |
| Umbral setup final | **55–60** |
| Confianza mínima IA | 70 |
| Auto-trading | ON solo cuando estés listo |
| Trailing stop | ON (activación ~200–300, distancia ~100–150) |
| Pérdida diaria máxima | p.ej. 3–5% del balance en USD |
| Objetivo diario | p.ej. 2–3% — parar al llegar |

**Símbolos para empezar (uno o dos, no diez):**

1. `Volatility 75 Index` o `Volatility 50 Index` (trend-follow).
2. Un solo Boom **o** un solo Crash (spike-hunt con filtro).

No operes Boom 300 y Crash 300 a la vez “por diversificar”: correlacionan en riesgo de cola.

---

## Cómo revisar que funciona (checklist)

### A) Humo técnico (5 min)

```bash
python main.py
```

1. Conecta MT5 demo.
2. Añade **un** símbolo (p.ej. V75).
3. En logs debe aparecer:
   - `strategy_engine` / `MODO: trend_follow` o `boom_spike_hunt`
   - `MT5MonitorWorker iniciado`
4. Con auto-trading **OFF**: debe analizar y **no** abrir órdenes.
5. Con score alto y auto-trading ON: máximo **1** posición por símbolo.

### B) Calidad de señales (2–3 días demo)

Anota por cada señal:

- ¿Hubo setup_score ≥ umbral?
- ¿TP/SL alcanzados o trailing?
- Profit factor aproximado (ganancias brutas / pérdidas brutas)

Si winrate < 40% con R:R 1:2, sube `min_setup_score` a 65–70.

### C) Boom/Crash específico

Solo entrar cuando el log diga setup fuerte (RSI extremo + varias velas de drift).  
Si entra “en cualquier momento”, el score mínimo está demasiado bajo.

---

## Lo que aún falta (siguiente iteración)

1. **Backtester** M5 out-of-sample (sin esto, cualquier ajuste es hipótesis).
2. Contador de ticks desde último spike (mejor proxy que velas M5 para Boom/Crash).
3. Modo “drift trade” opcional (vender Boom / comprar Crash) con SL amplio y tamaño mínimo — distinto del spike-hunt.
4. Sacar credenciales de `config.py` a `.env`.

---

## Resumen en una frase

El bot ya no se contradice en Boom/Crash, exige setups medibles, usa SL/TP coherentes y protege capital; **ahora toca validar en demo** y subir filtros si el expectancy no es positivo — no arriesgar más size.
