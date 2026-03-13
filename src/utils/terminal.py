import subprocess
import os
from typing import Dict, Any

class SafeTerminalTool:
    """
    Antigravity Phase 3: Safe Terminal Tool
    Responsibility: Execute shell commands within the Antigravity context.
    Safeguards: Prevents destructive commands and respects the Antigravity Ops directory.
    """
    
    from typing import Optional
    def __init__(self, workspace_root: Optional[str] = None):
        if workspace_root is None:
            ag_home = os.environ.get('AG_HOME', os.path.expanduser('~/Agents'))
            workspace_root = os.path.join(ag_home, "antigravity-ops")
        self.workspace_root = workspace_root
        # Basic protection list (not exhaustive)
        self.blacklist = ["rm -rf /", "sudo", "mkfs", "dd"]

    def execute(self, command: str) -> Dict[str, Any]:
        """Executes a command and returns the result."""
        for restricted in self.blacklist:
            if restricted in command:
                return {"success": False, "output": f"Error: Command '{command}' is restricted."}
        
        print(f"🛠  Terminal: Executing [{command}]...")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=30 # Safety timeout
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "exit_code": result.returncode
                }
            else:
                return {
                    "success": False,
                    "output": result.stderr,
                    "exit_code": result.returncode
                }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Error: Command timed out after 30 seconds."}
        except Exception as e:
            return {"success": False, "output": f"Error: {str(e)}"}
