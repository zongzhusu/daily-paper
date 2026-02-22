def normalize_entry(item: dict):
    translated = (item.get("translated_zh") or "").strip()
    if not translated or len(translated) > 300:
        return None

    arxiv_id = (item.get("arxiv_id") or "").strip()
    if not arxiv_id:
        return None

    out = dict(item)
    out["translated_zh"] = translated
    out["abs_url"] = f"https://arxiv.org/abs/{arxiv_id}"
    out["pdf_url"] = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    return out
