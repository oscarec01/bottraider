# 📖 Manual de Instalación - Deriv Synthetic Indices Bot

## 🎯 Requisitos del Sistema

### Hardware Mínimo
- **Procesador**: Intel Core i3 o equivalente
- **RAM**: 4 GB mínimo, 8 GB recomendado
- **Disco**: 5 GB de espacio libre
- **Internet**: Conexión estable (mínimo 5 Mbps)

### Software
- **Sistema Operativo**: Windows 10/11 (64-bit)
- **Python**: 3.8 o superior
- **MetaTrader 5**: Última versión
- **Ollama**: Última versión

---

## 📋 Instalación Paso a Paso

### Paso 1: Instalar Python

1. **Descargar Python**
   - Visita: https://www.python.org/downloads/
   - Descarga Python 3.11 o superior
   
2. **Instalar**
   - ✅ **IMPORTANTE**: Marca "Add Python to PATH"
   - Ejecuta el instalador
   - Selecciona "Install Now"

3. **Verificar Instalación**
   ```powershell
   python --version
   # Debería mostrar: Python 3.11.x
   ```

---

### Paso 2: Instalar MetaTrader 5

1. **Crear Cuenta Deriv**
   - Visita: https://deriv.com
   - Crea una cuenta gratuita
   - Verifica tu email

2. **Descargar MT5**
   - Desde tu cuenta Deriv, descarga MetaTrader 5
   - O visita: https://www.metatrader5.com/

3. **Instalar y Configurar**
   - Ejecuta el instalador
   - Abre MT5
   - Inicia sesión con credenciales de Deriv
   
4. **Crear Cuenta DEMO** (Recomendado para pruebas)
   - En MT5: File → Open an Account
   - Selecciona "Deriv Demo"
   - Completa el registro
   - **Guarda**:
     - Login (número de cuenta)
     - Contraseña
     - Servidor (ej: "Deriv-Demo")

---

### Paso 3: Instalar Ollama

1. **Descargar Ollama**
   - Visita: https://ollama.ai/download
   - Descarga para Windows

2. **Instalar**
   - Ejecuta el instalador
   - Sigue las instrucciones
   
3. **Verificar Instalación**
   ```powershell
   ollama --version
   # Debería mostrar la versión instalada
   ```

4. **Descargar Modelo Mistral**
   ```powershell
   ollama pull mistral
   # Espera a que descargue (~4 GB)
   ```

5. **Iniciar Ollama** (debe estar siempre corriendo)
   ```powershell
   ollama serve
   ```
   > 💡 **Tip**: Deja esta terminal abierta o configura Ollama como servicio

---

### Paso 4: Configurar el Proyecto

1. **Descargar el Código**
   - Descarga o clona el proyecto en:
     ```
     e:\Documentos\VS_desarrollos\python\bot_trader
     ```

2. **Estructura Final**
   ```
   bot_trader/
   ├── auto_trader_10min.py
   ├── config.py
   ├── synthetic_trader.py
   ├── sentiment_analysis.py
   ├── technical_indicators.py
   ├── prediction_models.py
   ├── mt5_executor.py
   ├── requirements.txt
   └── README.md
   ```

---

### Paso 5: Crear Entorno Virtual

1. **Abrir PowerShell** en la carpeta del proyecto

2. **Crear Virtual Environment**
   ```powershell
   python -m venv venv
   ```

3. **Activar el Entorno**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   > ⚠️ Si hay error de permisos:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Verificar Activación**
   - Deberías ver `(venv)` al inicio del prompt

---

### Paso 6: Instalar Dependencias

```powershell
pip install -r requirements.txt
```

**Dependencias instaladas**:
- `MetaTrader5` - Conexión con MT5
- `pandas` - Manipulación de datos
- `numpy` - Cálculos numéricos
- `scikit-learn` - Regresión lineal
- `ta` - Indicadores técnicos
- `requests` - Conexión con Ollama

---

### Paso 7: Configurar Credenciales

1. **Abrir `config.py`**

2. **Editar Credenciales MT5**
   ```python
   # CONFIGURACIÓN METATRADER 5
   MT5_ACCOUNT = 12345678      # Tu número de cuenta Deriv
   MT5_PASSWORD = "TuPassword"  # Tu contraseña
   MT5_SERVER = "Deriv-Demo"    # O "Deriv-Server" para real
   ```

3. **Verificar Modelo Ollama**
   ```python
   # Configuración de IA
   OLLAMA_URL = "http://localhost:11434/api/generate"
   OLLAMA_MODEL = "mistral"
   ```

4. **Revisar Activos Permitidos**
   ```python
   ACTIVOS_PERMITIDOS = [
       "Boom 1000 Index",
       "Crash 500 Index",
       "Volatility 75 Index",
       "XAUUSD"
       # Edita según tus preferencias
   ]
   ```

5. **Guardar el archivo**

---

### Paso 8: Verificar Instalación

#### Test 1: Verificar Conexión MT5

```powershell
python -c "from mt5_executor import connect_mt5; print('✅ MT5 OK' if connect_mt5() else '❌ Error MT5')"
```

**Resultado esperado**: `✅ MT5 OK`

#### Test 2: Verificar Ollama

```powershell
python -c "import requests; r = requests.post('http://localhost:11434/api/generate', json={'model': 'mistral', 'prompt': 'Test', 'stream': False}, timeout=30); print('✅ Ollama OK' if r.status_code == 200 else '❌ Error')"
```

**Resultado esperado**: `✅ Ollama OK`

#### Test 3: Verificar Dependencias

```powershell
python -c "import MetaTrader5, pandas, numpy, sklearn, ta, requests; print('✅ Todas las dependencias OK')"
```

**Resultado esperado**: `✅ Todas las dependencias OK`

---

## 🚀 Primera Ejecución

### Pre-requisitos Antes de Ejecutar

- [ ] ✅ Ollama corriendo (`ollama serve`)
- [ ] ✅ MetaTrader 5 abierto y conectado
- [ ] ✅ Virtual environment activado
- [ ] ✅ Credenciales configuradas
- [ ] ✅ Cuenta DEMO seleccionada (para pruebas)

### Ejecutar el Bot

```powershell
python auto_trader_10min.py
```

### Qué Esperar

```
======================================================================
 🚀 INICIANDO AUTO TRADER - DERIV SYNTHETIC INDICES BOT 🚀 
======================================================================
 Duración: 10 minutos
 Intervalo de análisis: 120 segundos
 Activos a analizar: 17
======================================================================
✅ Conectado a MetaTrader 5

📋 ACTIVOS CONFIGURADOS:
   1. Boom 1000 Index                  (Lote: 0.35)
   2. Crash 500 Index                  (Lote: 0.35)
   ...
```

---

## 🔧 Solución de Problemas

### Error: "No se puede conectar a MT5"

**Causas posibles**:
- MT5 no está abierto
- Credenciales incorrectas
- Servidor incorrecto

**Solución**:
1. Abre MetaTrader 5
2. Verifica que estés conectado
3. Revisa `config.py`:
   - Número de cuenta correcto
   - Contraseña correcta
   - Servidor correcto ("Deriv-Demo" o "Deriv-Server")

---

### Error: "Ollama no responde"

**Causas posibles**:
- Ollama no está corriendo
- Modelo no descargado
- Puerto bloqueado

**Solución**:
1. Abre una terminal y ejecuta:
   ```powershell
   ollama serve
   ```
2. Verifica modelo:
   ```powershell
   ollama list
   # Debe aparecer "mistral"
   ```
3. Si no está, descárgalo:
   ```powershell
   ollama pull mistral
   ```

---

### Error: "ModuleNotFoundError"

**Causa**: Dependencias no instaladas o virtual env no activado

**Solución**:
1. Activa el virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. Reinstala dependencias:
   ```powershell
   pip install -r requirements.txt
   ```

---

### Error: "Cannot be loaded because running scripts is disabled"

**Causa**: Política de ejecución de PowerShell

**Solución**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Órdenes Rechazadas por MT5

**Causas posibles**:
- Lote mínimo incorrecto
- Símbolo no disponible
- Saldo insuficiente

**Solución**:
1. Verifica símbolos disponibles en MT5
2. Ajusta lotes en `config.py`:
   ```python
   LOT_SIZES = {
       'Boom 1000 Index': 0.35,  # Ajusta según tu broker
       'XAUUSD': 0.01,
   }
   ```
3. Verifica saldo en cuenta

---

## 📊 Validación Final

### Checklist de Instalación Completa

- [ ] Python 3.8+ instalado y en PATH
- [ ] MetaTrader 5 instalado y funcionando
- [ ] Cuenta Deriv creada (Demo para pruebas)
- [ ] Ollama instalado y corriendo
- [ ] Modelo Mistral descargado
- [ ] Proyecto descargado
- [ ] Virtual environment creado
- [ ] Dependencias instaladas
- [ ] `config.py` configurado con credenciales
- [ ] Tests de verificación pasados
- [ ] Primera ejecución exitosa

---

## 🎯 Configuración Opcional

### Ejecutar Ollama como Servicio

Para que Ollama inicie automáticamente:

1. Descarga NSSM: https://nssm.cc/download
2. Instala Ollama como servicio:
   ```powershell
   nssm install Ollama "C:\Users\[TU_USUARIO]\AppData\Local\Programs\Ollama\ollama.exe" "serve"
   nssm start Ollama
   ```

### Configurar Lanzamiento Rápido

Crea un archivo `start_bot.bat`:

```batch
@echo off
cd /d e:\Documentos\VS_desarrollos\python\bot_trader
call venv\Scripts\activate.bat
python auto_trader_10min.py
pause
```

Doble clic para ejecutar el bot.

---

## 📚 Próximos Pasos

Después de la instalación:

1. **Lee el README.md** - Guía de uso completo
2. **Revisa la documentación de algoritmos** - Entiende cómo funciona
3. **Prueba en DEMO** - Familiarízate con el bot
4. **Ajusta configuración** - Optimiza según tus necesidades
5. **Considera cuenta REAL** - Solo cuando estés 100% seguro

---

## ⚠️ Advertencias Importantes

> [!CAUTION]
> **NUNCA ejecutes el bot en cuenta REAL sin probar extensivamente en DEMO**

> [!WARNING]
> **Trading conlleva riesgo de pérdida de capital**
> - Este bot no garantiza ganancias
> - Usa solo capital que puedas permitirte perder
> - Supervisa siempre las operaciones

> [!IMPORTANT]
> **Mantén actualizados**:
> - Python y dependencias
> - MetaTrader 5
> - Ollama y modelo Mistral

---

## ✅ Instalación Completada

¡Felicitaciones! Tu bot de trading está instalado y listo para usar.

**Comando para ejecutar**:
```powershell
cd e:\Documentos\VS_desarrollos\python\bot_trader
.\venv\Scripts\Activate.ps1
python auto_trader_10min.py
```

**¡Happy Trading! 🚀📈**
