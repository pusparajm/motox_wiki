#!/usr/bin/env bash
# Point this repo at version-controlled hooks in .githooks/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository: $ROOT" >&2
  exit 1
fi

chmod +x .githooks/pre-commit .githooks/post-merge 2>/dev/null || true
git config core.hooksPath .githooks

echo "Git hooks enabled (core.hooksPath=.githooks)"
echo "  pre-commit  → rebuild js/dist/ before commit when JS sources change"
echo "  post-merge  → rebuild js/dist/ after git pull when sources are newer"
