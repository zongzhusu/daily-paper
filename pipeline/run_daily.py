"""daily-paper pipeline runner.

This project orchestrates:
- news-collector (paper_v0) -> CollectResult (items)
- news-scorer (score_v0)    -> ScoreResult (items with score + translated_zh)
- local curation + rendering -> daily markdown + static site

Design goals:
- Deterministic execution from bash/cron
- Minimal dependencies (Python stdlib + pyyaml)
- Clear file outputs in ./output

Outputs (by date):
- output/YYYY-MM-DD.json      (scored items snapshot, after curate)
- output/site/YYYY-MM-DD.html (static page)
- output/site/index.html, archive.html

Note: publish (git push) is handled by scripts/publish.sh.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from .adapters import load_collector_output, load_scorer_output
from .curate import normalize_entry
from .render import render_daily_markdown
from .topic_mapper import map_topic


@dataclass
class Paths:
    root: Path
    output_dir: Path
    output_site: Path
    tmp_dir: Path

    @staticmethod
    def from_root(root: Path) -> "Paths":
        return Paths(
            root=root,
            output_dir=root / "output",
            output_site=root / "output" / "site",
            tmp_dir=root / ".tmp",
        )


def default_run_date() -> str:
    return date.today().isoformat()


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "command failed: "
            + " ".join(cmd)
            + f"\nexit={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


def load_pipeline_config(root: Path) -> dict:
    cfg_path = root / "config" / "pipeline.yaml"
    if not cfg_path.exists():
        return {}
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}


def load_topics_config(root: Path) -> dict:
    cfg_path = root / "config" / "topics.yaml"
    if not cfg_path.exists():
        return {}
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}


def build_collect_request(root: Path, topics_cfg: dict) -> dict:
    # For now, use the default categories in news-collector/references/paper_v0.json.
    # Future: map topics -> categories & override categories here.
    _ = (root, topics_cfg)
    return {
        "mode": "paper_v0",
        "config": {},
        "run": {"maxItems": 50},
    }


def build_score_request(items: list[dict]) -> dict:
    # Keep it minimal. The scorer script supports reading items from request JSON.
    return {
        "mode": "score_v0",
        "items": items,
        "config": {},
        "run": {},
    }


def curate_items(items: list[dict]) -> list[dict]:
    curated: list[dict] = []
    for raw in items:
        item = normalize_entry(raw)
        if not item:
            continue
        item["topic"] = item.get("topic") or map_topic(item)
        curated.append(item)
    return curated


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_daily(run_date: str, *, mode: str = "paper") -> Path:
    root = Path(__file__).resolve().parents[1]
    paths = Paths.from_root(root)

    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.output_site.mkdir(parents=True, exist_ok=True)
    paths.tmp_dir.mkdir(parents=True, exist_ok=True)

    pipeline_cfg = load_pipeline_config(root)
    topics_cfg = load_topics_config(root)
    _ = (pipeline_cfg, mode)

    collect_req = build_collect_request(root, topics_cfg)
    collect_req_path = paths.tmp_dir / f"collect-{run_date}.json"
    collect_out_path = paths.tmp_dir / f"collect-result-{run_date}.json"
    write_json(collect_req_path, collect_req)

    proc = subprocess.run(
        [
            "node",
            "/root/.openclaw/skills/news-collector/scripts/arxiv_collect.js",
            "--input",
            str(collect_req_path),
        ],
        cwd=str(root),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0 and proc.stdout.strip() == "":
        raise RuntimeError(f"collector failed with no json output\nstderr:\n{proc.stderr}")
    collect_out_path.write_text(proc.stdout, encoding="utf-8")

    collect_result = load_collector_output(str(collect_out_path))
    if not isinstance(collect_result, dict) or collect_result.get("mode") != "paper_v0":
        raise RuntimeError(f"unexpected collect result: {type(collect_result)}")
    collected_items = collect_result.get("items") or []

    score_req = build_score_request(collected_items)
    score_req_path = paths.tmp_dir / f"score-{run_date}.json"
    score_out_path = paths.tmp_dir / f"score-result-{run_date}.json"
    write_json(score_req_path, score_req)

    # Run news-scorer
    proc2 = subprocess.run(
        [
            "node",
            "/root/.openclaw/skills/news-scorer/scripts/score.mjs",
            "--input",
            str(score_req_path),
        ],
        cwd=str(root),
        text=True,
        capture_output=True,
    )
    if proc2.returncode != 0 and proc2.stdout.strip() == "":
        raise RuntimeError(f"scorer failed with no json output\nstderr:\n{proc2.stderr}")
    score_out_path.write_text(proc2.stdout, encoding="utf-8")

    score_result = load_scorer_output(str(score_out_path))
    scored_items = score_result.get("items") if isinstance(score_result, dict) else None
    if not isinstance(scored_items, list):
        raise RuntimeError("unexpected scorer output (missing items list)")

    curated = curate_items(scored_items)

    out_json = paths.output_dir / f"{run_date}.json"
    write_json(out_json, curated)

    md = render_daily_markdown(run_date, curated)
    out_md = paths.output_dir / f"{run_date}.md"
    out_md.write_text(md + "\n", encoding="utf-8")

    # Build site
    _run(["node", "web/generate.js", "--mode", mode], cwd=root)

    return out_md


def main(argv: list[str]) -> int:
    run_date = default_run_date()
    mode = "paper"

    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--date":
            run_date = argv[i + 1]
            i += 2
            continue
        if token == "--mode":
            mode = argv[i + 1]
            i += 2
            continue
        i += 1

    out_md = run_daily(run_date, mode=mode)
    print(f"[daily-paper] OK: {out_md}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as e:
        print(f"[daily-paper] ERROR: {e}", file=sys.stderr)
        raise SystemExit(2)
