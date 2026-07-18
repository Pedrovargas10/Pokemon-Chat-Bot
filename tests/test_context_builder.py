import pytest
from pathlib import Path

from src.context_builder import build_context, get_system_prompt


def test_build_context_reads_all_md_files(tmp_path):
    (tmp_path / "events.md").write_text("# Events\n\n## Kyogre Raids\n- type: raid")
    (tmp_path / "announcements.md").write_text(
        "# Announcements\n\n## Anniversary\n- Big event"
    )
    (tmp_path / "not_md.txt").write_text("should be ignored")

    context = build_context(tmp_path)

    assert "Kyogre Raids" in context
    assert "Anniversary" in context
    assert "should be ignored" not in context


def test_build_context_empty_dir(tmp_path):
    context = build_context(tmp_path)
    assert context == ""


def test_build_context_nonexistent_dir():
    context = build_context(Path("/nonexistent/dir"))
    assert context == ""


def test_get_system_prompt_includes_persona():
    context = "## Kyogre Raids\n- type: raid"
    prompt = get_system_prompt(context)

    assert "Pokémon GO" in prompt
    assert context in prompt
    assert "brasileiro" in prompt.lower()


def test_get_system_prompt_handles_empty_context():
    prompt = get_system_prompt("")
    assert "Pokémon GO" in prompt
    assert "indisponíveis" in prompt.lower()
