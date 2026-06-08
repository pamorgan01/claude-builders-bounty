#!/usr/bin/env python3
"""Unit checks for destructive_bash_guard.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).with_name("destructive_bash_guard.py")
spec = importlib.util.spec_from_file_location("destructive_bash_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


BLOCKED = [
    "rm -rf build",
    "rm -fr /tmp/cache",
    "rm -r -f ./dist",
    "psql -c 'DROP TABLE users'",
    "mysql -e 'TRUNCATE sessions'",
    "sqlite3 app.db 'DELETE FROM users'",
    "git push --force origin main",
    "git push --force-with-lease origin main",
]

ALLOWED = [
    "rm build.log",
    "rm -r dist",
    "git push origin main",
    "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
    "python3 -m pytest",
    "npm run build",
]


def main() -> int:
    for command in BLOCKED:
        assert guard.block_reason(command), f"expected block: {command}"
    for command in ALLOWED:
        assert guard.block_reason(command) is None, f"expected allow: {command}"
    print("destructive bash guard tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
