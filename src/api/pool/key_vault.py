import os
from typing import List, Dict, Optional

class KeyVault:
    """
    Antigravity Key Vault
    Responsibility: Load and provide access to the pool of API keys.
    """
    
    def __init__(self, env_path: Optional[str] = None):
        if env_path is None:
            ag_home = os.environ.get('AG_HOME', os.path.expanduser('~/Agents'))
            env_path = os.path.join(ag_home, "antigravity-ops/.env")
        self.env_path = env_path
        self.keys: Dict[str, List[str]] = {
            "gemini": [],
            "groq": [],
            "openrouter": []
        }
        self.load_keys()

    def load_keys(self):
        """Discovers keys from the .env file based on naming conventions (e.g., GEMINI_KEY_A)."""
        if not os.path.exists(self.env_path):
            return

        with open(self.env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Handle 'export KEY=VAL' or 'KEY=VAL'
                if line.startswith('export '):
                    line = line.replace('export ', '', 1)
                
                if '=' not in line:
                    continue
                    
                key_name, val = line.split('=', 1)
                val = val.strip('"').strip("'")
                
                # Primary key (legacy support for GEMINI_API_KEY)
                if key_name == "GEMINI_API_KEY":
                    self.keys["gemini"].append(val)
                elif "GEMINI_KEY" in key_name:
                    self.keys["gemini"].append(val)
                elif "GROQ_KEY" in key_name:
                    self.keys["groq"].append(val)
                elif "OPENROUTER_KEY" in key_name:
                    self.keys["openrouter"].append(val)

    def get_keys(self, provider: str) -> List[str]:
        return self.keys.get(provider.lower(), [])
