# 🏗️ Arquitectura del Proyecto - Bot Trader IA

## Índice

1. [Visión General](#visión-general)
2. [Arquitectura Dual](#arquitectura-dual)
3. [Arquitectura Moderna (MVC)](#arquitectura-moderna-mvc)
4. [Archivos Legacy](#archivos-legacy)
5. [Flujo de Datos](#flujo-de-datos)
6. [Base de Datos](#base-de-datos)
7. [Sistema de Workers](#sistema-de-workers)
8. [Comunicación entre Componentes](#comunicación-entre-componentes)

---

## Visión General

El proyecto **Bot Trader IA** implementa una **arquitectura dual**:

1. **Aplicación Moderna (GUI)**: Interfaz gráfica PyQt6 con patrón MVC
2. **Scripts Legacy (CLI)**: Scripts de línea de comandos para ejecución automatizada

Ambas arquitecturas comparten:
- Módulos de análisis técnico
- Conexión a MetaTrader 5
- Integración con Ollama (IA local)
- Sistema de predicción y aprendizaje

---

## Arquitectura Dual

### Decisión de Diseño

**¿Por qué mantener ambas arquitecturas?**

- **GUI (main.py)**: Para usuarios que prefieren control visual y configuración interactiva
- **CLI (auto_trader_10min.py)**: Para automatización programada, cron jobs, servidores headless

### Diagrama de Alto Nivel

```
┌─────────────────────────────────────┐
│         Usuario / Scheduler         │
└────────────┬────────────────────────┘
             │
       ┌─────┴─────┐
       │           │
   GUI │           │ CLI
(main.py)      (auto_trader_10min.py)
       │           │
       └─────┬─────┘
             │
    ┌────────▼─────────┐
    │  Módulos Comunes │
    ├──────────────────┤
    │ • trading_algorithm.py
    │ • technical_indicators.py
    │ • sentiment_analysis.py
    │ • prediction_models.py
    │ • mt5_connection.py
    └──────────────────┘
             │
    ┌────────▼─────────┐
    │   MetaTrader 5   │
    │   Ollama (IA)    │
    └──────────────────┘
```

---

## Arquitectura Moderna (MVC)

### Diagrama MVC

```
┌───────────────────────────────────────────────────────────┐
│                         VIEWS                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ MainWindow   │  │ SymbolCard   │  │ Settings     │   │
│  │              │  │              │  │ Dialog       │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                  │                  │            │
│         │    Señales PyQt6 (signals/slots)   │            │
└─────────┼──────────────────┼──────────────────┼───────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼───────────┐
│                      CONTROLLERS                           │
│  ┌──────────────┐  ┌──────────────┐                       │
│  │ MainCtrl     │  │ SymbolCtrl   │                       │
│  │              │  │              │                       │
│  └──────┬───────┘  └──────┬───────┘                       │
└─────────┼──────────────────┼───────────────────────────────┘
          │                  │
          │    Llamadas a    │
          │     Modelos      │
┌─────────▼──────────────────▼───────────────────────────────┐
│                         MODELS                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Database     │  │ Trading      │  │ MT5          │    │
│  │              │  │ Algorithm    │  │ Connection   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼───────────┐
│                       WORKERS                              │
│  ┌──────────────┐  ┌──────────────┐                       │
│  │ TradingWorker│  │ TrailingStop │                       │
│  │ (QThread)    │  │ Manager      │                       │
│  └──────────────┘  └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Principales

#### 📦 Models (Capa de Datos)

| Archivo | Responsabilidad |
|---------|----------------|
| `database.py` | Gestión SQLite con sistema de predicción |
| `trading_algorithm.py` | Algoritmo de 6 pasos + verificación |
| `mt5_connection.py` | Singleton para conexión MT5 |
| `symbol_config.py` | Configuración por símbolo |

#### 🎨 Views (Interfaz Gráfica)

| Archivo | Componente |
|---------|------------|
| `main_window.py` | Ventana principal con dashboard |
| `symbol_card.py` | Card visual por símbolo (precio, señal, predicción) |
| `settings_dialog.py` | Configuración MT5/Ollama/Trading |
| `history_dialog.py` | Historial de análisis y operaciones |
| `analysis_details_dialog.py` | Detalles completos del análisis de 6 pasos |

#### 🎮 Controllers (Lógica de Control)

| Archivo | Función |
|---------|---------|
| `main_controller.py` | Orquesta la aplicación, gestiona símbolos |
| `symbol_controller.py` | Control por símbolo (start/stop análisis) |

#### ⚙️ Workers (Procesamiento Asíncrono)

| Archivo | Proceso |
|---------|---------|
| `trading_worker.py` | QThread para análisis automático (cada N segundos) |
| `trailing_stop_manager.py` | Gestión de trailing stops en segundo plano |

---

## Archivos Legacy

### Estructura CLI

```python
# auto_trader_10min.py
# ├─ Sesión de 10 minutos
# ├─ Análisis cada 2 minutos
# └─ Usa synthetic_trader.py

# synthetic_trader.py
# ├─ Orquesta los 6 pasos
# ├─ Importa módulos legacy:
# │   ├─ prediction_models.py    (Regresión Lineal)
# │   ├─ technical_indicators.py (Panel de Expertos)
# │   └─ sentiment_analysis.py   (IA con Ollama)
# └─ Llama a mt5_executor.py para ejecutar
```

### Dependencia entre Moderno y Legacy

**Punto crítico**: La arquitectura moderna **importa módulos legacy**:

```python
# En models/trading_algorithm.py
try:
    from prediction_models import get_monthly_probability
    from technical_indicators import get_technical_summary
    from sentiment_analysis import analyze_price_action
    import config
except ImportError as e:
    print(f"Error importando módulos legacy: {e}")
```

**Razón**: Los algoritmos de análisis (regresión, indicadores, IA) están implementados en los archivos legacy y son reutilizados por la aplicación moderna.

---

## Flujo de Datos

### Flujo Completo de Análisis (GUI)

```
1. Usuario presiona PLAY en SymbolCard
        ↓
2. SymbolController.start()
   - Crea TradingWorker (QThread)
   - Inicia análisis periódico
        ↓
3. TradingWorker ejecuta cada N segundos:
   - trading_algorithm.analyze_symbol()
        ↓
4. TradingAlgorithm.analyze_symbol():
   ┌─ PASO 0: Verificar predicción anterior
   │  └─ Database.get_last_analysis()
   ├─ PASO 1: Identificar activo
   ├─ PASO 2: get_monthly_probability()      [legacy]
   ├─ PASO 3: get_technical_summary()        [legacy]
   ├─ PASO 4: analyze_price_action()         [legacy]
   ├─ PASO 5: Consolidar veredicto
   └─ PASO 6: _get_prediction()
        ↓
5. Guardar resultado:
   - Database.save_analysis(result)
        ↓
6. Emitir señal Qt:
   - TradingWorker.analysis_complete.emit(result)
        ↓
7. SymbolCard.update_analysis(result)
   - Actualiza UI con resultado
        ↓
8. Si señal es COMPRA/VENTA:
   - MT5Connection.open_trade()
```

---

## Base de Datos

### Esquema SQLite

#### Tabla: `analysis_log`

```sql
CREATE TABLE analysis_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT,                           -- COMPRA/VENTA/ESPERAR
    confidence INTEGER,                     -- 0-100
    details TEXT,                          -- JSON completo del análisis
    prediction TEXT,                       -- JSON: {prediction, probability, target_price, rationale}
    prediction_accuracy TEXT DEFAULT 'PENDIENTE',  -- ACERTADA/FALLIDA/PENDIENTE
    prediction_adjustment INTEGER DEFAULT 0,       -- +5 o -5
    FOREIGN KEY (symbol) REFERENCES symbols(symbol)
);
```

#### Tabla: `symbols`

```sql
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,
    symbol_type TEXT NOT NULL,
    lot_size REAL NOT NULL DEFAULT 0.35,
    is_active BOOLEAN DEFAULT 1,
    is_running BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Tabla: `trade_history`

```sql
CREATE TABLE trade_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    trade_type TEXT NOT NULL,
    entry_price REAL NOT NULL,
    stop_loss REAL NOT NULL,
    take_profit REAL NOT NULL,
    lot_size REAL NOT NULL,
    ticket INTEGER,
    open_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    close_time TIMESTAMP,
    close_price REAL,
    profit REAL,
    status TEXT DEFAULT 'OPEN',
    FOREIGN KEY (symbol) REFERENCES symbols(symbol)
);
```

#### Tabla: `settings`

```sql
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Patrón de Acceso

- **Singleton thread-safe**: Una sola instancia de `Database` para toda la aplicación
- **Conexiones thread-local**: Cada thread tiene su propia conexión SQLite
- **WAL Mode**: Mejor concurrencia para lecturas/escrituras simultáneas

---

## Sistema de Workers

### TradingWorker (QThread)

```python
class TradingWorker(QThread):
    """
    Worker asíncrono para análisis periódico.
    Se ejecuta en thread separado para no bloquear UI.
    """
    
    # Señales Qt
    analysis_complete = pyqtSignal(object)  # Emite resultado de análisis
    status_update = pyqtSignal(str)         # Emite mensajes de estado
    error_occurred = pyqtSignal(str)        # Emite errores
    
    def run(self):
        """Loop principal del worker"""
        while self.running:
            # 1. Ejecutar análisis
            result = self.trading_algo.analyze_symbol(self.symbol)
            
            # 2. Guardar en BD
            self.db.save_analysis(self.symbol, result)
            
            # 3. Emitir señal
            self.analysis_complete.emit(result)
            
            # 4. Si hay señal, ejecutar trade
            if result['final_action'] in ['COMPRA', 'VENTA']:
                self._execute_trade(result)
            
            # 5. Esperar intervalo
            time.sleep(self.interval)
```

### TrailingStopManager

```python
class TrailingStopManager(QThread):
    """
    Gestiona trailing stops para operaciones abiertas.
    Monitorea precios y ajusta SL dinámicamente.
    """
    
    def run(self):
        while self.running:
            # 1. Obtener posiciones abiertas
            positions = self.mt5.get_open_positions()
            
            # 2. Para cada posición
            for pos in positions:
                # 3. Calcular SL dinámico
                new_sl = self._calculate_trailing_sl(pos)
                
                # 4. Modificar si es necesario
                if new_sl != pos.sl:
                    self.mt5.modify_position(pos.ticket, new_sl)
            
            # 5. Esperar 5 segundos
            time.sleep(5)
```

---

## Comunicación entre Componentes

### Patrón Signals/Slots (Qt)

```python
# ========== En MainController ==========
# Conectar señal de settings guardados
self.settings_dialog.settings_saved.connect(self._on_settings_saved)

# ========== En SymbolController ==========
# Conectar señales del worker
self.worker.analysis_complete.connect(self.card.update_analysis)
self.worker.status_update.connect(self.card.update_status)
self.worker.error_occurred.connect(self.card.set_error_state)

# ========== En SymbolCard ==========
# Emitir señales de control
self.play_clicked.emit(self.symbol)
self.stop_clicked.emit(self.symbol)
```

### Ventajas del Patrón

- ✅ **Desacoplamiento**: Views no conocen Controllers directamente
- ✅ **Thread-safe**: Qt maneja la sincronización entre threads
- ✅ **Escalable**: Fácil agregar nuevos listeners

---

## Inicialización de la Aplicación

### Secuencia de Inicio (main.py)

```
1. Crear QApplication
        ↓
2. Crear MainWindow (View)
        ↓
3. Crear MainController (Controller)
   ├─ Inicializa Database
   ├─ Inicializa MT5Connection
   ├─ Carga configuración
   └─ Conecta señales
        ↓
4. Intenta conectar MT5
   ├─ Si falla → Muestra SettingsDialog
   └─ Si éxito → Continúa
        ↓
5. Carga símbolos activos
   ├─ Para cada símbolo:
   │   ├─ Crea SymbolCard (View)
   │   ├─ Crea SymbolController
   │   └─ Conecta señales
   └─ Agrega cards al Dashboard
        ↓
6. MainWindow.show()
        ↓
7. QApplication.exec() [Event Loop]
```

---

## Mejores Prácticas del Proyecto

### Separación de Responsabilidades

- ✅ **Models**: Lógica de negocio y datos (sin Qt)
- ✅ **Views**: Solo UI (sin lógica de negocio)
- ✅ **Controllers**: Orquestación entre Models y Views
- ✅ **Workers**: Procesamiento pesado en threads separados

### Gestión de Estado

- ✅ **Database**: Fuente única de verdad para datos persistentes
- ✅ **Settings**: Configuración global en BD
- ✅ **MT5Connection**: Singleton para estado de conexión
- ✅ **SymbolController**: Estado de ejecución por símbolo

### Thread Safety

- ✅ **Database**: Conexiones thread-local + Lock para escrituras
- ✅ **MT5Connection**: Lock para operaciones críticas
- ✅ **Workers**: Comunicación vía signals (thread-safe por Qt)

---

## Diagrama de Dependencias

```
main.py
  ├─ views/
  │   ├─ main_window.py
  │   └─ symbol_card.py
  │       └─ views/analysis_details_dialog.py
  │
  ├─ controllers/
  │   ├─ main_controller.py
  │   │   ├─ models/database.py
  │   │   ├─ models/mt5_connection.py
  │   │   └─ views/settings_dialog.py
  │   │
  │   └─ symbol_controller.py
  │       ├─ workers/trading_worker.py
  │       │   ├─ models/trading_algorithm.py
  │       │   │   ├─ prediction_models.py [LEGACY]
  │       │   │   ├─ technical_indicators.py [LEGACY]
  │       │   │   └─ sentiment_analysis.py [LEGACY]
  │       │   └─ models/database.py
  │       │
  │       └─ workers/trailing_stop_manager.py
  │           └─ models/mt5_connection.py
  │
  └─ config.py [GLOBAL]
```

---

## Consideraciones de Migración

### De Legacy a Moderno

Si en el futuro se decide deprecar los archivos legacy:

1. **Refactorizar algoritmos**:
   - Mover `prediction_models.py` → `models/regression_model.py`
   - Mover `technical_indicators.py` → `models/technical_analysis.py`
   - Mover `sentiment_analysis.py` → `models/ai_analysis.py`

2. **Actualizar imports** en `trading_algorithm.py`

3. **Deprecar archivos CLI**:
   - Marcar `auto_trader_10min.py` como deprecado
   - Documentar migración a GUI

### Convivencia Actual

Por ahora, **conviven sin conflicto**:
- GUI usa módulos legacy para análisis
- CLI funciona independientemente
- Ambos comparten BD y configuración

---

## Roadmap Arquitectural

### Corto Plazo
- ✅ Documentar arquitectura dual
- ✅ Refactorizar `symbol_card.py` (eliminar código duplicado)
- ✅ Agregar validaciones de startup

### Mediano Plazo
- 🔄 Agregar tests unitarios por capa
- 🔄 Implementar caching para análisis
- 🔄 Dashboard de métricas de predicción

### Largo Plazo
- ⏳ Deprecar archivos legacy (opcional)
- ⏳ Migrar a microservicios (si escala)
- ⏳ API REST para integración externa

---

**Versión**: 1.0  
**Última actualización**: 2026-01-02  
**Autor**: Bot Trader IA Team
