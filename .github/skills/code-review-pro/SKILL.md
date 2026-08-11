---
name: code-review-pro
description: "Reusable findings-first code review workflow for Python and TypeScript/Node. Use when reviewing pull requests, diffs, or files for correctness, security, performance, maintainability, test gaps, and API compatibility."
argument-hint: "Provide scope, changed files or diff, and any risk focus (security/perf/api/tests)."
user-invocable: true
disable-model-invocation: false
---

# Code Review Pro

## What This Skill Does

Runs a consistent, reusable code review process optimized for risk detection across repositories.

Primary goals:
- Identify behavior regressions and bug risk first.
- Prioritize security and correctness over style.
- Provide actionable fixes with concrete evidence.
- Keep output concise and severity-ordered.

## When to Use

Use when:
- Reviewing a pull request, commit range, or selected files.
- Investigating potential regressions after refactors.
- Evaluating security, reliability, and API contract changes.
- Checking whether tests cover risky paths.

Do not use when:
- The task is only formatting or lint autofix.
- The user asks for architecture brainstorming without code.

## Review Procedure

1. Collect context.
- Identify changed files and critical execution paths.
- Identify boundaries: external APIs, data stores, auth, async flows.

2. Triage risk quickly.
- Look first for correctness, security, and data integrity issues.
- Then evaluate performance and maintainability impact.

3. Validate behavior changes.
- Compare old vs new behavior assumptions.
- Flag silent behavior drift, missing guards, and edge-case handling gaps.

4. Assess tests.
- Check whether changed behavior has tests.
- Flag missing coverage for failure paths and contract boundaries.

5. Report findings using the output contract below.

## Severity Rubric

Use the rubric in [severity-rubric](./references/severity-rubric.md).

Default ordering:
1. Critical
2. High
3. Medium
4. Low

## Language-Specific Guidance

- Python checklist: [python-review-checklist](./references/python-review-checklist.md)
- TypeScript/Node checklist: [typescript-node-review-checklist](./references/typescript-node-review-checklist.md)
- ReactJS checklist: [reactjs-review-checklist](./references/reactjs-review-checklist.md)
- Regression heuristics: [regression-risk-playbook](./references/regression-risk-playbook.md)

## Output Contract (Required)

Always present findings first.

Section 1: Findings (ordered by severity)
- **REQUIRED**: Every finding MUST include specific file path AND line number
- For each finding, include all required fields:
  - Severity: Critical | High | Medium | Low
  - **Location**: file path + line number(s) — REQUIRED FORMAT EXAMPLES:
    - `src/auth.ts:45` (recommended)
    - `lib/database.py (line 12)`
    - `config/settings.yml:8`
  - Category: Correctness | Security | Performance | Maintainability | Tests | API Compatibility
  - Evidence: what in code triggered the finding
  - Risk: user/system impact if not fixed
  - Fix: minimal concrete remediation

Recommended format (use this exactly):

| Severity | Location | Category | Finding | Risk | Fix |
|---|---|---|---|---|---|
| Critical | src/auth.ts:42 | Security | SQL injection in query builder | Database takeover | Use parameterized queries |
| High | lib/api.ts:87 | Correctness | Missing null check on user.id | NullPointerException | Add: if (!user?.id) return error |

**Critical Rule**: Location field must ALWAYS have the format `path/to/file.ext:LINE_NUMBER`. No exceptions.

Section 2: Open Questions / Assumptions
- Include only when evidence is incomplete.
- Keep each question specific and testable.

Section 3: Change Summary
- Short summary after findings.
- Mention overall risk posture and test confidence.

If no findings are discovered:
- State that explicitly: "No significant findings."
- Add residual risks or testing gaps still worth validating.

## Reviewer Defaults

- Prefer concrete behavior bugs over stylistic remarks.
- Do not block on low-priority nits when high-risk issues exist.
- Recommend smallest safe fix first.
- Call out missing or weak tests for non-trivial behavior changes.
