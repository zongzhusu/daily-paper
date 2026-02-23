"""Score paper items using daily-report's ContentProcessor.

We reuse the scoring stack from daily-report to avoid duplicating logic.
Input: list of items (collector schema) with title/abstract/url/categories
Output: list of enriched items with fields:
- score (int)
- translated_zh (string)

This is a pragmatic bridge until a dedicated paper scorer is built.
"""

from __future__ import annotations

import os
import sys
from typing import Any


def _ensure_daily_report_import() -> None:
    # daily-report pipeline is a python package-like folder.
    sys.path.insert(0, "/root/.openclaw/projects/daily-report/pipeline")


def score_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _ensure_daily_report_import()

    # Import after sys.path change
    from core.processors import ContentProcessor  # type: ignore

    # Some daily-report internals expect cwd at project root.
    os.chdir("/root/.openclaw/projects/daily-report")

    processor = ContentProcessor()

    out: list[dict[str, Any]] = []
    for item in items:
        title = str(item.get("title") or "").strip()
        abstract = str(item.get("abstract") or "").strip()
        source = str(item.get("source") or "arxiv")

        if not title:
            continue

        # First round on title+abstract (fast integer)
        r1 = processor.score_article_first_round(title, abstract[:3000], source)
        # Always do second round for papers (they are usually short), but keep json mode.
        r2 = processor.score_article(title, abstract[:2000] or title, source)

        enriched = dict(item)
        enriched["first_score"] = r1
        enriched["score"] = int(r2.get("score", r1)) if isinstance(r2, dict) else int(r1)
        enriched["translated_zh"] = str(r2.get("reasoning") or "").strip() if isinstance(r2, dict) else ""
        out.append(enriched)

    return out
