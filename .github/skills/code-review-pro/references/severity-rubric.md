# Severity Rubric

## Critical

Use when impact is immediate and severe.

Examples:
- Authentication/authorization bypass.
- Data corruption or irreversible data loss path.
- Remote code execution or secret exposure.
- Hard crash in core runtime path with no mitigation.

## High

Use when impact is significant but not catastrophic.

Examples:
- Incorrect business logic causing wrong results in common paths.
- API contract break likely to fail consumers.
- Missing validation enabling privilege escalation conditions.
- Unbounded resource growth in production path.

## Medium

Use when issue is real but localized or conditional.

Examples:
- Edge-case bug behind uncommon inputs.
- Performance degradation under moderate scale.
- Test gaps around changed behavior with moderate risk.
- Maintainability choices likely to cause future defects.

## Low

Use when impact is minor or mostly cosmetic.

Examples:
- Minor readability problems.
- Non-blocking naming inconsistencies.
- Micro-optimizations without measured impact.

## Tie-Break Rules

If uncertain between two levels:
- Raise severity when exploitability or blast radius is broad.
- Raise severity when rollback is hard.
- Lower severity when safe guards or compensating controls exist.

## Reporting Rules

Every finding should include:
- Severity
- Location (file and line)
- Evidence
- User/system risk
- Minimal fix