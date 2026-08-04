# TypeScript and Node Review Checklist

## Correctness

- Validate types at boundaries, not only internal inference.
- Check promise chains for missed await or unhandled rejection.
- Ensure nullable/undefined values are handled explicitly.
- Validate runtime schema checks for untrusted inputs.
- Confirm module side effects and initialization order assumptions.

## Security

- Check auth and permission checks for each route/action.
- Validate input sanitization and output encoding.
- Flag unsafe dynamic eval, path joins, and template injection vectors.
- Ensure secrets are never logged or returned in responses.

## Performance

- Detect N+1 patterns or repeated network calls.
- Check synchronous CPU-heavy work on event loop hot paths.
- Validate pagination, batching, and backpressure behavior.
- Confirm caching strategy and stale data risks.

## Maintainability

- Check API types match runtime behavior.
- Prefer explicit error propagation over silent fallback.
- Flag deeply nested conditionals without decomposition.
- Ensure config defaults are safe and discoverable.

## Tests

- Ensure changed routes/services have behavior tests.
- Add regression tests for schema and contract changes.
- Verify error path tests, not only happy paths.
- Check compatibility tests for external API payloads.
