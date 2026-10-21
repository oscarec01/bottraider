"""
Sistema de proveedores de IA para el Bot de Trading.
Permite usar múltiples proveedores (Ollama, Cloudflare Workers AI, etc.)
de forma transparente.
"""

import requests
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Norton/antivirus en Windows a menudo rompe la verificación SSL (CERTIFICATE_VERIFY_FAILED).
# Se intenta primero con verify=True; si falla SSL, reintenta sin verificar (configurable).
_SSL_VERIFY_FALLBACK = True


def _http_post(url: str, *, headers=None, json_body=None, timeout: int = 30, verify: bool = True):
    """POST con reintento si el antivirus rompe el store de certificados."""
    try:
        return requests.post(url, headers=headers, json=json_body, timeout=timeout, verify=verify)
    except requests.exceptions.SSLError as e:
        if verify and _SSL_VERIFY_FALLBACK:
            logger.warning(
                "SSL verify fallo (%s). Reintentando sin verificacion de certificado "
                "(tipico con antivirus HTTPS). Desactiva el escaneo SSL o instala el CA del antivirus.",
                e,
            )
            return requests.post(
                url, headers=headers, json=json_body, timeout=timeout, verify=False
            )
        raise


class AIProvider(ABC):
    """
    Clase base abstracta para proveedores de IA.
    Todos los proveedores deben implementar estos métodos.
    """
    
    @abstractmethod
    def query(self, prompt: str, timeout: int = 30, format_json: bool = False) -> str:
        """
        Envía un prompt al proveedor de IA y retorna la respuesta.
        
        Args:
            prompt: El texto del prompt
            timeout: Timeout en segundos
            format_json: Si True, solicita formato JSON en la respuesta
            
        Returns:
            La respuesta del modelo como string
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el proveedor está disponible y configurado correctamente.
        
        Returns:
            True si el proveedor está disponible, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Retorna el nombre del proveedor"""
        pass


class OllamaProvider(AIProvider):
    """
    Proveedor de IA usando Ollama local.
    """
    
    def __init__(self, url: str = "http://localhost:11434/api/generate", 
                 model: str = "mistral"):
        """
        Inicializa el proveedor Ollama.
        
        Args:
            url: URL del endpoint de Ollama
            model: Nombre del modelo a usar
        """
        self.url = url
        self.model = model
        logger.info(f"OllamaProvider inicializado con modelo: {model}")
    
    def query(self, prompt: str, timeout: int = 30, format_json: bool = False) -> str:
        """
        Consulta Ollama con el prompt dado.
        
        Args:
            prompt: El texto del prompt
            timeout: Timeout en segundos
            format_json: Si True, solicita formato JSON
            
        Returns:
            La respuesta del modelo
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            if format_json:
                payload["format"] = "json"
            
            response = _http_post(self.url, json_body=payload, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json().get("response", "").strip()
                logger.debug(f"Ollama response received (length: {len(result)})")
                return result
            else:
                logger.error(f"Ollama error: status {response.status_code}")
                return ""
                
        except requests.exceptions.Timeout:
            logger.warning(f"Ollama timeout after {timeout}s")
            return ""
        except Exception as e:
            logger.error(f"Error en query Ollama: {e}")
            return ""
    
    def is_available(self) -> bool:
        """
        Verifica si Ollama está disponible haciendo un ping.
        
        Returns:
            True si Ollama responde, False en caso contrario
        """
        try:
            # Intentar una consulta simple
            response = requests.get(
                self.url.replace("/api/generate", "/api/tags"),
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_name(self) -> str:
        return f"Ollama ({self.model})"


class CloudflareProvider(AIProvider):
    """
    Proveedor de IA usando Cloudflare Workers AI.
    """
    
    def __init__(self, account_id: str, api_token: str, 
                 model: str = "@cf/mistral/mistral-7b-instruct-v0.1"):
        """
        Inicializa el proveedor Cloudflare.
        
        Args:
            account_id: ID de la cuenta de Cloudflare
            api_token: Token de API de Cloudflare
            model: Nombre del modelo a usar
        """
        self.account_id = account_id
        self.api_token = api_token
        self.model = model
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/"
        logger.info(f"CloudflareProvider inicializado con modelo: {model}")
    
    def query(self, prompt: str, timeout: int = 30, format_json: bool = False) -> str:
        """
        Consulta Cloudflare Workers AI con el prompt dado.
        
        Args:
            prompt: El texto del prompt
            timeout: Timeout en segundos
            format_json: Si True, agrega instrucción para formato JSON
            
        Returns:
            La respuesta del modelo
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Agregar instrucción JSON si se solicita
            actual_prompt = prompt
            if format_json:
                actual_prompt = f"{prompt}\n\nRespond ONLY in valid JSON format."
            
            # Cloudflare usa formato de mensajes
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": actual_prompt
                    }
                ],
                "max_tokens": 512  # CRÍTICO: Permitir respuestas completas (default es muy bajo)
            }
            
            url = f"{self.base_url}{self.model}"
            response = _http_post(url, headers=headers, json_body=payload, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Cloudflare raw response: {json.dumps(data, indent=2)[:500]}")
                
                # Cloudflare retorna la respuesta en result.response (para modelos de chat)
                # La estructura es: {"result": {"response": "texto..."}}
                result_data = data.get("result", {})
                
                # Intentar obtener respuesta de diferentes posibles estructuras
                result = ""
                if isinstance(result_data, dict):
                    # Estructura 1: result.response
                    result = result_data.get("response", "")
                    
                    # Estructura 2: result.messages (array de mensajes)
                    if not result and "messages" in result_data:
                        messages = result_data.get("messages", [])
                        if messages and len(messages) > 0:
                            result = messages[-1].get("content", "")
                    
                    # Estructura 3: result directamente es string
                    if not result and isinstance(result_data, str):
                        result = result_data
                elif isinstance(result_data, str):
                    result = result_data
                
                result = result.strip()
                
                if result:
                    logger.info(f"✅ Cloudflare response received (length: {len(result)})")
                    logger.debug(f"Response preview: {result[:200]}...")
                    return result
                else:
                    logger.error(f"❌ Cloudflare response empty. Full data: {json.dumps(data, indent=2)}")
                    return ""
            else:
                logger.error(f"Cloudflare error: status {response.status_code}, response: {response.text}")
                return ""
                
        except requests.exceptions.Timeout:
            logger.warning(f"Cloudflare timeout after {timeout}s")
            return ""
        except Exception as e:
            logger.error(f"Error en query Cloudflare: {e}")
            return ""
    
    def is_available(self) -> bool:
        """
        Verifica si Cloudflare Workers AI está disponible.
        
        Returns:
            True si las credenciales son válidas, False en caso contrario
        """
        try:
            # Hacer una consulta de prueba simple
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {"role": "user", "content": "test"}
                ]
            }
            
            url = f"{self.base_url}{self.model}"
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            return response.status_code == 200
        except:
            return False
    
    def get_name(self) -> str:
        model_name = self.model.split('/')[-1] if '/' in self.model else self.model
        return f"Cloudflare ({model_name})"


class OpenRouterProvider(AIProvider):
    """
    Proveedor de IA usando OpenRouter (API compatible con OpenAI Chat Completions).
    Docs: https://openrouter.ai/api/v1/chat/completions
    """

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        base_url: str = "https://openrouter.ai/api/v1/chat/completions",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        logger.info(f"OpenRouterProvider inicializado con modelo: {model}")

    def query(self, prompt: str, timeout: int = 60, format_json: bool = False) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/oscarec01/bottraider",
                "X-Title": "BotTrader Deriv",
            }

            system = (
                "Eres un analista de trading. Responde SOLO JSON válido, sin markdown."
                if format_json
                else "Eres un analista de trading conciso."
            )
            user_content = prompt
            if format_json:
                user_content = f"{prompt}\n\nResponde ÚNICAMENTE JSON válido."

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.2,
                "max_tokens": 512,
            }

            response = _http_post(
                self.base_url, headers=headers, json_body=payload, timeout=timeout
            )

            if response.status_code != 200:
                logger.error(
                    f"OpenRouter error {response.status_code}: {response.text[:500]}"
                )
                return ""

            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                logger.error(f"OpenRouter sin choices: {json.dumps(data)[:400]}")
                return ""

            message = choices[0].get("message") or {}
            result = (message.get("content") or "").strip()
            if result:
                logger.info(f"OpenRouter OK ({len(result)} chars) model={self.model}")
            return result

        except requests.exceptions.Timeout:
            logger.warning(f"OpenRouter timeout after {timeout}s")
            return ""
        except Exception as e:
            logger.error(f"Error en query OpenRouter: {e}")
            return ""

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            # Ping ligero: listar modelos requiere auth; usamos un chat mínimo
            text = self.query('Responde exactamente: {"ok":true}', timeout=20, format_json=True)
            return bool(text)
        except Exception:
            return False

    def get_name(self) -> str:
        return f"OpenRouter ({self.model})"


def get_ai_provider(db_instance) -> AIProvider:
    """
    Factory function para obtener el proveedor de IA configurado.
    
    Args:
        db_instance: Instancia de Database para obtener configuración
        
    Returns:
        Una instancia del proveedor de IA configurado
    """
    provider_name = db_instance.get_setting('ai_provider', 'ollama')

    if provider_name == 'openrouter':
        api_key = db_instance.get_setting('openrouter_api_key', '')
        model = db_instance.get_setting('openrouter_model', 'openai/gpt-4o-mini')
        if not api_key:
            logger.warning("OpenRouter sin API key. Intentando Ollama.")
            provider_name = 'ollama'
        else:
            logger.info(f"Usando proveedor: OpenRouter ({model})")
            return OpenRouterProvider(api_key, model)
    
    if provider_name == 'cloudflare':
        account_id = db_instance.get_setting('cloudflare_account_id', '')
        api_token = db_instance.get_setting('cloudflare_api_token', '')
        model = db_instance.get_setting('cloudflare_model', '@cf/mistral/mistral-7b-instruct-v0.1')
        
        if not account_id or not api_token:
            logger.warning("Cloudflare configurado pero faltan credenciales. Usando Ollama por defecto.")
            provider_name = 'ollama'
        else:
            logger.info(f"Usando proveedor: Cloudflare Workers AI ({model})")
            return CloudflareProvider(account_id, api_token, model)
    
    # Por defecto usar Ollama
    url = db_instance.get_setting('ollama_url', 'http://localhost:11434/api/generate')
    model = db_instance.get_setting('ollama_model', 'mistral')
    logger.info(f"Usando proveedor: Ollama local ({model})")
    return OllamaProvider(url, model)
