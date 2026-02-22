#!/usr/bin/env bash
set -euo pipefail

MODE="paper"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-paper}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

node "$(dirname "$0")/../web/generate.js" --mode "$MODE"
