import json
import os
import time
from datetime import datetime
from typing import Dict, Any

class MissionLogger:
    """
    Antigravity Phase 3.2: Mission Logger
    Responsibility: Record detailed logs of all mission events, API calls, and tool executions.
    Provides an 'Audit Trail' for autonomous operations.
    """
    
    from typing import Optional
    def __init__(self, log_dir: Optional[str] = None):
        if log_dir is None:
            ag_home = os.environ.get('AG_HOME', os.path.expanduser('~/Agents'))
            log_dir = os.path.join(ag_home, "antigravity-ops/logs")
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "mission_log.jsonl")

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Logs a structured event in JSONL format."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **data
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def log_api_call(self, provider: str, model: str, request: Dict[str, Any], response: Dict[str, Any], latency: float):
        """Specifically logs API interactions with metadata for observability."""
        self.log_event("api_call", {
            "provider": provider,
            "model": model,
            "request_summary": {
                "messages_count": len(request.get("messages", [])),
                "last_message": request.get("messages", [])[-1]["content"][:100] if request.get("messages") else ""
            },
            "response_status": "success" if "error" not in response else "failed",
            "latency_sec": float(round(latency, 3))
        })

    def log_mission_summary(self, mission_id: str, objective: str, state: str, history_count: int):
        """Logs a high-level summary of a completed or updated mission."""
        summary_file = os.path.join(self.log_dir, f"mission_{str(mission_id)[:8]}.summary.json")
        summary = {
            "mission_id": mission_id,
            "objective": objective,
            "final_state": state,
            "steps_completed": history_count,
            "last_updated": datetime.now().isoformat()
        }
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
