from pathlib import Path
import subprocess
import json


def _run_generate(*args: str) -> None:
    cmd = ["node", "projects/daily-paper/web/generate.js", *args]
    subprocess.run(cmd, check=True)


def test_generate_default_mode_uses_paper_brand():
    _run_generate()
    html = Path("projects/daily-paper/output/site/index.html").read_text(encoding="utf-8")
    assert "Daily Paper" in html


def test_generate_news_mode_uses_news_brand():
    _run_generate("--mode", "news")
    html = Path("projects/daily-paper/output/site/index.html").read_text(encoding="utf-8")
    assert "Daily News" in html


def test_generate_builds_daily_pages_and_archive_from_json():
    output_dir = Path("projects/daily-paper/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    sample = {
        "date": "2026-02-20",
        "items": [
            {
                "title": "Chiplet-aware NPU",
                "topic": "芯片与硬件架构",
                "score": 92,
                "translated_zh": "面向大模型推理的 Chiplet 协同架构。",
                "abs_url": "https://arxiv.org/abs/2502.00001",
                "pdf_url": "https://arxiv.org/pdf/2502.00001.pdf",
            }
        ],
    }
    older = {"date": "2026-02-19", "items": []}
    (output_dir / "2026-02-20.json").write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
    (output_dir / "2026-02-19.json").write_text(json.dumps(older, ensure_ascii=False), encoding="utf-8")

    _run_generate()

    index_html = Path("projects/daily-paper/output/site/index.html").read_text(encoding="utf-8")
    day_html = Path("projects/daily-paper/output/site/2026-02-20.html").read_text(encoding="utf-8")
    archive_html = Path("projects/daily-paper/output/site/archive.html").read_text(encoding="utf-8")

    assert "Chiplet-aware NPU" in index_html
    assert "https://arxiv.org/pdf/2502.00001.pdf" in day_html
    assert "2026-02-20" in archive_html
    assert "2026-02-19" in archive_html


def test_generate_derives_arxiv_links_from_id_and_url():
    output_dir = Path("projects/daily-paper/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "date": "2026-02-18",
        "items": [
            {
                "title": "ASIC co-design for LLM inference",
                "topic": "芯片与硬件架构",
                "translated_zh": "通过编译器与硬件协同优化降低推理延迟。",
                "id": "arxiv:2502.12345",
            },
            {
                "title": "HBM-aware scheduling",
                "topic": "芯片与硬件架构",
                "translated_zh": "针对高带宽内存的任务调度策略。",
                "url": "https://arxiv.org/abs/2502.54321",
            },
        ],
    }
    (output_dir / "2026-02-18.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    _run_generate()

    day_html = Path("projects/daily-paper/output/site/2026-02-18.html").read_text(encoding="utf-8")
    assert "https://arxiv.org/abs/2502.12345" in day_html
    assert "https://arxiv.org/pdf/2502.12345.pdf" in day_html
    assert "https://arxiv.org/abs/2502.54321" in day_html
    assert "https://arxiv.org/pdf/2502.54321.pdf" in day_html


def test_archive_groups_by_month_and_shows_totals():
    output_dir = Path("projects/daily-paper/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    jan = {"date": "2026-01-31", "items": [{"title": "A"}]}
    feb = {"date": "2026-02-01", "items": [{"title": "B"}, {"title": "C"}]}
    (output_dir / "2026-01-31.json").write_text(json.dumps(jan, ensure_ascii=False), encoding="utf-8")
    (output_dir / "2026-02-01.json").write_text(json.dumps(feb, ensure_ascii=False), encoding="utf-8")

    _run_generate()

    archive_html = Path("projects/daily-paper/output/site/archive.html").read_text(encoding="utf-8")
    assert "2026年02月" in archive_html
    assert "2026年01月" in archive_html
    assert "共 2 个月" in archive_html
