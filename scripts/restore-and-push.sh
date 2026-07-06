#!/usr/bin/env bash
# Restore the cm-difftest work from the git bundle and push it to GitHub.
#
# Run this in a *NEW* Claude Code session (web or desktop) that has WRITE access
# to apani0409/markdown — the GitHub token is captured at session start, so a
# fresh session is required after installing the Claude GitHub App with
# "Contents: Read and write".
#
# Usage:  bash restore-and-push.sh [path/to/cm-difftest-final.bundle]
set -euo pipefail

BUNDLE="${1:-cm-difftest-final.bundle}"
BRANCH="claude/project-setup-docs-m7noqc"

[[ -f "$BUNDLE" ]] || { echo "ERROR: bundle not found: $BUNDLE" >&2; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "ERROR: run inside the cloned repo" >&2; exit 1; }

echo ">> verifying bundle"
git bundle verify "$BUNDLE"

echo ">> fetching branch '$BRANCH' from the bundle"
git fetch "$BUNDLE" "refs/heads/${BRANCH}:refs/heads/${BRANCH}"

echo ">> pushing to origin (the session's write-enabled remote)"
git push -u origin "$BRANCH"

echo ">> done. Branch pushed: $BRANCH"
echo "   Open a PR from it if you want it on the default branch."
