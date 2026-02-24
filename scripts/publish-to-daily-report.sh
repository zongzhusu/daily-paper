#!/usr/bin/env bash
set -euo pipefail

DATE="${1:-}"
if [[ -z "$DATE" ]]; then
  DATE="$(TZ=Asia/Shanghai date +%F)"
fi

ROOT="/root/.openclaw/projects"
PAPER_REPO="${ROOT}/daily-paper"
REPORT_REPO="${ROOT}/daily-report"

PAPER_JSON_SRC="${PAPER_REPO}/output/${DATE}.json"
REPORT_PAPERS_DIR="${REPORT_REPO}/output/papers"
REPORT_JSON_DST="${REPORT_PAPERS_DIR}/${DATE}.json"

REPORT_DIST_DIR="${REPORT_REPO}/web/dist"

log() {
  echo "[publish-to-daily-report] $*"
}

die() {
  echo "[publish-to-daily-report][ERROR] $*" >&2
  exit 1
}

log "date=${DATE}"

[[ -d "$PAPER_REPO/.git" ]] || die "missing git repo: ${PAPER_REPO}"
[[ -d "$REPORT_REPO/.git" ]] || die "missing git repo: ${REPORT_REPO}"

if [[ ! -f "$PAPER_JSON_SRC" ]]; then
  die "missing paper json: ${PAPER_JSON_SRC} (run daily-paper pipeline first)"
fi

log "sync ${PAPER_JSON_SRC} -> ${REPORT_JSON_DST}"
mkdir -p "$REPORT_PAPERS_DIR"
cp -f "$PAPER_JSON_SRC" "$REPORT_JSON_DST"

log "rebuild daily-report web/dist"
cd "$REPORT_REPO"
node web/generate.js >/dev/null

log "git commit+push daily-report"

cd "$REPORT_REPO"
# Always start clean to keep rebase/push reliable.
if [[ -n "$(git status --porcelain=v1)" ]]; then
  die "daily-report repo is dirty; please commit/stash first: ${REPORT_REPO}"
fi

# Rebase first to avoid push rejection.
git pull --rebase origin master

git add "$REPORT_JSON_DST"
# web/dist is ignored by default
if [[ -d "$REPORT_DIST_DIR" ]]; then
  git add -f web/dist
fi

if git diff --cached --quiet; then
  log "no changes to push"
  exit 0
fi

git commit -m "chore: publish daily-paper ${DATE}"

git push origin master

log "done"
