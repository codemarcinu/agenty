from agents.memory_manager import MemoryContext


def test_set_last_command():
    ctx = MemoryContext(session_id="abc123")
    assert ctx.last_command is None
    ctx.set_last_command("test_command")
    assert ctx.last_command == "test_command"
