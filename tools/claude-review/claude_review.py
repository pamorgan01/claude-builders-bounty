#!/usr/bin/env python3
"""Generate a structured Markdown PR review from a GitHub PR diff."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$")


@dataclass
class FileChange:
    path: str
    added: int = 0
    removed: int = 0
    hunks: int = 0


def pr_diff_url(pr_url: str) -> str:
    match = PR_RE.match(pr_url.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def fetch_diff(pr_url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(
        pr_diff_url(pr_url),
        headers={"User-Agent": "claude-review-cli", "Accept": "text/plain"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_diff(diff: str) -> list[FileChange]:
    files: list[FileChange] = []
    current: FileChange | None = None

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            path = parts[-1][2:] if len(parts) >= 4 and parts[-1].startswith("b/") else parts[-1]
            current = FileChange(path=path)
            files.append(current)
            continue
        if current is None:
            continue
        if line.startswith("@@"):
            current.hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            current.added += 1
        elif line.startswith("-") and not line.startswith("---"):
            current.removed += 1

    return files


def classify_area(path: str) -> str:
    lower = path.lower()
    if any(part in lower for part in ("test", "spec", "__tests__")):
        return "tests"
    if lower.endswith((".md", ".rst", ".txt")):
        return "documentation"
    if any(part in lower for part in ("workflow", ".github", "ci", "action")):
        return "automation"
    if lower.endswith((".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb")):
        return "application code"
    if lower.endswith((".json", ".yaml", ".yml", ".toml", ".ini")):
        return "configuration"
    return "project files"


def summarize(files: list[FileChange]) -> str:
    total_added = sum(file.added for file in files)
    total_removed = sum(file.removed for file in files)
    areas = sorted({classify_area(file.path) for file in files})
    largest = sorted(files, key=lambda file: file.added + file.removed, reverse=True)[:3]
    largest_paths = ", ".join(file.path for file in largest) if largest else "no files"

    return (
        f"This PR changes {len(files)} file(s), with {total_added} added line(s) and "
        f"{total_removed} removed line(s). The main touched areas are {', '.join(areas) or 'unknown'}, "
        f"with most activity in {largest_paths}."
    )


def risks(files: list[FileChange], diff: str) -> list[str]:
    result: list[str] = []
    total_changed = sum(file.added + file.removed for file in files)
    paths = [file.path.lower() for file in files]
    lower_diff = diff.lower()

    if total_changed > 500:
        result.append("Large diff size may hide behavioral regressions; review high-churn files carefully.")
    if any(path.endswith((".json", ".yaml", ".yml", ".toml")) for path in paths):
        result.append("Configuration changes can affect deployment or tooling behavior across environments.")
    if any("workflow" in path or ".github" in path for path in paths):
        result.append("Automation changes can alter CI permissions, triggers, or release behavior.")
    if "delete from" in lower_diff or "drop table" in lower_diff or "truncate" in lower_diff:
        result.append("SQL-like destructive operations appear in the diff; confirm they are guarded and reversible.")
    if any(path.endswith((".py", ".js", ".ts", ".tsx", ".jsx")) for path in paths) and not any(
        "test" in path or "spec" in path for path in paths
    ):
        result.append("Application-code changes do not appear to include matching test updates.")
    if not result:
        result.append("No obvious high-risk pattern was detected from the diff shape alone.")
    return result


def suggestions(files: list[FileChange]) -> list[str]:
    result = [
        "Confirm the changed files match the issue scope and do not include unrelated cleanup.",
        "Run the repository's normal test, lint, or validation command before merge.",
    ]
    if any(classify_area(file.path) == "documentation" for file in files):
        result.append("Check rendered Markdown for broken links, stale paths, or formatting issues.")
    if any(classify_area(file.path) == "automation" for file in files):
        result.append("Review workflow permissions and trigger conditions explicitly.")
    return result


def confidence(files: list[FileChange], diff: str) -> str:
    total_changed = sum(file.added + file.removed for file in files)
    has_tests = any("test" in file.path.lower() or "spec" in file.path.lower() for file in files)
    if not files or total_changed > 900:
        return "Low"
    if total_changed > 300 and not has_tests:
        return "Medium"
    return "High"


def render_review(pr_url: str | None, diff: str) -> str:
    files = parse_diff(diff)
    header = f" for `{pr_url}`" if pr_url else ""
    risk_items = "\n".join(f"- {item}" for item in risks(files, diff))
    suggestion_items = "\n".join(f"- {item}" for item in suggestions(files))

    return "\n".join(
        [
            f"## Claude Review{header}",
            "",
            "### Summary",
            summarize(files),
            "",
            "### Identified Risks",
            risk_items,
            "",
            "### Improvement Suggestions",
            suggestion_items,
            "",
            f"### Confidence Score: {confidence(files, diff)}",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a structured PR review comment.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    source.add_argument("--diff-file", help="Path to a local unified diff file")
    args = parser.parse_args()

    if args.pr:
        diff = fetch_diff(args.pr)
        pr_url = args.pr
    else:
        diff = Path(args.diff_file).read_text(encoding="utf-8")
        pr_url = None

    sys.stdout.write(render_review(pr_url, diff))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
