"""
AI Provider Abstraction Layer for MrLiou AI SuperComputer
支持多種 AI 服務提供商的統一介面
"""

import os
import json
import urllib.request
import urllib.error
import re
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional


# -------------------------
# Utility Functions
# -------------------------
def _sanitize_error_message(error_msg: str) -> str:
    """
    Sanitize error messages to prevent API key leakage.
    移除錯誤訊息中的敏感資訊，防止 API 密鑰洩漏
    """
    # Remove common API key patterns
    patterns = [
        (r'Bearer\s+[A-Za-z0-9\-_]+', 'Bearer [REDACTED]'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9\-_]+', 'api_key=[REDACTED]'),
        (r'sk-[A-Za-z0-9]{20,}', 'sk-[REDACTED]'),  # OpenAI keys
        (r'x-api-key:\s*[A-Za-z0-9\-_]+', 'x-api-key: [REDACTED]'),
    ]
    
    sanitized = error_msg
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized


# -------------------------
# Base Provider Interface
# -------------------------
class BaseAIProvider(ABC):
    """Base class for all AI providers / 所有 AI 提供商的基礎類別"""
    
    def __init__(self, config: dict):
        self.config = config
        self.model = config.get("model", "")
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "")
    
    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Synchronous completion / 同步完成"""
        pass
    
    @abstractmethod
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Streaming completion / 串流完成"""
        pass
    
    def get_info(self) -> dict:
        """Return provider info / 返回提供商資訊"""
        return {
            "provider": self.__class__.__name__,
            "model": self.model,
            "available": self.is_available()
        }
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available / 檢查提供商是否可用"""
        pass


# -------------------------
# OpenAI Provider
# -------------------------
class OpenAIProvider(BaseAIProvider):
    """OpenAI API Provider (GPT-4, GPT-3.5, etc.) / OpenAI API 提供商"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.7)
    
    def is_available(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key and self.api_key.strip())
    
    def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Synchronous completion using OpenAI API"""
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available: missing API key")
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())
                
                return {
                    "provider": "openai",
                    "model": self.model,
                    "content": result["choices"][0]["message"]["content"],
                    "usage": result.get("usage", {}),
                    "finish_reason": result["choices"][0].get("finish_reason"),
                    "raw": result
                }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            sanitized_error = _sanitize_error_message(error_body)
            raise RuntimeError(f"OpenAI API error {e.code}: {sanitized_error}")
        except Exception as e:
            sanitized_error = _sanitize_error_message(str(e))
            raise RuntimeError(f"OpenAI API request failed: {sanitized_error}")
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Streaming completion using OpenAI API"""
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available: missing API key")
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                for line in response:
                    line = line.decode().strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            # Skip malformed JSON chunks and continue streaming
                            continue
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            sanitized_error = _sanitize_error_message(error_body)
            raise RuntimeError(f"OpenAI API error {e.code}: {sanitized_error}")
        except Exception as e:
            sanitized_error = _sanitize_error_message(str(e))
            raise RuntimeError(f"OpenAI streaming failed: {sanitized_error}")


# -------------------------
# Claude Provider
# -------------------------
class ClaudeProvider(BaseAIProvider):
    """Anthropic Claude API Provider / Anthropic Claude API 提供商"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.7)
    
    def is_available(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key and self.api_key.strip())
    
    def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Synchronous completion using Claude API"""
        if not self.is_available():
            raise RuntimeError("Claude provider not available: missing API key")
        
        url = f"{self.base_url}/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())
                
                return {
                    "provider": "claude",
                    "model": self.model,
                    "content": result["content"][0]["text"],
                    "usage": result.get("usage", {}),
                    "stop_reason": result.get("stop_reason"),
                    "raw": result
                }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            sanitized_error = _sanitize_error_message(error_body)
            raise RuntimeError(f"Claude API error {e.code}: {sanitized_error}")
        except Exception as e:
            sanitized_error = _sanitize_error_message(str(e))
            raise RuntimeError(f"Claude API request failed: {sanitized_error}")
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Streaming completion using Claude API"""
        if not self.is_available():
            raise RuntimeError("Claude provider not available: missing API key")
        
        url = f"{self.base_url}/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                for line in response:
                    line = line.decode().strip()
                    if not line or not line.startswith("data: "):
                        continue
                    
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data_str)
                        if chunk.get("type") == "content_block_delta":
                            delta = chunk.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")
                    except json.JSONDecodeError:
                        continue
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            sanitized_error = _sanitize_error_message(error_body)
            raise RuntimeError(f"Claude API error {e.code}: {sanitized_error}")
        except Exception as e:
            sanitized_error = _sanitize_error_message(str(e))
            raise RuntimeError(f"Claude streaming failed: {sanitized_error}")


# -------------------------
# Gemini Provider
# -------------------------
class GeminiProvider(BaseAIProvider):
    """Google Gemini API Provider / Google Gemini API 提供商"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.temperature = config.get("temperature", 0.7)
    
    def is_available(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key and self.api_key.strip())
    
    def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Synchronous completion using Gemini API"""
        if not self.is_available():
            raise RuntimeError("Gemini provider not available: missing API key")
        
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        temperature = kwargs.get("temperature", self.temperature)
        
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())
                
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                
                return {
                    "provider": "gemini",
                    "model": self.model,
                    "content": content,
                    "usage": result.get("usageMetadata", {}),
                    "finish_reason": result["candidates"][0].get("finishReason"),
                    "raw": result
                }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            sanitized_error = _sanitize_error_message(error_body)
            raise RuntimeError(f"Gemini API error {e.code}: {sanitized_error}")
        except Exception as e:
            sanitized_error = _sanitize_error_message(str(e))
            raise RuntimeError(f"Gemini API request failed: {sanitized_error}")
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Streaming completion using Gemini API"""
        if not self.is_available():
            raise RuntimeError("Gemini provider not available: missing API key")
        
        url = f"{self.base_url}/models/{self.model}:streamGenerateContent?key={self.api_key}&alt=sse"
        headers = {
            "Content-Type": "application/json"
        }
        
        temperature = kwargs.get("temperature", self.temperature)
        
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                for line in response:
                    line = line.decode().strip()
                    if not line or not line.startswith("data: "):
                        continue
                    
                    try:
                        chunk = json.loads(line[6:])
                        if "candidates" in chunk and chunk["candidates"]:
                            parts = chunk["candidates"][0].get("content", {}).get("parts", [])
                            for part in parts:
                                if "text" in part:
                                    yield part["text"]
                    except json.JSONDecodeError:
                        continue
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            sanitized_error = _sanitize_error_message(error_body)
            raise RuntimeError(f"Gemini API error {e.code}: {sanitized_error}")
        except Exception as e:
            sanitized_error = _sanitize_error_message(str(e))
            raise RuntimeError(f"Gemini streaming failed: {sanitized_error}")


# -------------------------
# Ollama Provider
# -------------------------
class OllamaProvider(BaseAIProvider):
    """Ollama Local Model Provider / Ollama 本地模型提供商"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.temperature = config.get("temperature", 0.7)
    
    def is_available(self) -> bool:
        """Check if Ollama server is reachable"""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except (urllib.error.URLError, TimeoutError, OSError):
            return False
    
    def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Synchronous completion using Ollama API"""
        if not self.is_available():
            raise RuntimeError("Ollama provider not available: server not reachable")
        
        url = f"{self.base_url}/api/generate"
        headers = {
            "Content-Type": "application/json"
        }
        
        temperature = kwargs.get("temperature", self.temperature)
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode())
                
                return {
                    "provider": "ollama",
                    "model": self.model,
                    "content": result.get("response", ""),
                    "usage": {
                        "eval_count": result.get("eval_count", 0),
                        "prompt_eval_count": result.get("prompt_eval_count", 0)
                    },
                    "raw": result
                }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            sanitized_error = _sanitize_error_message(error_body)
            raise RuntimeError(f"Ollama API error {e.code}: {sanitized_error}")
        except Exception as e:
            sanitized_error = _sanitize_error_message(str(e))
            raise RuntimeError(f"Ollama API request failed: {sanitized_error}")
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Streaming completion using Ollama API"""
        if not self.is_available():
            raise RuntimeError("Ollama provider not available: server not reachable")
        
        url = f"{self.base_url}/api/generate"
        headers = {
            "Content-Type": "application/json"
        }
        
        temperature = kwargs.get("temperature", self.temperature)
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": True
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                for line in response:
                    line = line.decode().strip()
                    if not line:
                        continue
                    
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                    except json.JSONDecodeError:
                        continue
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            sanitized_error = _sanitize_error_message(error_body)
            raise RuntimeError(f"Ollama API error {e.code}: {sanitized_error}")
        except Exception as e:
            sanitized_error = _sanitize_error_message(str(e))
            raise RuntimeError(f"Ollama streaming failed: {sanitized_error}")


# -------------------------
# Azure OpenAI Provider
# -------------------------
class AzureOpenAIProvider(BaseAIProvider):
    """Azure OpenAI Service Provider / Azure OpenAI 服務提供商"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.endpoint = config.get("endpoint", "")
        self.deployment_name = config.get("deployment_name", "")
        self.api_version = config.get("api_version", "2024-02-15-preview")
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.7)
    
    def is_available(self) -> bool:
        """Check if API key and endpoint are configured"""
        return bool(self.api_key and self.endpoint and self.deployment_name)
    
    def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Synchronous completion using Azure OpenAI API"""
        if not self.is_available():
            raise RuntimeError("Azure OpenAI provider not available: missing configuration")
        
        url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())
                
                return {
                    "provider": "azure",
                    "model": self.deployment_name,
                    "content": result["choices"][0]["message"]["content"],
                    "usage": result.get("usage", {}),
                    "finish_reason": result["choices"][0].get("finish_reason"),
                    "raw": result
                }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            sanitized_error = _sanitize_error_message(error_body)
            raise RuntimeError(f"Azure OpenAI API error {e.code}: {sanitized_error}")
        except Exception as e:
            sanitized_error = _sanitize_error_message(str(e))
            raise RuntimeError(f"Azure OpenAI API request failed: {sanitized_error}")
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Streaming completion using Azure OpenAI API"""
        if not self.is_available():
            raise RuntimeError("Azure OpenAI provider not available: missing configuration")
        
        url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                for line in response:
                    line = line.decode().strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            # Skip malformed JSON chunks and continue streaming
                            continue
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            sanitized_error = _sanitize_error_message(error_body)
            raise RuntimeError(f"Azure OpenAI API error {e.code}: {sanitized_error}")
        except Exception as e:
            sanitized_error = _sanitize_error_message(str(e))
            raise RuntimeError(f"Azure OpenAI streaming failed: {sanitized_error}")


# -------------------------
# Provider Manager
# -------------------------
class AIProviderManager:
    """Manager for multiple AI providers / 多個 AI 提供商的管理器"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.providers = {}
        self._init_providers()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file with env variable substitution"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Substitute environment variables
        config = self._substitute_env_vars(config)
        return config
    
    def _substitute_env_vars(self, obj):
        """Recursively substitute ${ENV_VAR} patterns with environment variables"""
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Replace ${VAR_NAME} with environment variable
            import re
            def replacer(match):
                var_name = match.group(1)
                return os.environ.get(var_name, "")
            return re.sub(r'\$\{([^}]+)\}', replacer, obj)
        else:
            return obj
    
    def _init_providers(self):
        """Initialize all enabled providers"""
        provider_configs = self.config.get("providers", {})
        
        provider_classes = {
            "openai": OpenAIProvider,
            "claude": ClaudeProvider,
            "gemini": GeminiProvider,
            "ollama": OllamaProvider,
            "azure": AzureOpenAIProvider
        }
        
        for name, cfg in provider_configs.items():
            if cfg.get("enabled", False):
                provider_class = provider_classes.get(name)
                if provider_class:
                    try:
                        self.providers[name] = provider_class(cfg)
                    except Exception as e:
                        print(f"Warning: Failed to initialize {name} provider: {e}")
    
    def get_provider(self, name: Optional[str] = None) -> BaseAIProvider:
        """Get provider by name or return default"""
        if name is None:
            name = self.config.get("default_provider")
        
        provider = self.providers.get(name)
        if not provider:
            raise ValueError(f"Provider '{name}' not found or not enabled")
        
        return provider
    
    def list_providers(self) -> list:
        """List all available providers"""
        return [p.get_info() for p in self.providers.values()]
    
    def complete_with_fallback(self, prompt: str, provider_name: Optional[str] = None, **kwargs) -> dict:
        """
        Try primary provider, fallback to alternatives on failure.
        If provider_name is explicitly specified, no fallback is used (user choice is respected).
        """
        fallback_enabled = self.config.get("fallback_enabled", True)
        
        # Determine providers to try
        if provider_name:
            # Explicit provider specified: respect the choice, do not use fallbacks
            providers_to_try = [provider_name]
        else:
            # No explicit provider: use default and optional fallback chain
            providers_to_try = [self.config.get("default_provider")]
            
            # Add fallback providers if enabled
            if fallback_enabled:
                fallback_order = self.config.get("fallback_order", [])
                for fb in fallback_order:
                    if fb not in providers_to_try and fb in self.providers:
                        providers_to_try.append(fb)
        
        errors = []
        
        for prov_name in providers_to_try:
            try:
                provider = self.get_provider(prov_name)
                if not provider.is_available():
                    errors.append({
                        "provider": prov_name,
                        "error": "Provider not available"
                    })
                    continue
                
                result = provider.complete(prompt, **kwargs)
                result["fallback_used"] = prov_name != providers_to_try[0]
                result["attempts"] = len(errors) + 1
                return result
                
            except Exception as e:
                errors.append({
                    "provider": prov_name,
                    "error": str(e)
                })
        
        # All providers failed
        raise RuntimeError(f"All providers failed. Errors: {json.dumps(errors)}")
