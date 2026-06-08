#!/usr/bin/env python3
"""Install the Destructive Bash Guard into ~/.claude/settings.json."""

from __future__ import annotations

import json
from pathlib import Path


SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "python3 ~/.claude/hooks/destructive_bash_guard.py"


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def main() -> int:
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": HOOK_COMMAND,
            }
        ],
    }

    if entry not in pre_tool_use:
        pre_tool_use.append(entry)

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed Destructive Bash Guard in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
