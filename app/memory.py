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
