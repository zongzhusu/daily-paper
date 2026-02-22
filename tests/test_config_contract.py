from pathlib import Path

import yaml


def test_topics_has_five_sections():
    cfg = yaml.safe_load(
        Path("projects/daily-paper/config/topics.yaml").read_text(encoding="utf-8")
    )
    assert len(cfg["topics"]) == 5
    assert "芯片与硬件架构" in [x["name"] for x in cfg["topics"]]
