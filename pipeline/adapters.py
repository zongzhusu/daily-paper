from pathlib import Path
import json


def load_collector_output(path: str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_scorer_output(path: str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
