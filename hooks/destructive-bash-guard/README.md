# Destructive Bash Guard

Claude Code `PreToolUse` hook that blocks destructive Bash commands before execution.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-bash-guard/destructive_bash_guard.py ~/.claude/hooks/
python3 hooks/destructive-bash-guard/install_settings.py
```

Blocked attempts are appended to `~/.claude/hooks/blocked.log`.
For tests or custom deployments, set `CLAUDE_BASH_GUARD_LOG=/path/to/blocked.log`.
If the log path is not writable, the hook still denies the dangerous command and includes the logging error in the denial reason.

## What It Blocks

- `rm -rf` / `rm -fr` and split flag variants such as `rm -r -f`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Safe commands exit silently so Claude Code's normal permission flow continues.

## Hook Configuration

The installer merges this `PreToolUse` entry into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_bash_guard.py"
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python3 hooks/destructive-bash-guard/test_destructive_bash_guard.py
```
