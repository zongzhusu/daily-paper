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
