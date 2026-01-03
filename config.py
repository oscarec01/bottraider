# Configuración de IA - AI Provider Selection
AI_PROVIDER = "ollama"  # Opciones: "ollama" o "cloudflare"

# Ollama Configuration (Local)
GEMINI_API_KEY = "TU_API_KEY" # Mantener por compatibilidad
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

# Cloudflare Workers AI Configuration
CLOUDFLARE_ACCOUNT_ID = "8f296c9441738764c450954bfbcbc543"
CLOUDFLARE_API_TOKEN = "gNP7mxp3g1glmJq8-Qi59fYm6rnzeDdCyJyHTp4N"
CLOUDFLARE_MODEL = "@cf/mistral/mistral-7b-instruct-v0.1"
CLOUDFLARE_API_BASE_URL = "https://api.cloudflare.com/client/v4"


# MAPEO DE SÍMBOLOS  (códigos cortos -> nombres completos de Deriv)
SYMBOL_MAPPING = {
    # Booms
    'B1000': 'Boom 1000 Index',
    'B500': 'Boom 500 Index',
    'B300': 'Boom 300 Index',
    'B600': 'Boom 600 Index',
    'B900': 'Boom 900 Index',
    # Crashes
    'C1000': 'Crash 1000 Index',
    'C500': 'Crash 500 Index',
    'C300': 'Crash 300 Index',
    'C600': 'Crash 600 Index',
    'C900': 'Crash 900 Index',
    # Volatility
    'V10': 'Volatility 10 Index',
    'V25': 'Volatility 25 Index',
    'V50': 'Volatility 50 Index',
    'V75': 'Volatility 75 Index',
    'V100': 'Volatility 100 Index',
    'J75': 'Jump 75 Index',
    # Step Indices
    'STEP_RISE_1200': 'Step Rise 1200 Index',
    'STEP_RISE_999': 'Step Rise 999 Index',
    'STEP_DROP_1200': 'Step Drop 1200 Index',
    'STEP_DROP_999': 'Step Drop 999 Index',
    # Metales
    'XAUUSD': 'XAUUSD',
    'GOLD': 'XAUUSD'
}

# CONFIGURACIÓN DE LOTES MÍNIMOS POR TIPO DE ACTIVO
LOT_SIZES = {
    # Booms y Crashes - Lote mínimo típico
    'Boom 1000 Index': 0.35,
    'Boom 500 Index': 0.35,
    'Boom 300 Index': 0.35,
    'Boom 600 Index': 0.35,
    'Boom 900 Index': 0.35,
    'Crash 1000 Index': 0.35,
    'Crash 500 Index': 0.35,
    'Crash 300 Index': 0.35,
    'Crash 600 Index': 0.35,
    'Crash 900 Index': 0.35,
    # Volatility Indices
    'Volatility 10 Index': 0.35,
    'Volatility 25 Index': 0.35,
    'Volatility 50 Index': 0.35,
    'Volatility 75 Index': 0.35,
    'Volatility 100 Index': 0.35,
    'Jump 75 Index': 0.35,
    # Step Indices
    'Step Rise 1200 Index': 0.35,
    'Step Rise 999 Index': 0.35,
    'Step Drop 1200 Index': 0.35,
    'Step Drop 999 Index': 0.35,
    # Metales - Lote diferente
    'XAUUSD': 0.01
}

# LISTA DE ACTIVOS PERMITIDOS
ACTIVOS_PERMITIDOS = [
    # Booms
    "Boom 1000 Index", "Boom 500 Index", "Boom 300 Index", "Boom 600 Index", "Boom 900 Index",
    # Crashes
    "Crash 1000 Index", "Crash 500 Index", "Crash 300 Index", "Crash 600 Index", "Crash 900 Index",
    # Volatility / Otros
    "Jump 75 Index", "Volatility 10 Index", "Volatility 100 Index", "Volatility 25 Index", 
    "Volatility 50 Index", "Volatility 75 Index", 
    "Step Drop 1200 Index", "Step Drop 999 Index", "Step Rise 1200 Index", "Step Rise 999 Index",
    # Metales
    "XAUUSD"
]

# CONFIGURACIÓN METATRADER 5 (Deriv Synthetic Account)
MT5_ACCOUNT = 29514809  # Tu cuenta de Deriv
MT5_PASSWORD = "Fuego.0921"
MT5_SERVER = "Deriv-Demo"  # O "Deriv-Server" para cuenta real

# PARÁMETROS DE TRADING (Índices Sintéticos)
SYMBOL = "Volatility 75 Index"  # Ej: "Boom 1000 Index", "Crash 500 Index"
LOT_SIZE = 0.001  # Ajustar según contrato del índice
STOP_LOSS_PIPS = 500  # En sintéticos se suele usar pips o puntos grandes
TAKE_PROFIT_PIPS = 1000

# FUNCIÓN AUXILIAR: Obtener nombre completo del símbolo
def get_symbol_name(short_code):
    """
    Convierte códigos cortos a nombres completos de Deriv.
    Ejemplos:
        'B1000' -> 'Boom 1000 Index'
        'V75' -> 'Volatility 75 Index'
        'XAUUSD' -> 'XAUUSD'
    Si el código no está en el mapeo, retorna el mismo valor.
    """
    return SYMBOL_MAPPING.get(short_code, short_code)
