from app.memory import MemoryStore

def test_memory_persists(tmp_path):
    path = str(tmp_path / "memory.sqlite3")
    store = MemoryStore(path)
    store.remember("Prefer concise code examples")
    assert "Prefer concise code examples" in store.memories()
    store.add_message("user", "hello")
    assert store.recent_messages()[0]["content"] == "hello"
