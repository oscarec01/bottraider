# 🚀 INSTRUCCIONES PARA EJECUTAR EL BOT CON CÓDIGO ACTUALIZADO

## ⚠️ MUY IMPORTANTE

El código ha sido actualizado correctamente, PERO necesitas seguir estos pasos para que Python cargue la versión nueva:

## Pasos a Seguir:

### 1. Cierra TODAS las ventanas de PowerShell/Terminal
   - Incluye la ventana donde está corriendo el bot
   - Presiona Ctrl+C si está corriendo
   - Cierra la ventana completamente (X)

### 2. Abre PowerShell NUEVO (ventana fresca)
   - Windows + X → Windows PowerShell

### 3. Navega al proyecto:
```powershell
cd e:\Documentos\VS_desarrollos\python\bot_trader
```

### 4. Activa el entorno virtual:
```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Ejecuta el bot:
```powershell
python main.py
```

## ✅ Verificación

Cuando veas una señal de COMPRA/VENTA, deberías ver en los logs:

```
📤 [Boom 1000 Index] Orden COMPRA:
   [PASO 1] Valores iniciales:
   - Precio: 16981.36
   - SL inicial: 16980.86
   - TP inicial: 16982.36
   - Parámetros: SL_pips=500, TP_pips=1000, Point=0.0001, Dígitos=4
   
   [PASO 2] Validación de stops:
   - Stops Level bróker: 0 puntos
   - Mínimo aplicado: 50 puntos = 0.005 precio
   - Distancia SL: 0.5
   ✓ SL válido (distancia 0.5 >= mínimo 0.005)
   - Distancia TP: 1.5
   ✓ TP válido (distancia 1.5 >= mínimo 0.005)
   
   [PASO 3] Antes de normalización:
   - SL: 16980.86
   - TP: 16982.36
   
   [PASO 4 - FINAL] Valores normalizados a 4 decimales:
   - Precio: 16981.3578
   - SL: 16980.8578
   - TP: 16982.3578
```

## ❌ Si NO ves estos mensajes

Significa que Python aún usa código antiguo. En ese caso:

1. **Reinicia la computadora** (para limpiar toda la memoria de Python)
2. Sigue los pasos 1-5 nuevamente

## 📞 Si el error persiste DESPUÉS de ver los logs [PASO 1-4]

Copia TODOS los logs desde [PASO 1] hasta [PASO 4] y el mensaje de error completo.
