from pathlib import Path


def test_readme_declares_0830_publish_sla():
    text = Path("projects/daily-paper/README.md").read_text(encoding="utf-8")
    assert "08:30" in text
    assert "Asia/Shanghai" in text
