import sqlite3
import json
import os
from typing import Dict, Any, List, Optional

class SessionStore:
    """
    Antigravity Memory Layer: Session Store
    Responsibility: Persist mission states, plans, and history using SQLite.
    Provides 'Episodic Memory' for the control plane.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            ag_home = os.environ.get('AG_HOME', os.path.expanduser('~/Agents'))
            db_path = os.path.join(ag_home, "antigravity-ops/memory/antigravity.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS missions (
                    id TEXT PRIMARY KEY,
                    objective TEXT,
                    state TEXT,
                    plan TEXT,  -- JSON string
                    current_step INTEGER,
                    created_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission_id TEXT,
                    step_id INTEGER,
                    type TEXT,
                    result TEXT,
                    timestamp REAL,
                    FOREIGN KEY(mission_id) REFERENCES missions(id)
                )
            """)
            conn.commit()

    def save_mission(self, mission: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO missions (id, objective, state, plan, current_step, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                mission["id"],
                mission["objective"],
                mission["state"],
                json.dumps(mission["plan"]),
                mission["current_step"],
                mission["created_at"]
            ))
            conn.commit()

    def add_history(self, mission_id: str, step_data: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO history (mission_id, step_id, type, result, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                mission_id,
                step_data["step_id"],
                step_data["type"],
                step_data["result"],
                step_data.get("timestamp", 0.0)
            ))
            conn.commit()

    def load_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM missions WHERE id = ?", (mission_id,)).fetchone()
            if not row:
                return None
            
            mission = {
                "id": row[0],
                "objective": row[1],
                "state": row[2],
                "plan": json.loads(row[3]),
                "current_step": row[4],
                "created_at": row[5],
                "history": []
            }
            
            history_rows = conn.execute("SELECT step_id, type, result FROM history WHERE mission_id = ? ORDER BY id", (mission_id,)).fetchall()
            for h in history_rows:
                mission["history"].append({
                    "step_id": h[0],
                    "type": h[1],
                    "result": h[2]
                })
            
            return mission

    def list_missions(self, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT id, objective, state, created_at FROM missions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [{"id": r[0], "objective": r[1], "state": r[2], "created_at": r[3]} for r in rows]
