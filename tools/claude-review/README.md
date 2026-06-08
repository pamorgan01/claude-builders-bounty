# Claude Review

Structured PR review CLI for Claude Code workflows.

## Setup

```bash
tools/claude-review/claude-review --pr https://github.com/owner/repo/pull/123
```

Optionally copy `tools/claude-review/claude-review` onto your PATH as `claude-review`.

## Usage

```bash
tools/claude-review/claude-review --pr https://github.com/owner/repo/pull/123
tools/claude-review/claude-review --diff-file pr.diff
```

The command prints a structured Markdown review comment with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score

## Notes

- Uses only the Python standard library.
- Fetches public GitHub PR diffs through the `.diff` endpoint.
- Falls back to `--diff-file` for private repos, CI artifacts, or offline testing.
- The output is deterministic and ready to paste into a GitHub PR comment.
