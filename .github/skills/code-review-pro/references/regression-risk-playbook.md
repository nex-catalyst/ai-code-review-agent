# Regression Risk Playbook

## High-Signal Regression Patterns

- Silent defaults changed (config/env fallback behavior drift).
- Changed ordering assumptions (sorting, dedupe, precedence).
- Boundary behavior changed (timeouts, retries, pagination).
- Serialization shape changes (field names/types/nullability).
- Error handling changed from fail-fast to fail-open.

## Compatibility Hotspots

- Public API request/response contracts.
- Database schema assumptions and migration ordering.
- Authentication and authorization flow transitions.
- Event/message payload versions and consumers.

## Fast Validation Questions

- What user-visible behavior changed?
- Which consumers depend on old behavior?
- Are rollback and feature flags available?
- Do tests prove old critical behavior still holds?

## Evidence Checklist for Findings

For each regression-risk finding include:
- Old expectation (or likely consumer assumption).
- New behavior introduced by change.
- Impacted paths/consumers.
- Minimal safe remediation.

## Test Gap Heuristics

Flag test risk when:
- A boundary contract changed without contract tests.
- Error paths changed without negative tests.
- Retry/timeout logic changed without deterministic tests.
- Security-sensitive paths changed without authz tests.
