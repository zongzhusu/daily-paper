import importlib.util
from pathlib import Path


def _load_normalize_entry():
    mod_path = Path("projects/daily-paper/pipeline/curate.py")
    spec = importlib.util.spec_from_file_location("curate", mod_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.normalize_entry


def test_adds_pdf_url_from_arxiv_id():
    normalize_entry = _load_normalize_entry()
    out = normalize_entry({"arxiv_id": "2502.01234", "translated_zh": "a" * 30})
    assert out["pdf_url"] == "https://arxiv.org/pdf/2502.01234.pdf"


def test_rejects_over_300_chars_translation():
    normalize_entry = _load_normalize_entry()
    out = normalize_entry({"arxiv_id": "2502.01234", "translated_zh": "中" * 301})
    assert out is None
