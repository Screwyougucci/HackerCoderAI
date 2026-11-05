from app.memory import MemoryStore

def test_memory_persists(tmp_path):
    path = str(tmp_path / "memory.sqlite3")
    store = MemoryStore(path)
    store.remember("Prefer concise code examples")
    assert "Prefer concise code examples" in store.memories()
    store.add_message("user", "hello")
    assert store.recent_messages()[0]["content"] == "hello"

def test_agent_task_checkpoints_persist(tmp_path):
    store = MemoryStore(str(tmp_path / "memory.sqlite3"))
    task_id = store.create_task("Review my project")
    store.update_task(task_id, "running", "Step 1")
    store.add_task_step(task_id, 1, "analyze_patterns", '{"finding_count": 0}')
    task = store.get_task(task_id)
    assert task["status"] == "running"
    assert task["steps"][0]["action"] == "analyze_patterns"
