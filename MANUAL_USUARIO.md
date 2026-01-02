# 📖 Manual de Usuario - Bot de Trading con Inteligencia Artificial

**Para usuarios sin conocimientos técnicos**

---

## 🎯 ¿Qué hace este bot?

Imagina que tienes un **asistente financiero experto** que trabaja 24/7 analizando el mercado de valores por ti. Este bot es ese asistente. 

**En pocas palabras**: El bot observa el precio de activos financieros (como el oro o índices especiales) y decide si es buen momento para COMPRAR, VENDER, o simplemente ESPERAR.

**Lo especial**: No toma decisiones al azar. Sigue un proceso científico de **6 pasos**, donde cada paso es como consultar a un experto diferente. Al final, combina todas las opiniones y decide qué hacer.

---

## 🧠 ¿Cómo piensa el bot? Los 6 Pasos del Análisis

Imagina que quieres comprar una casa. No decides de inmediato, ¿verdad? Primero:
1. Verificas el barrio
2. Ves el precio histórico de casas similares
3. Consultas con expertos (arquitecto, abogado, etc.)
4. Usas tu intuición y experiencia
5. Consolidadas toda la información
6. Haces una predicción del valor futuro

**El bot hace exactamente lo mismo**, pero con activos financieros.

---

## 📊 PASO 0: Verificación de Predicciones Anteriores (Sistema de Aprendizaje)

**¿Qué hace?**  
Antes de analizar, el bot revisa si su predicción anterior fue correcta.

### Ejemplo práctico:

**Ayer a las 10:00 AM**, el bot analizó el índice "Boom 1000" y predijo:
```
🎯 Predicción: "El precio subirá a $43,500 en los próximos 15 minutos"
💡 Probabilidad: 65%
⏰ Timeframe: 15 minutos
```

**Hoy a las 10:15 AM**, el bot verifica:
```
📌 Precio predicho: $43,500
📌 Precio real actual: $43,520
📊 Diferencia: +$20 (muy cerca!)
```

**Resultado:**
```
✅ PREDICCIÓN ACERTADA
🎓 Aprendizaje: +5% de confianza
💬 Mensaje: "El bot está 'caliente', en racha ganadora"
```

### ¿Por qué es importante?

Igual que tú confías más en un doctor que acierta con frecuencia, el bot ajusta su confianza según su historial:

- **Racha ganadora** (✅✅✅) → Más confianza → Señales más fuertes
- **Racha perdedora** (❌❌❌) → Menos confianza → Señales más cautelosas

### En la interfaz verás:

```
🔮 Predicción Anterior: ✅ ACERTADA (+5%)
Fondo verde = Bot en racha ganadora
```

```
🔮 Predicción Anterior: ❌ FALLIDA (-5%)
Fondo rojo = Bot ajustando estrategia
```

```
🔮 Predicción Anterior: Pendiente
Fondo gris = Primera predicción del día
```

---

## 📊 PASO 1: Identificación del Activo

**¿Qué hace?**  
El bot identifica QUÉ está analizando.

### Ejemplo:

Tú le dices: "Analiza Boom 1000 Index"

El bot registra:
```
📋 IDENTIFICACIÓN:
   Nombre: Boom 1000 Index
   Tipo: Índice Sintético
   Mercado: Deriv
   Hora de análisis: 10:00 AM
   Precio actual: $43,450
```

**¿Por qué importa?**  
Diferentes activos se comportan diferente:

- **Boom 1000**: Diseñado para tener "saltos" alcistas (solo debería comprar)
- **Crash 500**: Diseñado para tener "caídas" bajistas (solo debería vender)
- **Oro (XAUUSD)**: Puede subir o bajar libremente

El bot memoriza esto para validar sus decisiones más adelante.

---

## 📈 PASO 2: Regresión Lineal (Tendencia a 30 Días)

**¿Qué hace?**  
Mira el comportamiento del precio en los **últimos 30 días** y determina la tendencia general.

### Analogía: El Clima

Imagina que quieres saber si hace calor o frío:
- No miras solo la temperatura de HOY
- Miras las últimas 4 semanas
- Si ha subido gradualmente: **Tendencia CALIENTE**
- Si ha bajado gradualmente: **Tendencia FRÍA**

### Ejemplo con números reales:

El bot descarga 30 días de precios del "Boom 1000 Index":

```
Día 1:  $40,000
Día 5:  $40,500
Día 10: $41,200
Día 15: $42,000
Día 20: $42,800
Día 25: $43,300
Día 30: $43,450  ← Precio actual
```

**Pregunta**: ¿Los precios están subiendo o bajando?

**Respuesta del bot:**
```
📈 REGRESIÓN LINEAL (30 días):
   Tendencia: ALCISTA ⬆️
   Confianza: 78%
   Interpretación: "El precio ha subido consistentemente"
   Recomendación: COMPRA
```

### ¿Cómo calcula la confianza?

El bot traza una "línea imaginaria" sobre los precios:

```
Precio
$44k │                          ●
     │                      ●  /
$43k │                  ●    /
     │              ●      /
$42k │          ●        /  ← Línea de tendencia
     │      ●          /
$41k │  ●            /
     │            /
$40k │●         /
     └─────────────────────── Tiempo (30 días)
```

- Si los puntos (●) están **muy cerca** de la línea: Alta confianza (78%)
- Si están **muy dispersos**: Baja confianza (30%)

**En este ejemplo:** Los precios siguen bien la línea, así que tiene 78% de confianza en que la tendencia es alcista.

---

## 🔬 PASO 3: Panel de Expertos Técnicos

**¿Qué hace?**  
Consulta con **9 expertos virtuales**, cada uno especializado en un aspecto diferente del mercado.

### Analogía: Comité Médico

Si tienes un problema de salud complejo, no consultas a un solo doctor. Consultas:
- Cardiólogo
- Neurólogo
- Nutricionista
- etc.

Luego, **votan** sobre el diagnóstico. Si 7 de 9 dicen lo mismo, es una decisión confiable.

### Los 9 Expertos del Bot:

#### 1️⃣ **Experto RSI** (Relative Strength Index)

**¿Qué mira?** Si el activo está "cansado" de subir o bajar midiendo la fuerza relativa.

**Fórmula Matemática:**
```
RSI = 100 - [100 / (1 + RS)]

Donde:
RS = (Ganancia Promedio de 14 períodos) / (Pérdida Promedio de 14 períodos)

Ganancia_i = max(Cierre_i - Cierre_(i-1), 0)
Pérdida_i = max(Cierre_(i-1) - Cierre_i, 0)
```

**Ejemplo con Cálculo Real:**

Supongamos los últimos 14 periodos de cambios de precio:

```
Periodo  Cierre   Cambio   Ganancia  Pérdida
1        $43,200    -       -         -
2        $43,250   +$50     $50       $0
3        $43,200   -$50     $0        $50
4        $43,300   +$100    $100      $0
5        $43,280   -$20     $0        $20
6        $43,320   +$40     $40       $0
7        $43,350   +$30     $30       $0
8        $43,340   -$10     $0        $10
9        $43,380   +$40     $40       $0
10       $43,400   +$20     $20       $0
11       $43,390   -$10     $0        $10
12       $43,420   +$30     $30       $0
13       $43,410   -$10     $0        $10
14       $43,450   +$40     $40       $0
15       $43,440   -$10     $0        $10
```

**Paso 1:** Calcular promedios
```
Suma de Ganancias = 50+100+40+30+40+20+30+40 = $350
Promedio Ganancias = $350 / 14 = $25

Suma de Pérdidas = 50+20+10+10+10+10 = $110  
Promedio Pérdidas = $110 / 14 = $7.86
```

**Paso 2:** Calcular RS
```
RS = $25 / $7.86 = 3.18
```

**Paso 3:** Calcular RSI
```
RSI = 100 - [100 / (1 + 3.18)]
RSI = 100 - [100 / 4.18]
RSI = 100 - 23.92
RSI = 76.08
```

**Resultado:**
```
RSI = 76 → SOBRECOMPRA (>70)

🔍 Interpretación:
   76 está por encima de 70 = SOBRECOMPRA
   Significa: "El precio subió mucho, probable corrección"
   Voto: VENTA 📉
```

**Zonas de Decisión:**
```
RSI < 30:  SOBREVENTA → Señal de COMPRA ⬆️
30 ≤ RSI ≤ 70:  ZONA NEUTRAL → ESPERAR ⏸
RSI > 70:  SOBRECOMPRA → Señal de VENTA ⬇️
```

---

#### 2️⃣ **Experto MACD** (Moving Average Convergence Divergence)

**¿Qué mira?** El impulso y la convergencia/divergencia de medias móviles exponenciales.

**Fórmula Matemática:**
```
MACD = EMA₁₇(precio) - EMA₃₅(precio)
Signal = EMA₉(MACD)
Histograma = MACD - Signal

Donde EMA se calcula:
EMA_t = (Precio_t × α) + (EMA_(t-1) × (1 - α))
α = 2 / (período + 1)
```

**Ejemplo con Cálculo Real:**

Supongamos que calculamos las EMAs sobre los últimos datos:

**Para EMA17:**
```
α₁₇ = 2 / (17 + 1) = 2 / 18 = 0.1111

Si EMA₁₇ anterior = $43,300
Precio actual = $43,450

EMA₁₇_nueva = ($43,450 × 0.1111) + ($43,300 × 0.8889)
EMA₁₇_nueva = $4,827.77 + $38,499.37
EMA₁₇_nueva = $43,327.14
```

**Para EMA35:**
```
α₃₅ = 2 / (35 + 1) = 2 / 36 = 0.0556

Si EMA₃₅ anterior = $43,200
Precio actual = $43,450

EMA₃₅_nueva = ($43,450 × 0.0556) + ($43,200 × 0.9444)
EMA₃₅_nueva = $2,415.82 + $40,798.08
EMA₃₅_nueva = $43,213.90
```

**Calcular MACD:**
```
MACD = EMA₁₇ - EMA₃₅
MACD = $43,327.14 - $43,213.90
MACD = +$113.24
```

**Calcular Signal:**
```
α₉ = 2 / (9 + 1) = 0.2

Si Signal anterior = $95.00
MACD actual = $113.24

Signal_nueva = ($113.24 × 0.2) + ($95.00 × 0.8)
Signal_nueva = $22.65 + $76.00
Signal_nueva = $98.65
```

**Calcular Histograma:**
```
Histograma = MACD - Signal
Histograma = $113.24 - $98.65
Histograma = +$14.59
```

**Resultado:**
```
MACD: +$113.24
Signal: +$98.65
Histograma: +$14.59

🔍 Interpretación:
   MACD (+113.24) > Signal (+98.65) = MOMENTO ALCISTA
   Histograma positivo y creciente = Fuerza compradora
   Voto: COMPRA 📈
```

**Reglas de Decisión:**
```
MACD > Signal:  ALCISTA → COMPRA
MACD < Signal:  BAJISTA → VENTA
MACD cruza Signal ↑:  Señal FUERTE de COMPRA
MACD cruza Signal ↓:  Señal FUERTE de VENTA
```

---

#### 3️⃣ **Experto Heikin Ashi** (Velas Suavizadas)

**¿Qué mira?** Tendencia suavizada usando velas japonesas modificadas.

**Fórmulas Matemáticas:**
```
HA_Close = (Open + High + Low + Close) / 4

HA_Open = (HA_Open_(anterior) + HA_Close_(anterior)) / 2

HA_High = max(High, HA_Open, HA_Close)

HA_Low = min(Low, HA_Open, HA_Close)
```

**Ejemplo con Cálculo Real:**

**Vela Actual (vela normal):**
```
Open:  $43,400
High:  $43,470
Low:   $43,380
Close: $43,450
```

**Vela Anterior (Heikin Ashi):**
```
HA_Open_anterior = $43,320
HA_Close_anterior = $43,390
```

**Paso 1:** Calcular HA_Close
```
HA_Close = (Open + High + Low + Close) / 4
HA_Close = ($43,400 + $43,470 + $43,380 + $43,450) / 4
HA_Close = $173,700 / 4
HA_Close = $43,425
```

**Paso 2:** Calcular HA_Open
```
HA_Open = (HA_Open_anterior + HA_Close_anterior) / 2
HA_Open = ($43,320 + $43,390) / 2
HA_Open = $86,710 / 2
HA_Open = $43,355
```

**Paso 3:** Calcular HA_High
```
HA_High = max($43,470, $43,355, $43,425)
HA_High = $43,470
```

**Paso 4:** Calcular HA_Low
```
HA_Low = min($43,380, $43,355, $43,425)
HA_Low = $43,355
```

**Resultado:**
```
Vela Heikin Ashi:
HA_Open:  $43,355
HA_Close: $43,425
HA_High:  $43,470
HA_Low:   $43,355

🔍 Análisis:
   HA_Close ($43,425) > HA_Open ($43,355)
   Diferencia: +$70
   Color: VERDE 🟢 (Alcista)
   
   Si hay 5 velas verdes consecutivas:
   Voto: COMPRA 📈
```

**Interpretación de Colores:**
```
🟢 Vela Verde: HA_Close > HA_Open (Alcista)
🔴 Vela Roja:  HA_Close < HA_Open (Bajista)

Secuencias:
🟢🟢🟢🟢🟢 = Tendencia ALCISTA fuerte → COMPRA
🔴🔴🔴🔴🔴 = Tendencia BAJISTA fuerte → VENTA
🟢🔴🟢🔴🟢 = Indecisión/Consolidación → ESPERAR
```

---

#### 4️⃣ **Experto EMA Cross** (Cruce de 4 Medias Móviles)

**¿Qué mira?** Alineación perfecta de 4 EMAs (9, 15, 28, 37) para confirmar tendencia.

**Fórmula para cada EMA:**
```
EMA_t = (Precio_t × α) + (EMA_(t-1) × (1 - α))

Donde:
α_9 = 2/(9+1) = 0.20
α_15 = 2/(15+1) = 0.125
α_28 = 2/(28+1) = 0.069
α_37 = 2/(37+1) = 0.053
```

**Ejemplo con Cálculo Real:**

**Precio Actual:** $43,450

**Calculando cada EMA:**

```
EMA9:
  EMA_anterior = $43,380
  EMA9_nueva = ($43,450 × 0.20) + ($43,380 × 0.80)
  EMA9_nueva = $8,690 + $34,704
  EMA9_nueva = $43,394

EMA15:
  EMA_anterior = $43,350
  EMA15_nueva = ($43,450 × 0.125) + ($43,350 × 0.875)
  EMA15_nueva = $5,431.25 + $37,931.25
  EMA15_nueva = $43,362.50

EMA28:
  EMA_anterior = $43,300
  EMA28_nueva = ($43,450 × 0.069) + ($43,300 × 0.931)
  EMA28_nueva = $2,998.05 + $40,312.30
  EMA28_nueva = $43,310.35

EMA37:
  EMA_anterior = $43,250
  EMA37_nueva = ($43,450 × 0.053) + ($43,250 × 0.947)
  EMA37_nueva = $2,302.85 + $40,957.75
  EMA37_nueva = $43,260.60
```

**Resultado:**
```
EMA9:  $43,394.00
EMA15: $43,362.50
EMA28: $43,310.35
EMA37: $43,260.60

🔍 Verificar alineación:
   EMA9 ($43,394) > EMA15 ($43,362.50) ✓
   EMA15 ($43,362.50) > EMA28 ($43,310.35) ✓
   EMA28 ($43,310.35) > EMA37 ($43,260.60) ✓
   
   ✅ ALINEACIÓN PERFECTA ALCISTA
   Voto: COMPRA 📈
```

**Reglas de Alineación:**
```
ALCISTA Fuerte:
EMA9 > EMA15 > EMA28 > EMA37 → COMPRA

BAJISTA Fuerte:
EMA9 < EMA15 < EMA28 < EMA37 → VENTA

Cualquier otro orden → ESPERAR (consolidación/indecisión)
```

---

#### 5️⃣ **Experto Bollinger Bands** (Bandas de Bollinger)

**¿Qué mira?** Si el precio está en zonas extremas de volatilidad.

**Fórmulas Matemáticas:**
```
Banda_Media = SMA(20)

Banda_Superior = SMA(20) + (2 × σ)

Banda_Inferior = SMA(20) - (2 × σ)

Desviación Estándar:
σ = √[Σ(Precio_i - SMA)² / 20]
```

**Ejemplo con Cálculo Real:**

**Últimos 20 precios de cierre:**
```
$43,200, $43,250, $43,220, $43,280, $43,300,
$43,320, $43,310, $43,350, $43,380, $43,400,
$43,390, $43,420, $43,410, $43,450, $43,440,
$43,470, $43,460, $43,480, $43,490, $43,500
```

**Paso 1:** Calcular SMA(20)
```
Suma = $868,300
SMA(20) = $868,300 / 20
SMA(20) = $43,415
```

**Paso 2:** Calcular Desviación Estándar
```
Para cada precio calculamos (Precio - SMA)²:

($43,200 - $43,415)² = (-$215)² = $46,225
($43,250 - $43,415)² = (-$165)² = $27,225
($43,220 - $43,415)² = (-$195)² = $38,025
... (continuar para los 20)
($43,500 - $43,415)² = (+$85)² = $7,225

Suma de cuadrados = $325,000
Varianza = $325,000 / 20 = $16,250
σ = √$16,250 = $127.48
```

**Paso 3:** Calcular Bandas
```
Banda_Superior = SMA + (2 × σ)
Banda_Superior = $43,415 + (2 × $127.48)
Banda_Superior = $43,415 + $254.96
Banda_Superior = $43,669.96

Banda_Inferior = SMA - (2 × σ)
Banda_Inferior = $43,415 - $254.96
Banda_Inferior = $43,160.04
```

**Resultado:**
```
Banda Superior:  $43,670
Banda Media:     $43,415 (SMA20)
Banda Inferior:  $43,160
Precio Actual:   $43,150

🔍 Análisis:
   Precio ($43,150) < Banda Inferior ($43,160)
   Estado: SOBREVENTA (tocando banda inferior)
   Significado: Precio muy bajo, probable rebote
   Voto: COMPRA 📈
```

**Zonas de Decisión:**
```
Precio ≤ Banda Inferior:  SOBREVENTA → COMPRA
Banda Inferior < Precio < Banda Superior:  NEUTRAL → ESPERAR
Precio ≥ Banda Superior:  SOBRECOMPRA → VENTA
```

---

#### 6️⃣ **Experto Estocástico** (K5, D4, Slowing 2)

**¿Qué mira?** Posición del precio en su rango reciente.

**Fórmulas Matemáticas:**
```
%K_raw = 100 × [(Close - Low₅) / (High₅ - Low₅)]

%K_smooth = SMA₂(%K_raw)  [Slowing period = 2]

%D = SMA₄(%K_smooth)  [D period = 4]

Donde:
Low₅ = Mínimo de los últimos 5 períodos
High₅ = Máximo de los últimos 5 períodos
```

**Ejemplo con Cálculo Real:**

**Últimos 5 períodos:**
```
Período  High      Low       Close
1        $43,500   $43,380   $43,450
2        $43,520   $43,400   $43,480
3        $43,550   $43,420   $43,500
4        $43,480   $43,350   $43,400
5        $43,460   $43,340   $43,350  ← Actual
```

**Paso 1:** Identificar máximo y mínimo del rango
```
High₅ = max($43,500, $43,520, $43,550, $43,480, $43,460)
High₅ = $43,550

Low₅ = min($43,380, $43,400, $43,420, $43,350, $43,340)
Low₅ = $43,340
```

**Paso 2:** Calcular %K_raw para el período actual
```
Close_actual = $43,350

%K_raw = 100 × [($43,350 - $43,340) / ($43,550 - $43,340)]
%K_raw = 100 × [$10 / $210]
%K_raw = 100 × 0.0476
%K_raw = 4.76
```

**Paso 3:** Aplicar Slowing (SMA de 2 períodos)
```
Si %K_raw anterior = 15.2
%K_raw actual = 4.76

%K_smooth = (15.2 + 4.76) / 2
%K_smooth = 19.96 / 2
%K_smooth = 9.98
```

**Paso 4:** Calcular %D (promedio de 4 períodos de %K)
```
Últimos 4 valores de %K_smooth: 25.3, 18.7, 15.2, 9.98

%D = (25.3 + 18.7 + 15.2 + 9.98) / 4
%D = 69.18 / 4
%D = 17.30
```

**Resultado:**
```
%K = 9.98
%D = 17.30

🔍 Interpretación:
   %K (9.98) < 20 = SOBREVENTA EXTREMA
   Precio está en el fondo de su rango
   Probable rebote alcista inminente
   Voto: COMPRA 📈
```

**Zonas de Decisión:**
```
%K < 20:   SOBREVENTA → COMPRA ⬆️
20 ≤ %K ≤ 80:   ZONA NEUTRAL → ESPERAR ⏸
%K > 80:   SOBRECOMPRA → VENTA ⬇️
```

---

#### 7️⃣ **Experto Micro Soportes/Resistencias**

**¿Qué mira?** "Pisos" (soportes) y "techos" (resistencias) donde el precio rebota.

**Algoritmo de Detección:**
```
Soporte_Micro = min(Low de últimos 10 períodos)
Resistencia_Micro = max(High de últimos 10 períodos)
Precio_Actual = Close actual

Umbral = Precio_Actual × 0.0005  (0.05%)

Distancia_Soporte = |Precio_Actual - Soporte_Micro|
Distancia_Resistencia = |Precio_Actual - Resistencia_Micro|
```

**Ejemplo con Cálculo Real:**

**Últimos 10 períodos:**
```
Período  High      Low       Close
1        $43,520   $43,380   $43,450
2        $43,550   $43,400   $43,480
3        $43,580   $43,420   $43,520
4        $43,530   $43,390   $43,450
5        $43,510   $43,370   $43,420
6        $43,490   $43,350   $43,400
7        $43,470   $43,340   $43,380  ← Mínimo
8        $43,500   $43,360   $43,420
9        $43,520   $43,380   $43,450
10       $43,490   $43,350   $43,370  ← Actual
```

**Paso 1:** Identificar niveles clave
```
Soporte_Micro = min de todos los Lows
Soporte_Micro = $43,340

Resistencia_Micro = max de todos los Highs
Resistencia_Micro = $43,580

Precio_Actual = $43,370
```

**Paso 2:** Calcular distancias
```
Distancia_Soporte = |$43,370 - $43,340|
Distancia_Soporte = $30

Distancia_Resistencia = |$43,370 - $43,580|
Distancia_Resistencia = $210
```

**Paso 3:** Calcular umbral de "cercanía"
```
Umbral = $43,370 × 0.0005
Umbral = $21.69
```

**Paso 4:** Determinar señal
```
¿Distancia_Soporte ($30) < Umbral ($21.69)? NO, pero muy cerca

Ajustamos umbral a 0.1% para más flexibilidad:
Umbral_ajustado = $43,370 × 0.001 = $43.37

¿Distancia_Soporte ($30) < Umbral_ajustado ($43.37)? SÍ
```

**Resultado:**
```
Precio Actual: $43,370
Soporte Micro: $43,340
Distancia: $30 (0.069%)

🔍 Interpretación:
   Precio muy cerca del soporte
   Histórico: Precio rebotó 3 veces en $43,340
   Probabilidad alta de rebote
   Voto: COMPRA 📈
```

**Lógica de Decisión:**
```
Cerca de Soporte → Esperar REBOTE → COMPRA
Cerca de Resistencia → Esperar RECHAZO → VENTA
En zona media → Sin señal clara → ESPERAR
```

---

#### 8️⃣ **Experto Volatilidad** (ATR - Average True Range)

**¿Qué mira?** Qué tan "nervioso" está el mercado y si hay suficiente movimiento para operar.

**Fórmulas Matemáticas:**
```
True Range (TR) = max(High - Low, |High - Close_anterior|, |Low - Close_anterior|)

ATR(14) = SMA₁₄(TR)

ATR_promedio = SMA₂₀(ATR)

Volatilidad_Alta = ATR actual > ATR_promedio
```

**Ejemplo con Cálculo Real:**

**Último período:**
```
High actual: $43,500
Low actual: $43,350
Close anterior: $43,380
```

**Paso 1:** Calcular True Range actual
```
Opción 1: High - Low = $43,500 - $43,350 = $150
Opción 2: |High - Close_ant| = |$43,500 - $43,380| = $120
Opción 3: |Low - Close_ant| = |$43,350 - $43,380| = $30

TR = max($150, $120, $30) = $150
```

**Paso 2:** Calcular ATR(14) - promedio de últimos 14 TR
```
Últimos 14 TR:
$140, $130, $160, $145, $155, $148, $142,
$138, $152, $146, $150, $144, $149, $150

Suma_TR = $2,049
ATR(14) = $2,049 / 14
ATR(14) = $146.36
```

**Paso 3:** Calcular ATR promedio (SMA20 del ATR)
```
Últimos 20 valores de ATR:
$138, $140, $142, $139, $145, $148, $150, $146,
$144, $149, $151, $147, $143, $146, $148, $152,
$149, $147, $145, $146.36

Suma_ATR = $2,920.36
ATR_promedio = $2,920.36 / 20
ATR_promedio = $146.02
```

**Paso 4:** Comparar con SMA(20)
```
SMA(20) del precio = $43,415
Precio actual = $43,450
```

**Resultado:**
```
ATR actual: $146.36
ATR promedio: $146.02
Volatilidad: ALTA ($146.36 > $146.02)

Precio actual ($43,450) > SMA20 ($43,415)

🔍 Interpretación:
   Alta volatilidad detectada
   Precio por encima de media móvil
   En alta volatilidad: seguir la tendencia
   Tendencia: ALCISTA
   Voto: COMPRA 📈
```

**Reglas de Decisión:**
```
Si Volatilidad ALTA:
  Si Precio > SMA20 → COMPRA (seguir tendencia alcista)
  Si Precio < SMA20 → VENTA (seguir tendencia bajista)

Si Volatilidad BAJA:
  → ESPERAR (poco movimiento, difícil operar)
```

---

#### 9️⃣ **Experto Volumen**

**¿Qué mira?** Quién tiene más fuerza: compradores o vendedores, basado en el volumen negociado.

**Algoritmo de Análisis:**
```
Para últimos 20 períodos:

Volumen_Velas_Verdes = Σ(Volumen donde Close > Open)
Volumen_Velas_Rojas = Σ(Volumen donde Close < Open)

Promedio_Vol_Verde = Volumen_Velas_Verdes / cantidad_velas_verdes
Promedio_Vol_Rojo = Volumen_Velas_Rojas / cantidad_velas_rojas

Ratio_Presión = Promedio_Vol_Verde / Promedio_Vol_Rojo
```

**Ejemplo con Cálculo Real:**

**Últimos 20 períodos:**
```
Período  Open     Close    Volumen   Color   Tipo
1        $43,380  $43,420  12,500    Verde   Compra
2        $43,420  $43,400  8,200     Roja    Venta
3        $43,400  $43,450  15,300    Verde   Compra
4        $43,450  $43,430  9,100     Roja    Venta
5        $43,430  $43,480  18,700    Verde   Compra
6        $43,480  $43,460  7,500     Roja    Venta
7        $43,460  $43,500  16,200    Verde   Compra
8        $43,500  $43,480  8,900     Roja    Venta
9        $43,480  $43,520  14,100    Verde   Compra
10       $43,520  $43,510  6,800     Roja    Venta
11       $43,510  $43,540  17,500    Verde   Compra
12       $43,540  $43,520  8,300     Roja    Venta
13       $43,520  $43,550  19,200    Verde   Compra
14       $43,550  $43,530  7,900     Roja    Venta
15       $43,530  $43,560  16,800    Verde   Compra
16       $43,560  $43,540  8,600     Roja    Venta
17       $43,540  $43,570  18,400    Verde   Compra
18       $43,570  $43,550  7,200     Roja    Venta
19       $43,550  $43,580  17,900    Verde   Compra
20       $43,580  $43,560  8,100     Roja    Venta
```

**Paso 1:** Separar y sumar volúmenes
```
Velas Verdes (10): 
12,500 + 15,300 + 18,700 + 16,200 + 14,100 + 
17,500 + 19,200 + 16,800 + 18,400 + 17,900
= 166,600 contratos

Velas Rojas (10):
8,200 + 9,100 + 7,500 + 8,900 + 6,800 + 
8,300 + 7,900 + 8,600 + 7,200 + 8,100
= 80,600 contratos
```

**Paso 2:** Calcular promedios
```
Promedio_Vol_Verde = 166,600 / 10 = 16,660 contratos
Promedio_Vol_Rojo = 80,600 / 10 = 8,060 contratos
```

**Paso 3:** Calcular ratio de presión
```
Ratio_Presión = 16,660 / 8,060
Ratio_Presión = 2.07
```

**Resultado:**
```
Volumen promedio velas verdes: 16,660
Volumen promedio velas rojas:   8,060
Ratio de presión: 2.07

🔍 Interpretación:
   Volumen comprador es 2.07× mayor que vendedor
   Presión compradora dominante (ratio > 1.1)
   Significado: Más dinero entrando que saliendo
   Voto: COMPRA 📈
```

**Reglas de Decisión:**
```
Ratio > 1.1:   Presión COMPRADORA → COMPRA
0.9 ≤ Ratio ≤ 1.1:   Volumen EQUILIBRADO → ESPERAR
Ratio < 0.9:   Presión VENDEDORA → VENTA
```

### 🗳️ VOTACIÓN FINAL DEL PANEL:

```
┌─────────────────────────────────────┐
│     RESULTADOS DE LA VOTACIÓN       │
├─────────────────────────────────────┤
│ 📈 COMPRA:    7 expertos            │
│ 📉 VENTA:     1 experto             │
│ ⏸  ESPERAR:   1 experto             │
├─────────────────────────────────────┤
│ 🎯 VEREDICTO: ALCISTA               │
│ 💪 CONFIANZA: 78% (7/9)             │
└─────────────────────────────────────┘
```

**Interpretación:**  
7 de 9 expertos dicen COMPRA → Alta confianza en señal alcista

---

## 🤖 PASO 4: Análisis de Inteligencia Artificial

**¿Qué hace?**  
Un "cerebro artificial" analiza TODA la información anterior y agrega su propia opinión basada en patrones que ha aprendido.

### ¿Cómo funciona la IA?

La IA (llamada "Ollama/Mistral") es como un trader experto con **años de experiencia** que puede ver patrones que los humanos no detectan fácilmente.

### Ejemplo de análisis de la IA:

**Información que recibe:**
```
📊 Contexto para IA:
   
   1. Regresión (Paso 2): ALCISTA 78%
   2. Panel Técnico (Paso 3): ALCISTA 78%
   3. RSI: 32 (sobreventa)
   4. MACD: Cruce alcista
   5. Tipo de activo: Boom 1000 (solo permite compras)
   6. Predicción anterior: ✅ ACERTADA (+5% confianza)
```

**Pregunta al cerebro IA:**  
"¿Qué recomiendas hacer con esta información?"

**Respuesta de la IA:**
```
🤖 ANÁLISIS DE INTELIGENCIA ARTIFICIAL:
   
   Señal: COMPRA 📈
   Confianza: 85% (base: 80% + 5% por predicción anterior acertada)
   
   Razón:
   "Confluencia técnica fuerte:
    • Tendencia macro alcista confirmada
    • Panel de expertos con mayoría compradora (78%)
    • RSI en sobreventa sugiere rebote inminente
    • MACD muestra momentum alcista
    • Tipo de activo (Boom) favorece compras
    • Historial reciente de predicciones exitosas"
```

### ¿Por qué la IA es importante?

La IA puede detectar **combinaciones** de factores:

**Ejemplo:**  
Un humano puede ver: "RSI está bajo"  
La IA ve: "RSI bajo + MACD cruzando + tendencia alcista + predicción anterior acertada = **95% de probabilidad** de subida"

---

## 🎯 PASO 5: Veredicto Final Consolidado

**¿Qué hace?**  
Combina TODOS los análisis anteriores y toma la decisión final.

### Sistema de Validación Cruzada

El bot usa **3 reglas de oro**:

#### Regla 1: Oposición Directa = BLOQUEO ❌

```
SI Regresión dice: ALCISTA
PERO IA dice: VENTA
→ DECISIÓN: ESPERAR

Razón: Señal contradictoria, muy riesgoso
```

#### Regla 2: Alta Confianza + Alineación = EJECUTAR ✅

```
SI IA tiene confianza ≥ 70%
Y ambos (IA y Regresión) apuntan en la MISMA dirección
→ DECISIÓN: EJECUTAR señal
```

#### Regla 3: Consenso IA + Panel = EJECUTAR ✅

```
SI IA dice: COMPRA
Y Panel dice: ALCISTA
→ DECISIÓN: COMPRA
```

### Ejemplo Completo de Decisión:

**Datos de entrada:**
```
PASO 2 (Regresión): ALCISTA (78%)
PASO 3 (Panel): ALCISTA (78%)
PASO 4 (IA): COMPRA (85%)
```

**Aplicando las reglas:**
```
✓ Regla 1: No hay oposición (todos alcistas)
✓ Regla 2: IA tiene 85% (≥70%) + alineados ✓
✓ Regla 3: IA (COMPRA) = Panel (ALCISTA) ✓
```

**Decisión:**
```
═══════════════════════════════════════════
         VEREDICTO FINAL
═══════════════════════════════════════════
🎯 ACCIÓN: COMPRA 📈
💪 CONFIANZA FINAL: 85%
📝 RAZÓN: "Alta confianza IA (85%) alineada 
          con tendencia macro alcista"
═══════════════════════════════════════════
```

### Validación Especial por Tipo de Activo

El bot hace una **última verificación** de seguridad:

```
¿El activo es "Boom 1000"? SÍ
¿La señal es COMPRA? SÍ
→ ✅ COMPATIBLE (Boom solo acepta compras)
```

Si hubiera sido al revés:
```
¿El activo es "Boom 1000"? SÍ
¿La señal es VENTA? SÍ
→ ❌ BLOQUEADO (Boom NO puede vender)
→ Cambiar a: ESPERAR
```

---

## 🔮 PASO 6: Pronóstico Futuro (Sistema de Aprendizaje)

**¿Qué hace?**  
Después de decidir qué hacer AHORA, el bot hace una **predicción** de qué pasará en los próximos 15 minutos.

### ¿Por qué es importante?

Imagina que juegas a predecir el clima:
- Si siempre aciertas, confías más en tu método
- Si siempre fallas, cambias tu estrategia

El bot hace lo mismo con el trading.

### Ejemplo de Predicción:

**Después de analizar, el bot predice:**

```
🎯 PRONÓSTICO PARA LOS PRÓXIMOS 15 MINUTOS:
   
   📊 Predicción: "Spike alcista esperado"
   🎲 Probabilidad: 65%
   💰 Precio objetivo: $43,650
   ⏰ Timeframe: 15 minutos (3-5 velas de 5 min)
   📝 Rationale: "RSI en sobreventa con MACD 
                 cruzando al alza sugiere movimiento
                 alcista inminente"
```

**El bot guarda esto en su "memoria"** para verificarlo en el próximo análisis.

### Ciclo de Aprendizaje Continuo:

```
Análisis #1 (10:00 AM):
├─ Hace predicción: "Subirá a $43,650"
└─ Guarda en base de datos

↓ [Pasan 15 minutos]

Análisis #2 (10:15 AM):
├─ Verifica predicción anterior
├─ Precio real: $43,670
├─ Predicho: $43,650
├─ Diferencia: $20 (casi exacto!)
├─ ✅ ACERTADA
└─ Ajusta confianza: +5%

↓ [Hace nueva predicción]

Análisis #2 continúa:
└─ Hace predicción: "Subirá a $43,800"
    (Ahora con 5% más de confianza)
```

### En la Interfaz Visual:

Verás un indicador que cambia de color:

**Primera vez del día:**
```
┌────────────────────────────────────┐
│ 🔮 Predicción Anterior: Pendiente │
│     (Fondo gris)                   │
└────────────────────────────────────┘
```

**Después de acertar:**
```
┌────────────────────────────────────┐
│ 🔮 Predicción Anterior:            │
│    ✅ ACERTADA (+5%)               │
│     (Fondo verde - Bot en racha)  │
└────────────────────────────────────┘
```

**Después de fallar:**
```
┌────────────────────────────────────┐
│ 🔮 Predicción Anterior:            │
│    ❌ FALLIDA (-5%)                │
│     (Fondo rojo - Bot ajustando)   │
└────────────────────────────────────┘
```

---

## 📊 Ejemplo Completo: Del Inicio al Fin

Vamos a seguir un análisis completo con números reales:

### ⏰ Momento: 10:00 AM - Análisis de "Boom 1000 Index"

#### **PASO 0: Verificación**
```
🔍 Buscando predicción anterior...
✅ Encontrada (de ayer a las 10:00 AM)
   Predicho: $43,500
   Real ahora: $43,520
   📊 Diferencia: $20 (dentro de tolerancia)
   ✅ ACERTADA → +5% confianza
```

#### **PASO 1: Identificación**
```
📋 Activo: Boom 1000 Index
   Tipo: Índice Sintético de Deriv
   Característica: Solo permite COMPRAS
   Precio actual: $43,450
```

#### **PASO 2: Regresión Lineal (30 días)**
```
📈 Descargando últimos 30 días...
   Día 1:  $40,000
   Día 30: $43,450
   
   Tendencia: ALCISTA ⬆️ (+8.6% en 30 días)
   Confianza R²: 78%
   Recomendación: COMPRA
```

#### **PASO 3: Panel de Expertos**
```
🗳️ Votación de 9 expertos:

1. RSI (32):          COMPRA 📈 (Sobreventa)
2. EMA Cross:         COMPRA 📈 (Alineadas)
3. MACD (+25 > +15):  COMPRA 📈 (Momento alcista)
4. Bollinger:         COMPRA 📈 (Banda inferior)
5. Heikin Ashi:       COMPRA 📈 (5 velas verdes)
6. Estocástico (18):  COMPRA 📈 (Sobreventa)
7. Soporte/Resist:    COMPRA 📈 (Cerca soporte)
8. Volatilidad:       COMPRA 📈 (Alta vol + precio > SMA)
9. Volumen:           ESPERAR ⏸ (Volumen neutro)

Resultados: 8 COMPRA, 0 VENTA, 1 ESPERAR
Veredicto: ALCISTA
Confianza Matemática: 89% (8/9)
```

#### **PASO 4: Inteligencia Artificial**
```
🤖 Procesando con Ollama (modelo Mistral)...

Señal IA: COMPRA 📈
Confianza base: 80%
Ajuste por predicción: +5%
Confianza final: 85%

Razonamiento:
"Confluencia técnica excepcional. Todos los 
 indicadores apuntan alcista. RSI en sobreventa 
 combinado con MACD alcista y tendencia macro 
 positiva sugieren alta probabilidad de 
 movimiento ascendente. Además, el activo Boom 
 1000 favorece movimientos alcistas naturalmente."
```

#### **PASO 5: Veredicto Final**
```
═══════════════════════════════════════════
Consolidando información:

✓ Regresión: ALCISTA (78%)
✓ Panel: ALCISTA (89%)
✓ IA: COMPRA (85%)

Validando reglas:
✓ No hay contradicción
✓ Confianza IA > 70%
✓ IA y Regresión alineados
✓ Tipo de activo compatible (Boom acepta COMPRA)

═══════════════════════════════════════════
🎯 DECISIÓN FINAL: COMPRA 📈
💪 CONFIANZA: 85%
📝 RAZÓN: "Alta confianza IA alineada con 
          tendencia macro y panel técnico"
═══════════════════════════════════════════
```

#### **PASO 6: Pronóstico Futuro**
```
🔮 Generando predicción para próximos 15 min...

Predicción: "Spike alcista esperado"
Probabilidad: 65%
Precio objetivo: $43,650 (de $43,450 actual)
Esperado aumento: $200 (+0.46%)
Timeframe: 15 minutos

💾 Guardado en base de datos para verificación
```

---

## 🎨 ¿Cómo se ve todo esto en la Pantalla?

### En la Card del Símbolo verías:

```
┌────────────────────────────────────────────┐
│  Boom 1000 Index              🟢 [LED]    │
├────────────────────────────────────────────┤
│  Precio: $43,450.00                        │
│  Última señal: 📈 COMPRA                   │
│  Confianza: 85%                            │
│                                            │
│  Panel Expertos: ALCISTA (89%)            │
│  Regresión Lineal: ALCISTA (78%)          │
│                                            │
│ ┌────────────────────────────────────────┐ │
│ │ 🔮 Predicción Anterior:                │ │
│ │    ✅ ACERTADA (+5%)                   │ │
│ └────────────────────────────────────────┘ │
│     (Fondo verde)                          │
│                                            │
│  💭 Alta confianza IA alineada con        │
│     tendencia macro                        │
│                                            │
│  [📊 Ver Detalles]                        │
│  ▶ Iniciar  |  ⏹ Detener                 │
└────────────────────────────────────────────┘
```

### Al hacer click en "📊 Ver Detalles":

Se abre una ventana completa mostrando:
- Los 6 pasos con todos los números
- Votación de cada experto
- Razonamiento de la IA
- Predicción actual
- Historial de predicciones anteriores

---

## 💡 Conceptos Clave Explicados Simplemente

### 1. ¿Qué es "Confianza"?

**Analogía del Clima:**
- Pronóstico de 90% de lluvia = Muy confiable (lleva paraguas)
- Pronóstico de 50% de lluvia = Poco confiable (quizás llueva, quizás no)

En el bot:
- **85% confianza = Muy confiable** → El bot ejecuta la operación
- **50% confianza = Poco confiable** → El bot prefiere ESPERAR

### 2. ¿Qué significa "ALCISTA" y "BAJISTA"?

**Alcista** 📈 = El precio tiende a SUBIR  
→ Recomendación: COMPRAR ahora, vender después más caro

**Bajista** 📉 = El precio tiende a BAJAR  
→ Recomendación: VENDER ahora, comprar después más barato

**Neutral** ⏸ = El precio no tiene dirección clara  
→ Recomendación: ESPERAR a señal más clara

### 3. ¿Qué es "Sobreventa" y "Sobrecompra"?

**Sobreventa:**  
Imagina un resorte muy comprimido. Cuanto más lo comprimes, más fuerte rebotará hacia arriba.  
→ Precio bajó mucho = Probable rebote al alza

**Sobrecompra:**  
Imagina un resorte muy estirado. Eventualmente se contraerá.  
→ Precio subió mucho = Probable corrección a la baja

### 4. ¿Qué son las "Velas" del gráfico?

Cada vela representa 5 minutos de movimiento:

```
🕐 10:00 AM - 10:05 AM = 1 vela

Si el precio SUBIÓ en esos 5 min: 🟢 Vela verde
Si el precio BAJÓ en esos 5 min: 🔴 Vela roja
```

5 velas verdes seguidas (🟢🟢🟢🟢🟢) = Tendencia alcista fuerte

---

## ⚙️ Configuraciones que Puedes Ajustar

### 1. Umbral de Confianza Mínima

**¿Qué es?**  
El nivel mínimo de confianza para que el bot ejecute una operación.

**Ejemplo:**
```
Umbral = 70%

Si IA dice COMPRA con 85% → ✅ EJECUTA
Si IA dice COMPRA con 60% → ❌ ESPERA (no alcanza umbral)
```

**Recomendación:**
- Conservador: 75-80% (menos operaciones, más seguras)
- Moderado: 70% (balance)
- Agresivo: 60-65% (más operaciones, más riesgo)

### 2. Tamaño del Lote

**¿Qué es?**  
Cuánto dinero arriesgas en cada operación.

**Ejemplo:**
```
Lote 0.35 = $35 por cada punto que se mueva el precio

Si compras a $43,450 y vende a $43,550:
Ganancia = 100 puntos × $35/punto = $3,500
```

**Recomendación:**
- Principiante: 0.10 - 0.20 (bajo riesgo)
- Intermedio: 0.35 - 0.50 (moderado)
- Avanzado: 0.50+ (alto riesgo, alto retorno)

### 3. Stop Loss y Take Profit

**Stop Loss (SL):**  
Cuánto estás dispuesto a PERDER antes de cerrar la operación.

**Take Profit (TP):**  
Cuánto quieres GANAR antes de cerrar automáticamente.

**Ejemplo:**
```
Compras a: $43,450
SL: 500 pips → Cierra si baja a $43,400 (pérdida $50)
TP: 1000 pips → Cierra si sube a $43,550 (ganancia $100)

Ratio 1:2 = Arriesgas $50 para ganar $100
```

---

## 🎓 Preguntas Frecuentes (No Técnicas)

### ❓ ¿El bot siempre gana?

**No.** Ningún sistema es perfecto. Pero:
- Busca situaciones de alta probabilidad
- Aprende de sus errores (sistema de predicción)
- Sigue reglas científicas, no emociones

**Estadísticas típicas:**
- 60-70% de operaciones exitosas
- 30-40% de pérdidas (normales y esperadas)

### ❓ ¿Cuánto tiempo tarda en analizar?

Cada análisis completo (6 pasos) toma aproximadamente:
- **20-30 segundos** en total
  - Paso 1: Instantáneo
  - Paso 2: 5 seg (descarga 30 días)
  - Paso 3: 10 seg (9 indicadores)
  - Paso 4: 5-10 seg (IA piensa)
  - Paso 5: Instantáneo
  - Paso 6: 5 seg (predicción IA)

### ❓ ¿Puedo analizar varios activos al mismo tiempo?

**Sí.** Cada activo tiene su propia "card" y se analiza independientemente.

Puedes tener:
- **Boom 1000** analizando cada 2 minutos
- **Crash 500** analizando cada 3 minutos
- **Volatility 75** analizando cada 2 minutos

Todos en paralelo.

### ❓ ¿Qué pasa si Ollama (IA) no funciona?

El bot sigue trabajando pero con capacidades limitadas:
- Pasos 1, 2, 3, 5 funcionan normal
- Paso 4 (IA) se salta o usa valores conservadores
- Paso 6 (Predicción) usa predicción simple sin IA

**Confianza baja** porque falta la "opinión experta" de la IA.

### ❓ ¿Cómo sé si todo funciona correctamente?

Verifica estos indicadores:

```
✅ LED verde en la card = Analizando activamente
✅ Precio se actualiza = Conexión MT5 OK
✅ Logs muestran "PASO 1", "PASO 2"... = Funcionando
✅ Predicción muestra estado (✅/❌/⏳) = Sistema IA OK
```

Si ves:
```
❌ LED rojo = Error (doble click para ver detalles)
⚠️  LED naranja = Pausado (temporal)
⚪ LED gris = Detenido (normal)
```

---

## 📚 Glosario de Términos

| Término | Significado Simple |
|---------|-------------------|
| **Índice Sintético** | Activo financiero creado artificialmente con reglas específicas |
| **Boom** | Índice que tiene "saltos" repentinos hacia ARRIBA |
| **Crash** | Índice que tiene "caídas" repentinas hacia ABAJO |
| **RSI** | Indicador de si está "cansado" de subir/bajar |
| **MACD** | Indicador de impulso (aceleración) |
| **EMA** | Promedio de precios recientes |
| **Bollinger** | "Orillas" del movimiento normal del precio |
| **Sobreventa** | Precio bajó demasiado, probable rebote |
| **Sobrecompra** | Precio subió demasiado, probable corrección |
| **Pip** | Punto: unidad mínima de movimiento del precio |
| **Lote** | Cantidad de contratos (tamaño de la operación) |
| **SL (Stop Loss)** | Pérdida máxima aceptable |
| **TP (Take Profit)** | Ganancia objetivo |
| **Trailing Stop** | SL que se mueve automáticamente con el precio |

---

## 🎬 Conclusión: El Bot en Una Frase

> **"El bot es como tener 9 expertos financieros + un cerebro de IA trabajando 24/7, analizando el mercado científicamente, aprendiendo de sus aciertos y errores, y ejecutando solo cuando hay alta probabilidad de éxito."**

---

**Manual creado**: 2026-01-02  
**Versión**: 1.0 - Para usuarios no técnicos  
**Bot versión**: 2.0 con sistema de predicción IA
