import importlib.util
from pathlib import Path


def _load_map_topic():
    mod_path = Path("projects/daily-paper/pipeline/topic_mapper.py")
    spec = importlib.util.spec_from_file_location("topic_mapper", mod_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.map_topic


def test_maps_cs_ar_to_hardware():
    map_topic = _load_map_topic()
    item = {"categories": ["cs.AR"], "title": "Chiplet-aware NPU"}
    assert map_topic(item) == "芯片与硬件架构"


def test_prefers_hardware_when_title_mentions_asic():
    map_topic = _load_map_topic()
    item = {"categories": ["cs.AI"], "title": "ASIC co-design for LLM inference"}
    assert map_topic(item) == "芯片与硬件架构"
