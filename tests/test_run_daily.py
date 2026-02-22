import importlib.util
from pathlib import Path


def _load_build_plan():
    mod_path = Path("projects/daily-paper/pipeline/run_daily.py")
    spec = importlib.util.spec_from_file_location("run_daily", mod_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_plan


def test_plan_contains_five_stages():
    build_plan = _load_build_plan()
    stages = build_plan("2026-02-20")
    assert stages == ["collect", "score", "curate", "render", "build"]
