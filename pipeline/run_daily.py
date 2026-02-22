from datetime import date


def build_plan(run_date: str) -> list[str]:
    _ = run_date
    return ["collect", "score", "curate", "render", "build"]


def default_run_date() -> str:
    return date.today().isoformat()
