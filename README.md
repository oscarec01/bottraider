# 🤖 Deriv Synthetic Indices Trading Bot

Bot de trading automatizado con IA para operar en índices sintéticos de Deriv usando MetaTrader 5 y Ollama.

## 📁 Estructura del Proyecto

```
bot_trader/
├── auto_trader_10min.py      # 🎯 ARCHIVO PRINCIPAL DE EJECUCIÓN
├── config.py                  # ⚙️ Configuración (credenciales, símbolos, lotes)
├── synthetic_trader.py        # 🔍 Sistema de análisis de 5 pasos
├── sentiment_analysis.py      # 🧠 Análisis IA con Ollama
├── technical_indicators.py    # 📊 Indicadores técnicos
├── prediction_models.py       # 📈 Regresión lineal
├── mt5_executor.py           # 🔌 Conexión y ejecución MT5
└── requirements.txt          # 📦 Dependencias
```

## 🚀 Inicio Rápido

### 1. Requisitos Previos

- ✅ Python 3.8+
- ✅ MetaTrader 5 instalado
- ✅ Ollama instalado y corriendo (`ollama serve`)
- ✅ Cuenta de Deriv (Demo o Real)

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar Credenciales

Edita `config.py`:

```python
# CONFIGURACIÓN METATRADER 5
MT5_ACCOUNT = 29514809          # Tu número de cuenta Deriv
MT5_PASSWORD = "TuContraseña"   # Tu contraseña
MT5_SERVER = "Deriv-Demo"       # O "Deriv-Server" para cuenta real
```

### 4. Ejecutar el Bot

```bash
python auto_trader_10min.py
```

## 🎯 Características del Auto Trader

### ⏱️ Funcionamiento

- **Duración**: 10 minutos de sesión
- **Intervalo**: Análisis cada 2 minutos
- **Activos**: Analiza todos los símbolos configurados en `config.ACTIVOS_PERMITIDOS`
- **Monitoreo**: Si al finalizar hay órdenes abiertas, espera hasta que se cierren (máx. 30 min)

### 🔍 Sistema de Análisis (5 Pasos)

```
PASO 1: Identificación del Activo
  ↓
PASO 2: Regresión Lineal (30 días H1)
  ↓
PASO 3: Panel de Expertos Técnicos (M5)
  - RSI
  - MACD
  - Cruce de Medias EMA
  - Bandas de Bollinger
  - Heikin Ashi
  ↓
PASO 4: Análisis de IA (Ollama)
  - Reglas específicas por tipo de activo
  - Búsqueda de confluencia técnica
  ↓
PASO 5: Veredicto Final Consolidado
  - Validación de compatibilidad con tipo de activo
  - Ejecución automática si hay consenso
```

### 🎲 Reglas por Tipo de Activo

| Tipo | Detección | Señales Permitidas | Lote |
|------|-----------|-------------------|------|
| **BOOM** | Empieza con 'B' | ✅ Solo COMPRA | 0.35 |
| **CRASH** | Empieza con 'C' | ✅ Solo VENTA | 0.35 |
| **VOLATILITY** | Empieza con 'V' | ✅ COMPRA y VENTA | 0.35 |
| **XAUUSD** | Contiene 'XAU' | ✅ COMPRA y VENTA | 0.01 |

### 📊 Ejemplo de Salida

```
======================================================================
 🚀 INICIANDO AUTO TRADER - DERIV SYNTHETIC INDICES BOT 🚀 
======================================================================
 Duración: 10 minutos
 Intervalo de análisis: 120 segundos
 Activos a analizar: 17
======================================================================

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!! CICLO 1 | HORA: 15:05:30 | RESTANTE: 10.0 min !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
>>> ESCANEANDO: Boom 1000 Index
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

[PASO 1] ACTIVO BAJO ANALISIS:
 -> SIMBOLO: Boom 1000 Index
 -> MERCADO: Indices Sinteticos (Deriv)

[PASO 2] ANALISIS DE REGRESION LINEAL (30 DIAS):
 -> Tendencia: ALCISTA
 -> Confianza R2: 78%

[PASO 3] PANEL DE EXPERTOS TECNICOS (M5):
 -> [E1] RSI (32): COMPRA
 => RESULTADO PANEL: ALCISTA

[PASO 4] ANALISIS DE IA (TRADER SENIOR - mistral):
 -> TIPO DE ACTIVO DETECTADO: BOOM → Solo señales de COMPRA permitidas
 -> SEÑAL IA: COMPRA
 -> CONFIANZA IA: 85%

[PASO 5] VEREDICTO FINAL CONSOLIDADO:
 -> ACCION FINAL: >>> COMPRA <<<

[!] INICIANDO EJECUCION REAL EN MT5...
 -> Símbolo: Boom 1000 Index
 -> Lote: 0.35
 -> SL: 500 pips | TP: 1000 pips
 ✅ SUCCESS: Operacion de COMPRA abierta para Boom 1000 Index.

  ============================================================
  POSICIONES ABIERTAS: 1
  ============================================================
  [1] Boom 1000 Index
      Tipo: COMPRA | Lote: 0.35
      Precio: 25430.50 -> 25435.20
      Ganancia: 🟢 $4.50
      Ticket: 123456789
```

## ⚙️ Configuración Avanzada

### Modificar Lista de Activos

En `config.py`:

```python
ACTIVOS_PERMITIDOS = [
    "Boom 1000 Index",
    "Crash 500 Index",
    "Volatility 75 Index",
    "XAUUSD"
    # Agrega o quita símbolos según necesites
]
```

### Ajustar Lotes Mínimos

```python
LOT_SIZES = {
    'Boom 1000 Index': 0.40,  # Cambiar según tu cuenta
    'XAUUSD': 0.02,
    # ...
}
```

### Modificar SL/TP

En `synthetic_trader.py`, líneas 185-191:

```python
if 'XAU' in symbol_upper or 'GOLD' in symbol_upper:
    sl_pips = 300
    tp_pips = 600
else:
    sl_pips = 500
    tp_pips = 1000
```

### Cambiar Modelo de IA

En `config.py`:

```python
OLLAMA_MODEL = "mistral"  # Cambiar a "llama2", "codellama", etc.
```

## 🛡️ Sistema de Seguridad

### Doble Validación

1. **Paso 4 (IA)**: La IA recibe reglas específicas por tipo de activo
2. **Paso 5 (Validación Final)**: Bloquea señales incompatibles antes de ejecutar

### Ejemplos de Bloqueo

```
Símbolo: Boom 1000 Index
Señal IA: VENTA

[PASO 5] VEREDICTO FINAL CONSOLIDADO:
 -> ACCION FINAL: >>> ESPERAR <<<
 -> MOTIVO: ⚠️ BLOQUEADO: Señal de VENTA NO permitida en activo BOOM.
```

## 📝 Logs

El bot genera un archivo `auto_trader_log.txt` con todos los eventos:

```
2025-12-19 15:05:30 - [AUTO-TRADER] - ✅ Señal ejecutada para Boom 1000 Index: COMPRA
2025-12-19 15:07:30 - [AUTO-TRADER] - ⏸️ Sin señal para Crash 500 Index: ESPERAR
```

## 🔧 Solución de Problemas

### Error: "No se pudo conectar a MT5"

- Verifica que MetaTrader 5 esté abierto
- Confirma credenciales en `config.py`
- Asegúrate de tener conexión a internet

### Error: "IA no disponible"

```bash
# Verificar que Ollama esté corriendo
ollama serve

# En otra terminal
ollama run mistral
```

### Órdenes Rechazadas

- Verifica lotes mínimos en `config.LOT_SIZES`
- Confirma que el símbolo esté disponible en tu cuenta
- Revisa que tengas saldo suficiente

## 📊 Símbolos Soportados

### Booms (Solo COMPRA)
- Boom 1000 Index
- Boom 500 Index
- Boom 300 Index

### Crashes (Solo VENTA)
- Crash 1000 Index
- Crash 500 Index
- Crash 300 Index

### Volatility (Bidireccional)
- Volatility 10 Index
- Volatility 75 Index
- Volatility 100 Index

### Step Indices
- Step Rise 1200 Index (Prioridad COMPRA)
- Step Drop 1200 Index (Prioridad VENTA)

### Metales
- XAUUSD (Bidireccional, requiere >75% confianza)

## ⚠️ Advertencias

> [!WARNING]
> - Este bot ejecuta operaciones REALES en MT5
> - Se recomienda probar primero en cuenta DEMO
> - Revisa y ajusta los parámetros según tu estrategia
> - El trading conlleva riesgos de pérdida de capital

> [!IMPORTANT]
> - Requiere Ollama corriendo localmente
> - Conexión estable a internet es esencial
> - Monitorea las operaciones durante la sesión

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs en `auto_trader_log.txt`
2. Verifica que todos los servicios estén corriendo
3. Confirma la configuración en `config.py`

## 🎯 Próximas Mejoras

- [ ] Dashboard web en tiempo real
- [ ] Notificaciones por Telegram
- [ ] Backtesting con datos históricos
- [ ] Gestión avanzada de riesgo
- [ ] Multi-timeframe analysis

## 📜 Licencia

Uso personal y educativo. No hay garantías de rentabilidad.

---

**¡Happy Trading! 🚀📈**
