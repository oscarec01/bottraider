"""
Script de prueba rápida para verificar la respuesta de Cloudflare Workers AI
"""

import requests
import json

# Credenciales del usuario
ACCOUNT_ID = "8f296c9441738764c450954bfbcbc543"
API_TOKEN = "gNP7mxp3g1glmJq8-Qi59fYm6rnzeDdCyJyHTp4N"
MODEL = "@cf/mistral/mistral-7b-instruct-v0.1"

url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{MODEL}"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "messages": [
        {
            "role": "user",
            "content": "Responde SOLO con este JSON: {\"señal\": \"COMPRA\", \"confianza\": 75, \"razon\": \"Test exitoso\"}"
        }
    ]
}

print("🔍 Probando Cloudflare Workers AI...")
print(f"URL: {url}")
print(f"Model: {MODEL}")
print("="*70)

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"\n✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📦 Estructura de respuesta completa:")
        print(json.dumps(data, indent=2))
        
        print(f"\n📊 Intentando extraer respuesta...")
        
        # Verificar diferentes estructuras
        result_data = data.get("result", {})
        print(f"\nTipo de 'result': {type(result_data)}")
        print(f"Keys en 'result': {result_data.keys() if isinstance(result_data, dict) else 'N/A'}")
        
        # Intentar extraer
        if isinstance(result_data, dict):
            response_text = result_data.get("response", "")
            print(f"\n✅ Respuesta extraída: {response_text}")
        elif isinstance(result_data, str):
            print(f"\n✅ Result es string directamente: {result_data}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ Excepción: {e}")
    import traceback
    traceback.print_exc()
