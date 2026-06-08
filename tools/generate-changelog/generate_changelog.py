#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from pathlib import Path


SECTIONS = ("Added", "Fixed", "Changed", "Removed")


def run_git(repo: Path, args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def latest_tag(repo: Path) -> str | None:
    tag = run_git(repo, ["describe", "--tags", "--abbrev=0"], check=False)
    return tag or None


def commit_range(repo: Path, since: str | None) -> str:
    if since:
        return f"{since}..HEAD"
    tag = latest_tag(repo)
    return f"{tag}..HEAD" if tag else "HEAD"


def categorize(subject: str) -> str:
    lower = subject.lower()
    prefix = lower.split(":", 1)[0]

    if prefix in {"feat", "feature", "add", "added"}:
        return "Added"
    if prefix in {"fix", "bugfix", "hotfix"}:
        return "Fixed"
    if prefix in {"remove", "removed", "delete", "deleted"}:
        return "Removed"
    if any(word in lower for word in ("remove ", "delete ", "drop ")):
        return "Removed"
    if any(word in lower for word in ("fix ", "repair ", "resolve ")):
        return "Fixed"
    if any(word in lower for word in ("add ", "create ", "introduce ")):
        return "Added"
    return "Changed"


def read_commits(repo: Path, revision_range: str) -> list[tuple[str, str]]:
    fmt = "%h%x09%s"
    output = run_git(repo, ["log", "--reverse", f"--pretty=format:{fmt}", revision_range], check=False)
    commits: list[tuple[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\t")
        commits.append((sha.strip(), subject.strip()))
    return commits


def build_changelog(commits: list[tuple[str, str]], source_range: str) -> str:
    grouped: dict[str, list[str]] = {section: [] for section in SECTIONS}
    for sha, subject in commits:
        grouped[categorize(subject)].append(f"- {subject} ({sha})")

    today = dt.date.today().isoformat()
    lines = [
        "# Changelog",
        "",
        "All notable changes generated from git history.",
        "",
        f"## Unreleased - {today}",
        "",
        f"Source range: `{source_range}`",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for section in SECTIONS:
        lines.append(f"### {section}")
        lines.extend(grouped[section] or ["- No changes."])
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git commits.")
    parser.add_argument("--repo", default=".", help="Path to the git repository.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output changelog path.")
    parser.add_argument("--since", help="Tag or revision to use as the starting point.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    revision_range = commit_range(repo, args.since)
    commits = read_commits(repo, revision_range)
    changelog = build_changelog(commits, revision_range)

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.write_text(changelog, encoding="utf-8")

    print(f"Wrote {output}")
    print(f"Commits included: {len(commits)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

