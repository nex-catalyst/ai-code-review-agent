# Python Review Checklist

## Correctness

- Validate None handling, optional values, and narrowing assumptions.
- Check exception handling: avoid broad except that hides failures.
- Verify async/await usage and cancellation safety.
- Confirm timezone/date arithmetic and serialization correctness.
- Validate dict/list mutation side effects across call boundaries.

## Security

- Ensure no hardcoded secrets or token leakage in logs.
- Validate authz checks happen at the correct boundary.
- Validate input parsing and deserialization safety.
- Check subprocess, shell, or file-path handling for injection risks.

## Performance

- Detect repeated remote/database calls in loops.
- Watch for large in-memory copies and unbounded accumulation.
- Check serialization/deserialization hot paths.
- Verify caching invalidation and stale-read behavior.

## Maintainability

- Prefer clear boundaries over hidden global state.
- Check function/class responsibilities for cohesion.
- Flag fragile implicit contracts and magic values.
- Ensure errors include actionable context.

## Tests

- Confirm changed logic has tests for success and failure paths.
- Add edge-case tests for null/empty/invalid inputs.
- Validate async behavior and timeout/retry paths.
- Ensure contract tests exist for external integrations.
