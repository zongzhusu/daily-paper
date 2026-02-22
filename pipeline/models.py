from dataclasses import dataclass


@dataclass
class PaperItem:
    arxiv_id: str
    title: str
    categories: list[str]
    translated_zh: str
    score: float
    topic: str = ""
    abs_url: str = ""
    pdf_url: str = ""
