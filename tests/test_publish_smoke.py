from pathlib import Path


def test_publish_script_has_dry_run_flag():
    text = Path("projects/daily-paper/scripts/publish.sh").read_text(encoding="utf-8")
    assert "--dry-run" in text


def test_build_site_script_forwards_mode_flag():
    text = Path("projects/daily-paper/scripts/build-site.sh").read_text(encoding="utf-8")
    assert "--mode" in text


def test_run_daily_script_accepts_mode_flag():
    text = Path("projects/daily-paper/scripts/run-daily.sh").read_text(encoding="utf-8")
    assert "--mode" in text


def test_publish_script_builds_and_pushes_site():
    text = Path("projects/daily-paper/scripts/publish.sh").read_text(encoding="utf-8")
    assert "build-site.sh" in text
    assert "git push" in text


def test_deploy_workflow_points_to_output_site():
    text = Path("projects/daily-paper/.github/workflows/deploy.yml").read_text(encoding="utf-8")
    assert "projects/daily-paper/output/site" in text
