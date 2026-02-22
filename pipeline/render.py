def render_daily_markdown(run_date: str, items: list[dict]) -> str:
    lines = [f"# Daily Paper {run_date}", ""]
    for i, item in enumerate(items, start=1):
        lines.append(f"## {i}. {item['title']}")
        lines.append(f"- 主题: {item['topic']}")
        lines.append(f"- 评分: {item['score']}")
        lines.append(f"- 摘要: {item['translated_zh']}")
        lines.append(f"- abs: {item['abs_url']}")
        lines.append(f"- pdf: {item['pdf_url']}")
        lines.append("")
    return "\n".join(lines)
