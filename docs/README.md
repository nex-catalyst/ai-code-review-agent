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

- Default review target branch is any branch (`target_base_branch` defaults to empty and applies no base-branch filter).
- Default review scope is `latest_commit`.
- Default comment mode is `inline_only` (GitHub PR review line comments).
- `llm_model` and `llm_base_url` are centralized in the reusable workflow and are not caller workflow inputs.
- Reusable review job runs only for internal pull requests (head repository must match base repository); fork-origin PRs are skipped.
- Moderate cleanup is enabled by default: outdated bot comments are minimized (not deleted) when no longer relevant in newer commits.
- Set `MODERATE_CLEANUP_ENABLED=false` to disable auto-minimization.
- Review comments are deduplicated at `(file, line, body)`.
- Reviewer identity is provided by `CENTRAL_REVIEW_GH_TOKEN`.
- Optional `expected_reviewer_login` input enforces token identity before posting.
- Set `dry_run: true` in caller workflow inputs to test without posting comments.
