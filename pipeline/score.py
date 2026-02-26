"""Score arXiv paper items (daily-paper).

This module reuses `daily-report`'s ContentProcessor (LLM-based) to produce:
- first_score (int 0-100)
- score (int 0-100) + translated_zh (short Chinese summary/reasoning)

To keep runtime/cost bounded for daily cron:
- First-round score is computed for up to `max_items` collected papers.
- Only top-K (by first_score, above threshold) get second-round scoring.

Env knobs:
- DAILY_PAPER_MAX_ITEMS (default 30)
- DAILY_PAPER_TOPK (default 10)
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any


def _ensure_daily_report_import() -> None:
    sys.path.insert(0, "/root/.openclaw/projects/daily-report/pipeline")


_ARXIV_ID_RE = re.compile(r"(\d{4}\.\d{4,5}(?:v\d+)?)")


def extract_arxiv_id(item: dict[str, Any]) -> str:
    for key in ("arxiv_id", "id", "url", "abs_url", "pdf_url"):
        val = item.get(key)
        if not val:
            continue
        s = str(val)
        m = _ARXIV_ID_RE.search(s)
        if m:
            return m.group(1)
    return ""


def score_items(collected_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _ensure_daily_report_import()

    from core.processors import ContentProcessor  # type: ignore
    from core.utils import smooth_score  # type: ignore

    # daily-report internals expect cwd at project root.
    os.chdir("/root/.openclaw/projects/daily-report")

    # daily-paper wants a stricter default threshold than daily-report.
    # NOTE: ContentProcessor reads SCORE_THRESHOLD at init time.
    paper_threshold = int(os.getenv("DAILY_PAPER_SCORE_THRESHOLD", "85"))
    os.environ["SCORE_THRESHOLD"] = str(paper_threshold)

    processor = ContentProcessor()

    max_items = int(os.getenv("DAILY_PAPER_MAX_ITEMS", "30"))
    topk = int(os.getenv("DAILY_PAPER_TOPK", "10"))

    items = collected_items[: max(0, max_items)]

    scored_stage1: list[dict[str, Any]] = []
    for item in items:
        title = str(item.get("title") or "").strip()
        abstract = str(item.get("abstract") or "").strip()
        source = str(item.get("source") or "arxiv")
        if not title:
            continue
        r1 = processor.score_article_first_round(title, abstract[:3000], source)
        enriched = dict(item)
        enriched["arxiv_id"] = extract_arxiv_id(enriched)
        enriched["first_score"] = int(r1)
        scored_stage1.append(enriched)

    # pick candidates for round-2
    threshold = int(getattr(processor, "score_threshold", 50))
    candidates = [x for x in scored_stage1 if int(x.get("first_score") or 0) >= threshold]
    candidates.sort(key=lambda x: int(x.get("first_score") or 0), reverse=True)
    candidates = candidates[: max(0, topk)]

    # build lookup for which items get round2
    round2_ids = set()
    for x in candidates:
        # Prefer arxiv_id, fallback to id/url
        round2_ids.add(x.get("arxiv_id") or x.get("id") or x.get("url"))

    out: list[dict[str, Any]] = []
    for item in scored_stage1:
        key = item.get("arxiv_id") or item.get("id") or item.get("url")
        if key in round2_ids:
            title = str(item.get("title") or "").strip()
            abstract = str(item.get("abstract") or "").strip()
            source = str(item.get("source") or "arxiv")

            r2 = processor.score_article(title, abstract[:2000] or title, source)
            if not isinstance(r2, dict):
                # fallback
                item["score"] = int(item.get("first_score") or 0)
                item["translated_zh"] = ""
                out.append(item)
                continue

            second_score = int(r2.get("score", item.get("first_score") or 0))
            final_score = int(smooth_score(int(item.get("first_score") or 0), second_score))

            item["second_score"] = second_score
            item["score"] = final_score

            # Prefer structured Chinese summary (Markdown, multi-line). Fallback to reasoning.
            zh = str(r2.get("summary_zh") or r2.get("reasoning") or "").strip()
            # Keep formatting; cap length to avoid breaking the page layout.
            if len(zh) > 900:
                zh = zh[:897] + "..."
            item["translated_zh"] = zh

        out.append(item)

    return out
