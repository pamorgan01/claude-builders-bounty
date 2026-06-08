# Generate Changelog

Create a structured `CHANGELOG.md` from commits since the last git tag.

## Setup

1. Copy this directory into a git repository.
2. Run `bash tools/generate-changelog/changelog.sh`.
3. Review the generated `CHANGELOG.md` and commit it.

## What It Does

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- Reads commits after that tag, or all commits if no tag exists.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep-a-Changelog style `CHANGELOG.md`.

## Optional Arguments

```bash
bash tools/generate-changelog/changelog.sh
python tools/generate-changelog/generate_changelog.py --output CHANGELOG.md
python tools/generate-changelog/generate_changelog.py --repo /path/to/repo
python tools/generate-changelog/generate_changelog.py --since v1.2.0
```
