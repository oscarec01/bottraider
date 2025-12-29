# 📘 Guía de Programación - Bot Trader IA (ACTUALIZADA 2025-12-29)

> **Versión:** 2.0  
> **Última actualización:** 2025-12-29  
> **Proyecto:** Bot de Trading Automatizado con IA + Sistema de Aprendizaje Predictivo

---

## 🎯 CAMBIOS IMPORTANTES (Versión 2.0)

### **NUEVAS FUNCIONALIDADES**

1. ✅ **Sistema de Aprendizaje Predictivo** (Paso 6)
   - Pronóstico IA para próximos 15 minutos
   - Verificación automática de predicciones anteriores
   - Ajuste dinámico de confianza (+5%/-5%)
   - UI visual con indicador de rachas (✅/❌)

2. ✅ **Especialización para Boom/Crash**
   - Lógica direccional forzada
   - Parámetros de trailing stop ampliados
   - Volumen mínimo 0.20 lotes

3. ✅ **Flujo de Configuración Mejorado**
   - Desconexión/reconexión limpia de MT5
   - Reinicio automático de workers activos
   - Sin congelamiento de UI

---

## 📋 Estructura de Base de Datos

### **Tabla: `analysis_log` (NUEVA ESTRUCTURA)**

```sql
CREATE TABLE analysis_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT,                          -- COMPRA/VENTA/ESPERAR
    confidence INTEGER,                    -- 0-100
    details TEXT,                         -- JSON completo del análisis
    prediction TEXT,                      -- JSON: {prediction, probability, target_price, rationale}
    prediction_accuracy TEXT DEFAULT 'PENDIENTE',  -- ACERTADA/FALLIDA/PENDIENTE
    prediction_adjustment INTEGER DEFAULT 0,       -- +5 o -5
    FOREIGN KEY (symbol) REFERENCES symbols(symbol)
)
```

**⚠️ IMPORTANTE:** Estructura completamente nueva desde 2025-12-29

---

## 🔧 API de Base de Datos

### **Método: `save_analysis()`**

**Nueva firma (v2.0):**
```python
def save_analysis(self, symbol: str, analysis_result: dict):
    """
    Guarda análisis completo con sistema de predicción.
    
    Args:
        symbol: Símbolo analizado
        analysis_result: Dict completo con todos los pasos + predicción
    """
```

**Estructura de `analysis_result`:**
```python
{
    'symbol': 'Boom 1000 Index',
    'timestamp': datetime.now(),
    'paso1': {...},  # Identificación
    'paso2': {...},  # Regresión lineal
    'paso3': {...},  # Panel expertos
    'paso4': {...},  # IA
    'paso5': {'decision': 'COMPRA', 'reasoning': '...'},
    'prediction': {  # NUEVO
        'prediction': 'Spike alcista esperado',
        'probability': 65,
        'target_price': 43500.0,
        'timeframe': '15 minutos',
        'rationale': 'Acumulación en RSI'
    },
    'prediction_verification': {  # NUEVO
        'had_prediction': True,
        'was_accurate': True,
        'confidence_adjustment': +5,
        'details': '✅ ACERTADA: ...'
    }
}
```

### **Método: `get_last_analysis()`**

**Nueva función (v2.0):**
```python
def get_last_analysis(self, symbol: str) -> Optional[dict]:
    """
    Obtiene último análisis con predicción para verificación.
    
    Returns:
        {
            'details': dict,      # Análisis completo
            'prediction': dict,   # Predicción JSON
            'timestamp': str,
            'accuracy': str       # ACERTADA/FALLIDA/PENDIENTE
        }
    """
```

---

## 🤖 Sistema de Análisis (6 Pasos)

### **PASO 1-5: Sin cambios**
(Mantiene estructura original)

### **PASO 6: PRONÓSTICO FUTURO (NUEVO)**

```python
def _get_prediction(self, symbol: str, recent_data: pd.DataFrame, 
                   current_analysis: dict) -> dict:
    """
    Genera pronóstico IA para próximas 3-5 velas M5 (15 min).
    
    Usa Ollama para predecir movimiento basado en:
    - Precio actual
    - RSI
    - MACD
    - Tendencia macro
    
    Returns:
        {
            'prediction': 'Spike alcista esperado',
            'timeframe': '15 minutos (3-5 velas M5)',
            'probability': 65,
            'target_price': 43500.0,
            'rationale': 'Razón técnica'
        }
    """
```

### **Verificación de Predicción Anterior (NUEVO)**

```python
def _verify_previous_prediction(self, symbol: str, 
                                current_price: float) -> dict:
    """
    Verifica acierto de predicción anterior.
    
    Lógica:
    - Compara precio actual vs predicción anterior
    - Tolerancia: 50 pips
    - Ajusta confianza: +5% si acertó, -5% si falló
    
    Returns:
        {
            'had_prediction': bool,
            'was_accurate': bool,
            'confidence_adjustment': int,  # +5 o -5
            'details': str
        }
    """
```

**Integración en `analyze_symbol()`:**
```python
# AL INICIO (antes de Paso 1)
verification = self._verify_previous_prediction(symbol, current_price)
if verification['had_prediction']:
    logger.info(f"📊 VERIFICACIÓN PREDICCIÓN ANTERIOR:")
    logger.info(f"   {verification['details']}")
    logger.info(f"   Ajuste confianza: {verification['confidence_adjustment']:+d}%")

# AL FINAL (después de Paso 5)
prediction = self._get_prediction(symbol, recent_data, result)
result['prediction'] = prediction

logger.info(f"🎯 Predicción: {prediction['prediction']}")
logger.info(f"   Probabilidad: {prediction['probability']}%")
logger.info(f"   Precio objetivo: {prediction['target_price']}")
```

---

## 🎨 UI: SymbolCard con Memoria IA

### **Nuevo Label de Predicción**

```python
# En _setup_ui():
self.prediction_label = QLabel("🔮 Predicción Anterior: Pendiente")
self.prediction_label.setWordWrap(True)
self.prediction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
self.prediction_label.setStyleSheet("...")
```

### **Actualización en `update_analysis()`**

```python
# Mostrar resultado verificación
verification = analysis_result.get('prediction_verification', {})

if verification.get('had_prediction'):
    was_accurate = verification.get('was_accurate', False)
    adjustment = verification.get('confidence_adjustment', 0)
    
    if was_accurate:
        self.prediction_label.setText(f"🔮 Predicción Anterior: ✅ ACERTADA ({adjustment:+d}%)")
        self.prediction_label.setStyleSheet("color: #2ecc71; background: rgba(46,204,113,0.1); ...")
    else:
        self.prediction_label.setText(f"🔮 Predicción Anterior: ❌ FALLIDA ({adjustment:+d}%)")
        self.prediction_label.setStyleSheet("color: #e74c3c; background: rgba(231,76,60,0.1); ...")
```

**Interpretación visual:**
- 🟢 Verde = Bot está "caliente" (racha ganadora)
- 🔴 Rojo = Bot está "frío" (racha perdedora)
- ⚪ Gris = Primera predicción

---

## ⚙️ Configuración: Flujo Sin Congelamiento

### **MainController._on_settings_saved() (NUEVO)**

**Problema original:** Reconexión síncrona causaba freeze

**Solución implementada:**
```python
def _on_settings_saved(self, new_settings: dict):
    """
    FLUJO LIMPIO:
    1. Guardar símbolos activos
    2. Detener TODOS los workers
    3. Desconectar MT5 completamente
    4. Guardar ajustes
    5. Reconectar MT5
    6. Reiniciar workers que estaban activos
    """
    try:
        # 1. Guardar estado
        active_symbols = []
        for symbol, controller in self.symbol_controllers.items():
            if controller.is_running():
                active_symbols.append(symbol)
        
        # 2. Detener workers
        for symbol in list(self.symbol_controllers.keys()):
            controller = self.symbol_controllers.get(symbol)
            if controller and controller.is_running():
                controller.stop()
        
        # 3. Desconectar MT5
        if self.mt5.is_connected():
            self.mt5.disconnect()
        
        # 4. Ajustes ya guardados en SettingsDialog
        
        # 5. Reconectar
        success = self._try_connect_mt5()
        if not success:
            self.window.show_error("Error", "No se pudo reconectar")
            return
        
        # 6. Reiniciar workers activos
        if active_symbols:
            for symbol in active_symbols:
                controller = self.symbol_controllers.get(symbol)
                if controller:
                    controller.start()
        
        self.window.show_success("Configuración", "Aplicado correctamente")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        self.window.show_error("Error", str(e))
```

**Beneficios:**
- ✅ Sin congelamiento UI
- ✅ Conexión limpia
- ✅ Workers se reinician automáticamente
- ✅ Usuario ve progreso en logs

---

## 📊 Especialización: Boom/Crash Indices

### **Detección de Índices**

```python
def _is_boom_index(self, symbol: str) -> bool:
    """Detecta Boom (spikes alcistas)"""
    keywords = ['Boom 300', 'Boom 500', 'Boom 600', 'Boom 900', 'Boom 1000']
    return any(k.lower() in symbol.lower() for k in keywords)

def _is_crash_index(self, symbol: str) -> bool:
    """Detecta Crash (spikes bajistas)"""
    keywords = ['Crash 300', 'Crash 500', 'Crash 600', 'Crash 900', 'Crash 1000']
    return any(k.lower() in symbol.lower() for k in keywords)
```

### **Validación de Señales (Modo Scalper)**

```python
def _validate_signal_compatibility(self, signal: str, symbol: str):
    """
    Valida compatibilidad señal/activo.
    
    Boom: Solo COMPRA
    Crash: Solo VENTA
    """
    scalper_mode = self.db.get_setting('scalper_mode', False)
    
    if not scalper_mode:
        return True, "Modo normal"
    
    # BOOM: Forzar solo BUY
    if self._is_boom_index(symbol):
        if signal == 'VENTA':
            return False, "[SCALPING] Señal bloqueada: Boom solo permite COMPRA"
        return True, "Compatible con Boom"
    
    # CRASH: Forzar solo SELL
    if self._is_crash_index(symbol):
        if signal == 'COMPRA':
            return False, "[SCALPING] Señal bloqueada: Crash solo permite VENTA"
        return True, "Compatible con Crash"
    
    return True, "Compatible"
```

### **Parámetros SL/TP para Boom/Crash**

```python
def get_sl_tp_params(self, symbol: str):
    """
    Parámetros ampliados para volatilidad de spikes.
    
    Boom/Crash:
    - SL: 300 pips (default, rango 200-500)
    - TP: 600 pips (default, rango 400-1000)
    
    Otros:
    - SL: 100 pips
    - TP: 200 pips
    """
    if self._is_boom_index(symbol) or self._is_crash_index(symbol):
        sl_pips = self.db.get_setting('trailing_activation_pips', 300)
        tp_pips = self.db.get_setting('trailing_distance_pips', 600)
    else:
        sl_pips = self.db.get_setting('sl_pips', 100)
        tp_pips = self.db.get_setting('tp_pips', 200)
    
    return sl_pips, tp_pips
```

### **Volumen Mínimo**

```python
def calculate_lot_size(self, symbol: str, signal: str, confidence: int):
    """
    Calcula volumen con mínimo forzado para Boom/Crash.
    
    Deriv requiere mínimo 0.20 lotes para índices sintéticos.
    """
    # ... cálculo normal ...
    
    # Forzar mínimo para Boom/Crash
    if self._is_boom_crash_index(symbol):
        final_lot_size = max(final_lot_size, 0.20)
        logger.info(f"[BOOM/CRASH] Volumen ajustado a mínimo: {final_lot_size}")
    
    return final_lot_size
```

---

## 🔄 Flujo Completo de Análisis con Predicción

```
┌─────────────────────────────────────────────┐
│  1. Obtener precio actual                   │
│  2. Verificar predicción anterior           │
│     ├─ Si existe: Comparar vs actual        │
│     ├─ Calcular accuracy                    │
│     └─ Ajustar confianza (+5%/-5%)          │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  PASO 1: Identificar activo                 │
│  PASO 2: Regresión lineal                   │
│  PASO 3: Panel de expertos                  │
│  PASO 4: Análisis IA (con confianza ajustada)│
│  PASO 5: Decisión final                     │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  PASO 6: Generar predicción futura          │
│     ├─ Llamar Ollama                        │
│     ├─ Obtener pronóstico 15 min            │
│     └─ target_price, probability, rationale │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  Guardar en BD:                              │
│     - Análisis completo                      │
│     - Predicción nueva                       │
│     - Accuracy de anterior                   │
│     - Ajuste de confianza                    │
└─────────────────────────────────────────────┘
```

---

## 📝 Logging: Nuevos Patrones

### **Predicción**
```
[PASO 6] PRONÓSTICO FUTURO:
🎯 Predicción: Spike alcista esperado
   Probabilidad: 65%
   Precio objetivo: 43500.00
   Timeframe: 15 minutos (3-5 velas M5)
   Razón: Acumulación en RSI + divergencia MACD
```

### **Verificación**
```
📊 VERIFICACIÓN PREDICCIÓN ANTERIOR:
   ✅ ACERTADA: Spike alcista @ 43500 (actual: 43520)
   Ajuste confianza: +5%
```

### **Scalper Boom/Crash**
```
[SCALPING] Señal bloqueada: Boom solo permite COMPRA
[BOOM/CRASH] Volumen ajustado a mínimo: 0.20
```

---

## ⚠️ MIGRACIONES Y CAMBIOS CRÍTICOS

### **Si vienes de versión anterior:**

1. **Base de datos:**
   ```bash
   # OPCIÓN 1: Borrar BD (pierdes historial)
   rm trading_bot.db
   
   # OPCIÓN 2: Migrar (script pendiente)
   python migrate_db.py
   ```

2. **Llamadas a save_analysis:**
   ```python
   # ❌ ANTIGUO (NO USAR)
   self.db.save_analysis(
       symbol=symbol,
       paso1=str(...),
       paso2=str(...),
       # ...
   )
   
   # ✅ NUEVO (USAR SIEMPRE)
   self.db.save_analysis(
       symbol=symbol,
       analysis_result=result  # Dict completo
   )
   ```

3. **SymbolCard:**
   - Agregar `self.prediction_label` en `_setup_ui()`
   - Actualizar `update_analysis()` para manejar verificación

---

## 🧪 Testing de Sistema de Predicción

### **Caso 1: Primera Predicción**
```python
# Ejecutar análisis
result = trading_algo.analyze_symbol("Boom 1000 Index")

# Verificar
assert 'prediction' in result
assert result['prediction']['probability'] > 0
assert result['prediction']['target_price'] > 0

# En BD
row = db.get_last_analysis("Boom 1000 Index")
assert row['prediction_accuracy'] == 'PENDIENTE'
```

### **Caso 2: Verificación Acertada**
```python
# Simular precio subió como se predijo
current_price = 43520  # Predicción era 43500
verification = trading_algo._verify_previous_prediction("Boom 1000", current_price)

assert verification['was_accurate'] == True
assert verification['confidence_adjustment'] == +5
assert '✅ ACERTADA' in verification['details']
```

### **Caso 3: Verificación Fallida**
```python
# Precio bajó en vez de subir
current_price = 43200  # Predicción era subida a 43650
verification = trading_algo._verify_previous_prediction("Boom 1000", current_price)

assert verification['was_accurate'] == False
assert verification['confidence_adjustment'] == -5
assert '❌ FALLIDA' in verification['details']
```

---

## 📚 Referencias Rápidas

### **Archivos Clave Modificados (v2.0)**

| Archivo | Cambios |
|---------|---------|
| `models/database.py` | Nueva tabla, save_analysis(), get_last_analysis() |
| `models/trading_algorithm.py` | Paso 6, verificación, ajuste confianza |
| `views/symbol_card.py` | prediction_label, color coding |
| `workers/trading_worker.py` | Llamada nueva a save_analysis |
| `controllers/main_controller.py` | Flujo limpio settings |

### **Métodos Críticos**

```python
# Database
Database.save_analysis(symbol, analysis_result)
Database.get_last_analysis(symbol)

# TradingAlgorithm
TradingAlgorithm._verify_previous_prediction(symbol, price)
TradingAlgorithm._get_prediction(symbol, data, analysis)
TradingAlgorithm._validate_signal_compatibility(signal, symbol)
TradingAlgorithm._is_boom_index(symbol)
TradingAlgorithm._is_crash_index(symbol)

# MainController
MainController._on_settings_saved(new_settings)  # Flujo limpio

# SymbolCard
SymbolCard.update_analysis(analysis_result)  # Maneja predicción
```

---

## 🎓 Mejores Prácticas (Actualizadas)

1. **Siempre usar nueva firma de save_analysis**
2. **Verificar predicción ANTES de Paso 1**
3. **Generar predicción DESPUÉS de Paso 5**
4. **Manejar casos sin predicción anterior** (primera vez)
5. **UI debe mostrar estado de predicción** (verde/rojo/gris)
6. **Logs deben incluir emoji de estado** (📊✅❌🎯)
7. **Settings: siempre desconectar antes de guardar**
8. **Boom/Crash: validar señales en modo scalper**

---

## 🚀 Checklist Pre-Deploy

- [ ] BD tiene nueva estructura (prediction, accuracy, adjustment)
- [ ] Todos los save_analysis usan nueva firma
- [ ] UI tiene prediction_label
- [ ] Ollama está corriendo localmente
- [ ] Settings se guardan sin freeze
- [ ] Boom/Crash valida señales correctamente
- [ ] Logs muestran Paso 6
- [ ] Primera ejecución muestra "Pendiente"
- [ ] Segunda ejecución muestra ✅ o ❌

---

**Fin de Guía v2.0** 🎉
