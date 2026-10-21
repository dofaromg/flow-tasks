# origin_signature: MrLiouWord
# AI Provider Manager — Multi-provider orchestration (Ollama/OpenAI/Claude/Gemini)

import os, json
from ai_fusion_core import BaseAIProvider
ORIGIN = "MrLiouWord"

class OllamaProvider(BaseAIProvider):
    def __init__(self, config=None):
        super().__init__("ollama", config)
        self.base_url = (config or {}).get("base_url", "http://127.0.0.1:11434")
    def call(self, prompt, **kwargs):
        try:
            import urllib.request
            data = json.dumps({"model": kwargs.get("model", "llama3.2"), "prompt": prompt, "stream": False}).encode()
            req = urllib.request.Request(f"{self.base_url}/api/generate", data=data,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            return {"provider": "ollama", "response": result.get("response", ""), "origin_signature": ORIGIN}
        except Exception as e:
            return {"provider": "ollama", "error": str(e), "origin_signature": ORIGIN}

class OpenAIProvider(BaseAIProvider):
    def __init__(self, config=None):
        super().__init__("openai", config)
        self.api_key = (config or {}).get("api_key", os.environ.get("OPENAI_API_KEY", ""))
    def call(self, prompt, **kwargs):
        if not self.api_key:
            return {"provider": "openai", "error": "no api_key", "origin_signature": ORIGIN}
        try:
            import urllib.request
            data = json.dumps({"model": kwargs.get("model", "gpt-4o-mini"), "messages": [{"role": "user", "content": prompt}]}).encode()
            req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=data,
                                         headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            return {"provider": "openai", "response": result["choices"][0]["message"]["content"], "origin_signature": ORIGIN}
        except Exception as e:
            return {"provider": "openai", "error": str(e), "origin_signature": ORIGIN}

class ClaudeProvider(BaseAIProvider):
    def __init__(self, config=None):
        super().__init__("claude", config)
        self.api_key = (config or {}).get("api_key", os.environ.get("ANTHROPIC_API_KEY", ""))
    def call(self, prompt, **kwargs):
        if not self.api_key:
            return {"provider": "claude", "error": "no api_key", "origin_signature": ORIGIN}
        try:
            import urllib.request
            data = json.dumps({"model": "claude-sonnet-4-20250514", "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}).encode()
            req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
                                         headers={"Content-Type": "application/json", "x-api-key": self.api_key, "anthropic-version": "2023-06-01"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            return {"provider": "claude", "response": result["content"][0]["text"], "origin_signature": ORIGIN}
        except Exception as e:
            return {"provider": "claude", "error": str(e), "origin_signature": ORIGIN}

class AIProviderManager:
    def __init__(self, config_path=None):
        self.providers = {}
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                cfg = json.load(f).get("providers", {})
            if cfg.get("ollama", {}).get("enabled"):
                self.providers["ollama"] = OllamaProvider(cfg["ollama"])
            if cfg.get("openai", {}).get("enabled"):
                self.providers["openai"] = OpenAIProvider(cfg["openai"])
            if cfg.get("claude", {}).get("enabled"):
                self.providers["claude"] = ClaudeProvider(cfg["claude"])
        if not self.providers:
            self.providers["local"] = BaseAIProvider("local")
    def get_all(self):
        return list(self.providers.values())
    def get(self, name):
        return self.providers.get(name)
