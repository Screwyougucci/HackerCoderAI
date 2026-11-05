import sqlite3
from pathlib import Path
from datetime import datetime, timezone

class MemoryStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY, role TEXT NOT NULL,
                content TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY, note TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, goal TEXT NOT NULL, workspace TEXT NOT NULL,
                status TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS task_steps (
                id INTEGER PRIMARY KEY, task_id TEXT NOT NULL, step INTEGER NOT NULL,
                action TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL,
                UNIQUE(task_id,step)
            );
            """)

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()

    def add_message(self, role: str, content: str):
        with self.connect() as db:
            db.execute("INSERT INTO messages(role,content,created_at) VALUES(?,?,?)",
                       (role, content, self.now()))

    def recent_messages(self, limit: int = 12):
        with self.connect() as db:
            rows = db.execute("SELECT role,content FROM messages ORDER BY id DESC LIMIT ?",
                              (limit,)).fetchall()
        return list(reversed([dict(row) for row in rows]))

    def remember(self, note: str):
        note = note.strip()
        if not note or len(note) > 1000:
            raise ValueError("Memory must contain 1–1000 characters.")
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO memories(note,created_at) VALUES(?,?)",
                       (note, self.now()))

    def memories(self):
        with self.connect() as db:
            return [row["note"] for row in db.execute(
                "SELECT note FROM memories ORDER BY id DESC LIMIT 30")]

    def clear_messages(self):
        with self.connect() as db:
            db.execute("DELETE FROM messages")

    def create_task(self, goal: str, workspace: str = "") -> str:
        import uuid
        task_id = uuid.uuid4().hex
        with self.connect() as db:
            db.execute("""INSERT INTO tasks(id,goal,workspace,status,detail,created_at,updated_at)
                          VALUES(?,?,?,?,?,?,?)""",
                       (task_id, goal, workspace, "queued", "Queued", self.now(), self.now()))
        return task_id

    def update_task(self, task_id: str, status: str, detail: str = ""):
        with self.connect() as db:
            db.execute("""UPDATE tasks SET status=?,detail=?,updated_at=? WHERE id=?""",
                       (status, detail[:12000], self.now(), task_id))

    def get_task(self, task_id: str):
        with self.connect() as db:
            row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not row:
                return None
            item = dict(row)
            item["steps"] = [dict(x) for x in db.execute(
                "SELECT step,action,detail,created_at FROM task_steps WHERE task_id=? ORDER BY step",
                (task_id,)).fetchall()]
            return item

    def add_task_step(self, task_id: str, step: int, action: str, detail: str):
        with self.connect() as db:
            db.execute("""INSERT OR REPLACE INTO task_steps(task_id,step,action,detail,created_at)
                          VALUES(?,?,?,?,?)""",
                       (task_id, step, action, detail[:12000], self.now()))

    def list_tasks(self, limit: int = 20):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
                              (max(1, min(limit, 50)),)).fetchall()
        return [dict(row) for row in rows]

    def recover_interrupted_tasks(self):
        with self.connect() as db:
            db.execute("""UPDATE tasks SET status='paused',
                          detail='App restarted; saved checkpoint is available to resume.',
                          updated_at=? WHERE status IN ('queued','running')""", (self.now(),))
