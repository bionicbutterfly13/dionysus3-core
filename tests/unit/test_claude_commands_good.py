from pathlib import Path


def test_good_command_definition_exists_and_has_sections() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    command_path = repo_root / ".claude" / "commands" / "good.md"

    assert command_path.exists(), "Expected /good command definition to exist"

    content = command_path.read_text(encoding="utf-8")
    assert "What's good:" in content
    assert "What's broken:" in content
    assert "What works but shouldn't:" in content
    assert "What doesn't but pretends to:" in content
