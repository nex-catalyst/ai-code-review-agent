# ReactJS Review Checklist

## Correctness

- Validate state transitions and avoid stale closure bugs in effects and callbacks.
- Ensure dependency arrays for useEffect, useMemo, and useCallback are complete and intentional.
- Confirm controlled vs uncontrolled input behavior is consistent.
- Check key usage in lists for stability and identity correctness.
- Verify error and loading states for async UI flows.

## Security

- Flag unsafe use of dangerouslySetInnerHTML and untrusted HTML rendering.
- Validate route guards and client-side permission checks are not treated as server auth.
- Ensure secrets and tokens are never exposed to the client bundle or logs.
- Check URL/query/param handling for injection and open redirect risks.

## Performance

- Detect unnecessary re-renders from unstable props, inline objects, or function recreation.
- Validate memoization strategy (React.memo, useMemo, useCallback) only where it helps.
- Check expensive computations and large list rendering; recommend virtualization when needed.
- Confirm network requests are deduplicated/cancelled on unmount or parameter changes.

## Maintainability

- Prefer composable components over monolithic render logic.
- Check custom hooks for clear contracts and side-effect boundaries.
- Validate prop naming and component API consistency.
- Flag duplicated UI/business logic that should be shared.

## Accessibility

- Ensure semantic HTML is used before ARIA fallbacks.
- Check keyboard navigation, focus management, and visible focus states.
- Validate form labels, error messaging, and announced status updates.
- Confirm color contrast and non-color affordances for critical feedback.

## Tests

- Ensure changed UI behavior has interaction tests, not only snapshot tests.
- Add regression tests for effect timing, loading/error branches, and edge states.
- Verify accessibility assertions for roles, names, and keyboard usage.
- Check integration coverage for route-level and async data flows.
