import json
import os
import requests
import time
from typing import Optional, Dict, Any, List
from src.api.pool.key_vault import KeyVault
from src.api.pool.rotation_logic import RotationManager
from src.utils.logger import MissionLogger

class Dispatcher:
    """
    Antigravity Core Router: Dispatcher
    Responsibility: Route requests to the optimal model based on task complexity
    and environmental state (active-provider.json).
    """
    
    def __init__(self, ops_root: Optional[str] = None):
        if ops_root is None:
            ag_home = os.environ.get('AG_HOME', os.path.expanduser('~/Agents'))
            ops_root = os.path.join(ag_home, "antigravity-ops")
        self.ops_root = ops_root
        self.config_path = os.path.join(ops_root, "config/active-provider.json")
        self.proxy_url = "http://localhost:8000"
        self.master_key = "sk-antigravity-admin"
        
        # Initialize logging
        self.logger = MissionLogger()
        
        # Initialize key management
        self.vault = KeyVault()
        self.managers: Dict[str, RotationManager] = {}
        self._sync_rotation_managers()

    def _sync_rotation_managers(self):
        """Initializes rotation managers for each provider found in the vault."""
        for provider in ["gemini", "groq", "openrouter"]:
            keys = self.vault.get_keys(provider)
            if keys:
                self.managers[provider] = RotationManager(keys, provider)
        
    def get_active_provider_state(self) -> Dict[str, Any]:
        """Reads the current active provider from the local state file."""
        if not os.path.exists(self.config_path):
            return {"provider": "gemini", "status": "unknown"}
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {"provider": "gemini", "status": "error"}

    def route(self, complexity: str = "smart") -> str:
        """
        Maps a logical complexity requirement to a specific model alias 
        configured in the LiteLLM gateway.
        """
        if complexity == "fast":
            return "antigravity-fast"
        return "antigravity-smart"

    def chat_completion(self, messages: list, complexity: str = "smart", **kwargs) -> Dict[str, Any]:
        """
        Executes a chat completion via the LiteLLM Proxy Gateway.
        """
        start_time = time.time()
        model = self.route(complexity)
        
        headers = {
            "Authorization": f"Bearer {self.master_key}",
            "Content-Type": "application/json"
        }
        
        request_payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.proxy_url}/chat/completions",
                headers=headers,
                json=request_payload
            )
            
            latency = time.time() - start_time
            
            if response.status_code == 429:
                print("🚨 429 Detected: LiteLLM Pool is exhausted.")
                result = {"error": "Rate limit exceeded (429)", "status": "failed"}
                self.logger.log_api_call("unknown", model, request_payload, result, latency)
                return result
                
            response.raise_for_status()
            result = response.json()
            
            # Extract provider from response headers or body if available
            provider = result.get("provider", "pooled")
            self.logger.log_api_call(provider, model, request_payload, result, latency)
            
            return result
        except requests.exceptions.RequestException as e:
            latency = time.time() - start_time
            result = {"error": str(e), "status": "failed"}
            self.logger.log_api_call("error", model, request_payload, result, latency)
            return result

    def resilient_completion(self, messages: list, complexity: str = "fast", retries: int = 1) -> Dict[str, Any]:
        """
        Attempts a completion, with an automatic fallback to 'smart' 
        if 'fast' fails (e.g., due to rate limits).
        """
        response = self.chat_completion(messages, complexity=complexity)
        
        if "error" in response and "429" in response["error"] and complexity == "fast":
            print("🔄 Fast model throttled. Falling back to Smart model...")
            return self.chat_completion(messages, complexity="smart")
            
        return response
