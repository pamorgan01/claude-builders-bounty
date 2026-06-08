# Weekly Dev Summary

n8n workflow that collects one week of GitHub activity, asks Claude for a narrative summary, and posts it to Discord.

## Setup

1. Import `weekly-dev-summary.n8n.json` into n8n.
2. Set environment variables: `GITHUB_OWNER`, `GITHUB_REPO`, `SUMMARY_LANGUAGE`, `DISCORD_WEBHOOK_URL`, `ANTHROPIC_API_KEY`.
3. Open the `Config` node and confirm the default values match your repo and language.
4. Execute the workflow once manually, then enable it for the weekly Friday schedule.

## Variables

- `GITHUB_OWNER`: repository owner, for example `anthropics`.
- `GITHUB_REPO`: repository name, for example `anthropic-sdk-python`.
- `SUMMARY_LANGUAGE`: `EN` or `FR`.
- `DISCORD_WEBHOOK_URL`: Discord webhook destination.
- `ANTHROPIC_API_KEY`: Claude API key used by the HTTP request node.

## What It Does

- Runs weekly on Friday at 17:00.
- Fetches commits, closed issues, and merged pull requests from the GitHub API.
- Calls Claude with model `claude-sonnet-4-20250514`.
- Posts a narrative weekly summary to Discord.

## Validation

The workflow JSON was checked for valid JSON structure locally. A real n8n execution screenshot is still required before final bounty submission.
