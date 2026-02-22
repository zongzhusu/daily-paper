#!/usr/bin/env bash
set -euo pipefail

RUN_DATE="$(date +%F)"
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

echo "[daily-paper] run pipeline for ${RUN_DATE}"
echo "[daily-paper] mode: ${MODE}"
echo "[daily-paper] stages: collect -> score -> curate -> render -> build"
