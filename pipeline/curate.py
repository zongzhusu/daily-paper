"""Curation utilities for daily-paper.

Normalize scored items into the compact schema used by the site generator.
"""

from __future__ import annotations

from typing import Any, Optional


def normalize_entry(item: dict[str, Any]) -> Optional[dict[str, Any]]:
    title = str(item.get("title") or "").strip()
    if not title:
        return None

    arxiv_id = str(item.get("arxiv_id") or "").strip()
    if not arxiv_id:
        return None

    translated = (item.get("translated_zh") or item.get("reasoning") or "").strip()
    if not translated:
        return None

    # Keep Markdown formatting for web rendering; cap length to avoid overly long cards.
    if len(translated) > 900:
        translated = translated[:897] + "..."

    out = {
        "title": title,
        "topic": str(item.get("topic") or "").strip() or "未分类",
        "score": int(item.get("score") or item.get("second_score") or item.get("first_score") or 0),
        "translated_zh": translated,
        "arxiv_id": arxiv_id,
        "abs_url": item.get("abs_url") or f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": item.get("pdf_url") or f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        # For debugging / UX: show published date (normalized by collector timezone).
        "published_at": item.get("publishedAt") or item.get("published_at"),
        "published_date": item.get("publishedDate") or item.get("published_date"),
    }

    return out
