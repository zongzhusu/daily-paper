import importlib.util
from pathlib import Path


def _load_render_daily_markdown():
    mod_path = Path("projects/daily-paper/pipeline/render.py")
    spec = importlib.util.spec_from_file_location("render", mod_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render_daily_markdown


def test_render_includes_pdf_link():
    render_daily_markdown = _load_render_daily_markdown()
    md = render_daily_markdown(
        "2026-02-20",
        [
            {
                "title": "T",
                "pdf_url": "https://arxiv.org/pdf/1.pdf",
                "abs_url": "https://arxiv.org/abs/1",
                "translated_zh": "摘要",
                "topic": "芯片与硬件架构",
                "score": 88,
            }
        ],
    )
    assert "https://arxiv.org/pdf/1.pdf" in md
    assert "芯片与硬件架构" in md
