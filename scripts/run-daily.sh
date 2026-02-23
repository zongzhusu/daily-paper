#!/usr/bin/env bash
set -euo pipefail

RUN_DATE="$(TZ=Asia/Shanghai date +%F)"
MODE="paper"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --date)
      RUN_DATE="${2:-$RUN_DATE}"
      shift 2
      ;;
    --mode)
      MODE="${2:-paper}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

mkdir -p output .tmp output/site logs references

echo "[daily-paper] run pipeline for ${RUN_DATE}"
echo "[daily-paper] mode: ${MODE}"

time python3 -m pipeline.run_daily --date "$RUN_DATE" --mode "$MODE"
