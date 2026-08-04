# ai-code-review-agent

Central repository for shared code review skill and reusable PR review automation.

## What This Repository Owns

- Shared skill content:
  - `.github/skills/code-review-pro/SKILL.md`
  - `.github/skills/code-review-pro/references/*`
- Reusable workflow used by product repos:
  - `.github/workflows/reusable-pr-review.yml`
- PR review engine:
  - `scripts/review_pr.py`
- Local developer bootstrap:
  - `scripts/install_local_skill.sh`

## Product Repo Integration (Minimal)

Each product repository needs only one tiny caller workflow file that triggers on PRs and calls this reusable workflow.

## Required Secrets in Caller Repository

- `CENTRAL_REVIEW_GH_TOKEN`
- `CENTRAL_REVIEW_LLM_API_KEY`

## Local Skill Usage

From this repository root:

```bash
./scripts/install_local_skill.sh install
```

Then open a new Copilot Chat session and use `/code-review-pro`.

## Notes

- Default review target branch is `develop`.
- Review comments are deduplicated by PR head SHA marker.
- Set `dry_run: true` in caller workflow inputs to test without posting comments.
