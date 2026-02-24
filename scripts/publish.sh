#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="paper"
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-paper}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    *)
      shift
      ;;
  esac
done

cd "$PROJECT_ROOT"

echo "[daily-paper] build site (mode=${MODE})"
bash scripts/build-site.sh --mode "$MODE"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] skip git push"
  exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[daily-paper] not in git repository, stop publish"
  exit 1
fi

git add output/*.json output/site

if git diff --cached --quiet; then
  echo "[daily-paper] no site changes to publish"
  exit 0
fi

git commit -m "chore: publish daily-paper site (${MODE})"
git push

echo "[daily-paper] publish complete (git push done)"

# Optional: also publish into daily-report (Cloudflare Pages site) if available.
# This keeps the "web view" in the daily-report Pages project updated.
if [[ "${DAILY_PAPER_PUBLISH_TO_DAILY_REPORT:-0}" == "1" ]]; then
  echo "[daily-paper] publish to daily-report (papers)"
  bash scripts/publish-to-daily-report.sh "$(TZ=Asia/Shanghai date +%F)"
fi
