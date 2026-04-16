import sqlite3
import json
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict


@dataclass
class AgentState:
    current_task: Optional[str] = None
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    error_count: int = 0
    iteration: int = 0


class StateManager:
    def __init__(self, db_path: str = "agent_state.db"):
        self.db_path = db_path
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS task_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                action TEXT,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()

    def save(self, state: AgentState):
        self.db.execute(
            "INSERT OR REPLACE INTO state VALUES (?, ?)",
            ("current", json.dumps(asdict(state)))
        )
        self.db.commit()

    def load(self) -> AgentState:
        row = self.db.execute(
            "SELECT value FROM state WHERE key = ?", ("current",)
        ).fetchone()
        if row:
            data = json.loads(row[0])
            return AgentState(**data)
        return AgentState()

    def log_task(self, task_id: str, action: str, result: str):
        self.db.execute(
            "INSERT INTO task_log (task_id, action, result) VALUES (?, ?, ?)",
            (task_id, action, str(result))
        )
        self.db.commit()

    def get_history(self, limit: int = 50) -> List[Dict]:
        rows = self.db.execute(
            "SELECT task_id, action, result, timestamp FROM task_log ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [
            {"task_id": r[0], "action": r[1], "result": r[2], "timestamp": r[3]}
            for r in rows
        ]

    def reset(self):
        self.db.execute("DELETE FROM state")
        self.db.execute("DELETE FROM task_log")
        self.db.commit()
