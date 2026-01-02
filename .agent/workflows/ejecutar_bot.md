---
description: Cómo ejecutar el Bot de Trading
---

# Workflow: Ejecutar Bot de Trading

## Opción 1: Interfaz Gráfica (Recomendado) 🖥️

### Paso 1: Verificar Servicios Externos

Asegúrate de que los siguientes servicios estén corriendo:

- **MetaTrader 5**: Debe estar abierto y conectado a Deriv
- **Ollama**: Ejecutar en terminal separada:
  ```bash
  ollama serve
  ```

### Paso 2: Activar Entorno Virtual

// turbo
```bash
cd e:\Documentos\VS_desarrollos\python\bot_trader
venv\Scripts\activate
```

### Paso 3: Ejecutar Aplicación GUI

// turbo
```bash
python main.py
```

### Paso 4: Configurar en la Aplicación

1. Click en **"⚙️ Configuración"**
2. Verificar credenciales MT5:
   - Cuenta
   - Contraseña
   - Servidor (Deriv-Demo o Deriv-Server)
3. Configurar Ollama URL (default: `http://localhost:11434/api/generate`)
4. Ajustar parámetros de trading si es necesario
5. Click en **"Guardar"**

### Paso 5: Agregar Símbolos

1. Click en **"+ Agregar Símbolo"**
2. Seleccionar símbolo de la lista
3. Ajustar tamaño de lote (default: 0.35 para sintéticos)
4. Click en **"Agregar"**

### Paso 6: Iniciar Análisis

1. En la card del símbolo, click en **"▶ Iniciar"**
2. El bot comenzará análisis automático cada N segundos
3. Ver resultados en tiempo real:
   - 📈/📉 Última señal
   - 🎯 Confianza
   - 🔮 Estado de predicción anterior
   - 📊 Detalles del panel de expertos

### Paso 7: Monitorear

- Ver logs en el panel inferior
- Click en **"📊 Ver Detalles"** para análisis completo
- Click en **"📈 Historial"** para ver análisis anteriores

---

## Opción 2: Modo CLI (Legacy) 💻

### Paso 1: Verificar Servicios

Igual que Opción 1.

### Paso 2: Activar Entorno Virtual

// turbo
```bash
cd e:\Documentos\VS_desarrollos\python\bot_trader
venv\Scripts\activate
```

### Paso 3: Configurar config.py

Editar manualmente `config.py`:

```python
MT5_ACCOUNT = 29514809
MT5_PASSWORD = "TuContraseña"
MT5_SERVER = "Deriv-Demo"
OLLAMA_MODEL = "mistral"
```

### Paso 4: Ejecutar Trader Automático

// turbo
```bash
python auto_trader_10min.py
```

**Características**:
- Sesión de 10 minutos
- Análisis cada 2 minutos
- Ejecuta automáticamente todas las señales
- Logs en `auto_trader_log.txt`

---

## Solución de Problemas

### Error: "No se pudo conectar a MT5"

1. Verificar que MT5 esté abierto
2. Verificar credenciales en configuración
3. Asegurarse de que MT5 esté conectado a internet
4. Reiniciar MT5 y volver a intentar

### Error: "IA no disponible"

1. Verificar que Ollama esté corriendo:
   ```bash
   curl http://localhost:11434/api/version
   ```
2. Si no responde, ejecutar:
   ```bash
   ollama serve
   ```
3. Verificar modelo instalado:
   ```bash
   ollama list
   ```
4. Si falta el modelo:
   ```bash
   ollama pull mistral
   ```

### Error: "Invalid Stops" al ejecutar órdenes

- **Causa**: SL/TP muy cercanos al precio actual
- **Solución**: En configuración, aumentar:
  - SL pips: de 500 a 800
  - TP pips: de 1000 a 1600

### Error: "AttributeError" en symbol_card.py

- **Causa**: Código desactualizado (corregido en versión actual)
- **Solución**: Hacer `git pull` para obtener última versión

---

## Verificación de Éxito

### GUI Funcionando Correctamente

- ✅ Ventana principal se abre sin errores
- ✅ Settings muestra conexión MT5 exitosa (verde)
- ✅ Símbolos agregados muestran precio actual
- ✅ Al hacer click en "Iniciar", LED cambia a verde
- ✅ Logs muestran "PASO 1", "PASO 2", etc.
- ✅ Predicción anterior muestra estado (Pendiente/Acertada/Fallida)

### CLI Funcionando Correctamente

- ✅ Conexión MT5 exitosa al inicio
- ✅ Logs muestran análisis de cada símbolo
- ✅ Se muestran los 6 pasos completos
- ✅ Veredicto final se muestra claramente
- ✅ Si hay señal, se ejecuta en MT5

---

## Consejos de Uso

### Para Mejores Resultados

1. **Empezar con cuenta DEMO** hasta familiarizarse
2. **Monitorear las primeras horas** para ajustar configuración
3. **Revisar precisión de predicciones** en el historial
4. **Ajustar umbral de confianza** según resultados (default: 70%)
5. **Usar modo scalper** para Boom/Crash (fuerza dirección correcta)

### Parámetros Recomendados

#### Índices Sintéticos (Boom/Crash/Volatility)
- Lote: 0.35 - 0.50
- SL: 500-800 pips
- TP: 1000-1600 pips
- Confianza mínima: 70%
- Intervalo análisis: 120 segundos

#### Metales (XAUUSD)
- Lote: 0.01 - 0.02
- SL: 1500 pips
- TP: 4500 pips
- Confianza mínima: 75%
- Intervalo análisis: 300 segundos

---

## Desactivar Bot

### GUI
1. Click en **"⏹ Detener"** en cada símbolo activo
2. Esperar a que LED se ponga gris
3. Cerrar aplicación

### CLI
- Presionar `Ctrl+C` para cancelar sesión
- El bot esperará a que se cierren operaciones abiertas (hasta 30 min)

---

**Última actualización**: 2026-01-02
