#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"

python3 "$SCRIPT_DIR/generate_changelog.py" --repo "$REPO_ROOT" --output "$REPO_ROOT/CHANGELOG.md" "$@"
