#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


DEFAULT_BLOCK_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def normalize(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip())


def has_rm_force_recursive(command: str) -> bool:
    for match in re.finditer(r"(?:^|[;&|]\s*)rm\s+([^;&|]+)", command, re.IGNORECASE):
        args = match.group(1).split()
        combined_flags = "".join(arg[1:] for arg in args if arg.startswith("-") and not arg.startswith("--"))
        long_flags = {arg for arg in args if arg.startswith("--")}
        recursive = "r" in combined_flags or "R" in combined_flags or "--recursive" in long_flags
        force = "f" in combined_flags or "--force" in long_flags
        if recursive and force:
            return True
    return False


def delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        tail = command[match.end() :]
        statement = re.split(r"[;\n]", tail, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True
    return False


def block_reason(command: str) -> str | None:
    normalized = normalize(command)

    if has_rm_force_recursive(normalized):
        return "Blocked destructive filesystem removal: rm with recursive and force flags."
    if re.search(r"\bdrop\s+table\b", normalized, re.IGNORECASE):
        return "Blocked destructive SQL command: DROP TABLE."
    if re.search(r"\btruncate\b", normalized, re.IGNORECASE):
        return "Blocked destructive SQL command: TRUNCATE."
    if delete_without_where(normalized):
        return "Blocked destructive SQL command: DELETE FROM without a WHERE clause."
    if re.search(r"\bgit\s+push\b(?=.*\s--force(?:-with-lease)?(?:\s|$|=))", normalized, re.IGNORECASE):
        return "Blocked destructive git command: force push."

    return None


def read_input() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


def log_block(command: str, project_path: str, reason: str) -> None:
    block_log = Path(os.environ.get("CLAUDE_BASH_GUARD_LOG", str(DEFAULT_BLOCK_LOG))).expanduser()
    block_log.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with block_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            separators=(",", ":"),
        )
    )


def safe_log_block(command: str, project_path: str, reason: str) -> str:
    try:
        log_block(command, project_path, reason)
    except OSError as exc:
        return f"{reason} Logging failed: {exc}"
    return reason


def main() -> int:
    payload = read_input()
    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    if not command:
        return 0

    reason = block_reason(command)
    if not reason:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    final_reason = safe_log_block(command, project_path, reason)
    deny(final_reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
