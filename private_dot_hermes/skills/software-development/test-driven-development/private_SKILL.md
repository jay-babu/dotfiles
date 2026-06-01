---
name: test-driven-development
description: "TDD: enforce RED-GREEN-REFACTOR, tests before code."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [testing, tdd, development, quality, red-green-refactor]
    related_skills: [systematic-debugging, writing-plans, subagent-driven-development]
---

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

**Violating the letter of the rules is violating the spirit of the rules.**

## When to Use

**Always:**
- New features
- Bug fixes
- Refactoring
- Behavior changes

**Exceptions (ask the user first):**
- Throwaway prototypes
- Generated code
- Configuration files

Thinking "skip TDD just this once"? Stop. That's rationalization.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over.

**No exceptions:**
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete

Implement fresh from tests. Period.

## Red-Green-Refactor Cycle

### RED — Write Failing Test

Write one minimal test showing what should happen.

**Good test:**
```python
def test_retries_failed_operations_3_times():
    attempts = 0
    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception('fail')
        return 'success'

    result = retry_operation(operation)

    assert result == 'success'
    assert attempts == 3
```
Clear name, tests real behavior, one thing.

**Bad test:**
```python
def test_retry_works():
    mock = MagicMock()
    mock.side_effect = [Exception(), Exception(), 'success']
    result = retry_operation(mock)
    assert result == 'success'  # What about retry count? Timing?
```
Vague name, tests mock not real code.

**Requirements:**
- One behavior per test
- Clear descriptive name ("and" in name? Split it)
- Real code, not mocks (unless truly unavoidable)
- Name describes behavior, not implementation

### Verify RED — Watch It Fail

**MANDATORY. Never skip.**

```bash
# Use terminal tool to run the specific test
pytest tests/test_feature.py::test_specific_behavior -v
```

Confirm:
- Test fails (not errors from typos)
- Failure message is expected
- Fails because the feature is missing

**Test passes immediately?** You're testing existing behavior. Fix the test.

**Test errors?** Fix the error, re-run until it fails correctly.

### GREEN — Minimal Code

Write the simplest code to pass the test. Nothing more.

**Good:**
```python
def add(a, b):
    return a + b  # Nothing extra
```

**Bad:**
```python
def add(a, b):
    result = a + b
    logging.info(f"Adding {a} + {b} = {result}")  # Extra!
    return result
```

Don't add features, refactor other code, or "improve" beyond the test.

**Cheating is OK in GREEN:**
- Hardcode return values
- Copy-paste
- Duplicate code
- Skip edge cases

We'll fix it in REFACTOR.

### Verify GREEN — Watch It Pass

**MANDATORY.**

```bash
# Run the specific test
pytest tests/test_feature.py::test_specific_behavior -v

# Then run ALL tests to check for regressions
pytest tests/ -q
```

Confirm:
- Test passes
- Other tests still pass
- Output pristine (no errors, warnings)

**Test fails?** Fix the code, not the test.

**Other tests fail?** Fix regressions now.

### REFACTOR — Clean Up

After green only:
- Remove duplication
- Improve names
- Extract helpers
- Simplify expressions

Keep tests green throughout. Don't add behavior.

**If tests fail during refactor:** Undo immediately. Take smaller steps.

### Repeat

Next failing test for next behavior. One cycle at a time.

## Why Order Matters

**"I'll write tests after to verify it works"**

Tests written after code pass immediately. Passing immediately proves nothing:
- Might test the wrong thing
- Might test implementation, not behavior
- Might miss edge cases you forgot
- You never saw it catch the bug

Test-first forces you to see the test fail, proving it actually tests something.

**"I already manually tested all the edge cases"**

Manual testing is ad-hoc. You think you tested everything but:
- No record of what you tested
- Can't re-run when code changes
- Easy to forget cases under pressure
- "It worked when I tried it" ≠ comprehensive

Automated tests are systematic. They run the same way every time.

**"Deleting X hours of work is wasteful"**

Sunk cost fallacy. The time is already gone. Your choice now:
- Delete and rewrite with TDD (high confidence)
- Keep it and add tests after (low confidence, likely bugs)

The "waste" is keeping code you can't trust.

**"TDD is dogmatic, being pragmatic means adapting"**

TDD IS pragmatic:
- Finds bugs before commit (faster than debugging after)
- Prevents regressions (tests catch breaks immediately)
- Documents behavior (tests show how to use code)
- Enables refactoring (change freely, tests catch breaks)

"Pragmatic" shortcuts = debugging in production = slower.

**"Tests after achieve the same goals — it's spirit not ritual"**

No. Tests-after answer "What does this do?" Tests-first answer "What should this do?"

Tests-after are biased by your implementation. You test what you built, not what's required. Tests-first force edge case discovery before implementing.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Tests after achieve same goals" | Tests-after = "what does this do?" Tests-first = "what should this do?" |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost fallacy. Keeping unverified code is technical debt. |
| "Keep as reference, write tests first" | You'll adapt it. That's testing after. Delete means delete. |
| "Need to explore first" | Fine. Throw away exploration, start with TDD. |
| "Test hard = design unclear" | Listen to the test. Hard to test = hard to use. |
| "TDD will slow me down" | TDD faster than debugging. Pragmatic = test-first. |
| "Manual test faster" | Manual doesn't prove edge cases. You'll re-test every change. |
| "Existing code has no tests" | You're improving it. Add tests for the code you touch. |

## Red Flags — STOP and Start Over

If you catch yourself doing any of these, delete the code and restart with TDD:

- Code before test
- Test after implementation
- Test passes immediately on first run
- Can't explain why test failed
- Tests added "later"
- Rationalizing "just this once"
- "I already manually tested it"
- "Tests after achieve the same purpose"
- "Keep as reference" or "adapt existing code"
- "Already spent X hours, deleting is wasteful"
- "TDD is dogmatic, I'm being pragmatic"
- "This is different because..."

**All of these mean: Delete code. Start over with TDD.**

## Verification Checklist

Before marking work complete:

- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason (feature missing, not typo)
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, warnings)
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

Can't check all boxes? You skipped TDD. Start over.

## When Stuck

| Problem | Solution |
|---------|----------|
| Don't know how to test | Write the wished-for API. Write the assertion first. Ask the user. |
| Test too complicated | Design too complicated. Simplify the interface. |
| Must mock everything | Code too coupled. Use dependency injection. |
| Test setup huge | Extract helpers. Still complex? Simplify the design. |

## Hermes Agent Integration

### Running Tests

Use the `terminal` tool to run tests at each step:

```python
# RED — verify failure
terminal("pytest tests/test_feature.py::test_name -v")

# GREEN — verify pass
terminal("pytest tests/test_feature.py::test_name -v")

# Full suite — verify no regressions
terminal("pytest tests/ -q")
```

### With delegate_task

When dispatching subagents for implementation, enforce TDD in the goal:

```python
delegate_task(
    goal="Implement [feature] using strict TDD",
    context="""
    Follow test-driven-development skill:
    1. Write failing test FIRST
    2. Run test to verify it fails
    3. Write minimal code to pass
    4. Run test to verify it passes
    5. Refactor if needed
    6. Commit

    Project test command: pytest tests/ -q
    Project structure: [describe relevant files]
    """,
    toolsets=['terminal', 'file']
)
```

### With systematic-debugging

Bug found? Write failing test reproducing it. Follow TDD cycle. The test proves the fix and prevents regression.

Never fix bugs without a test.

## Testing Anti-Patterns

### Feature loop closure

For every new feature, close the full loop without waiting for the user to spell out obvious downstream uses. Ask: "What makes this useful in production, and where is it consumed or observed?" Then inspect and test that path.

Examples:
- Metadata/correlation IDs must be emitted, received, propagated, and visible in logs/traces/audit data operators actually use.
- New config/options must be wired into the code path that consumes them, not merely added to a schema or UI.
- New UI controls must affect requests, server parsing, persisted/query behavior, rendered state, and pagination/navigation URLs where applicable.
- New API fields must be produced and consumed by callers or documented as intentionally write-only/read-only.

If the implementation creates data that no one reads, logs, renders, stores, or acts on, the feature is incomplete. Prefer exact affected route/path tests over generic dummy-handler tests, and mention any intentionally unverified loop in the PR summary.

- **Testing mock behavior instead of real behavior** — mocks should verify interactions, not replace the system under test
- **Testing implementation details** — test behavior/results, not internal method calls
- **Happy path only** — always test edge cases, errors, and boundaries
- **Brittle tests** — tests should verify behavior, not structure; refactoring shouldn't break them
- **Piecemeal field assertions when a full expected object is clearer** — if the expected struct/object is reasonably small and stable, assert the full object so diffs catch accidental shape changes. Keep lookup/existence assertions separate (for example `found == true`), then compare the retrieved object to an explicit expected value. In Go, prefer `cmp.Diff(got, want, opts...)` or the project test helper rather than many `MustEqual(field, value)` calls.

### Frontend navigation links and route params

For UI work that adds a navigation link/button, write a focused component test before implementation that proves the user-facing contract:

- Query by accessible role/name, not CSS class or component internals: `getByRole('link', { name: /messages/i })`.
- Assert the exact `href`, including route params derived from the same context/provider the real page uses.
- Add a negative test for the gating condition so the link is absent when the required data/permission is missing.
- If the target is another route on the same app/host, prefer an environment-relative URL (for example `/v2/${entity.id}/messages/`) unless the requirement explicitly needs a cross-origin absolute URL. This keeps local/dev/gamma/prod on their current host.
- Gate on the most direct available DTO/API field that represents the requirement, and document when a more ideal source does not exist.

When inserting a link into a tabbed/sidebar navigation component, add regression tests for tab-state isolation, not just the link href:

- Link-only entries should be asserted as `role="link"` and explicitly not as `role="tab"`.
- Clicking the link-only entry must not call the tab change path or mutate persisted tab query params such as `?tab=messages`.
- A URL containing the link-only id as a tab param should fall back to the first real tab and render non-empty content.
- The component type/API should make illegal states hard to express: prefer a discriminated union where tab items require `content` and link items require `href` and cannot provide `content: null`.

### Date/time and UI preset behavior

For frontend behavior that computes date ranges, preset options, interval defaults, labels, or query boundaries, prefer extracting the calculation into a pure helper and testing that helper directly with an injected fixed `today`/`now` value. Do not make the only regression coverage a component-render test that depends on the real clock. Write the failing test against the desired public helper/API first, verify it fails because the helper/export or behavior is missing, then wire the UI to the helper. Assert both preset labels and exact local-date ranges where the UX depends on calendar boundaries (for example month intervals should start at `startOfMonth(subMonths(today, 1))`, not just “some date in the prior month”). Keep a separate query-boundary test for start-of-day/end-of-day serialization so interval presets do not accidentally change API range semantics.

### Server-rendered filters, search, and pagination

For server-rendered list pages with filters/search, write tests at the boundary where request query parameters become model/query arguments and rendered links. Cover the whole feature, not just the visible control:

- URL/query parsing: default behavior, explicit mode values, and invalid/missing params.
- Search semantics: exact expected wildcard/pattern construction for contains / starts-with / ends-with / exact, including the default mode.
- Ordering semantics: if the requirement says “latest matching hit,” test that filtering happens before grouping/picking the latest row, not after returning each parent’s overall latest row.
- URL preservation: active filters must survive the page URL, HTMX/content URL, and pagination/infinite-scroll URL.
- Rendered state: assert the selected pill/input values are present so the UI reflects the server state after navigation.

Keep these as targeted tests around existing handlers/templates/model calls before broad integration suites; broader suites may be slow or require external services, but targeted coverage should still prove the user-facing contract.

### Request/correlation ID headers

When adding a client-generated request/correlation ID header, test the full contract across both edges:

- Client emission: prove every request gets a fresh value with the required prefix/format. Use an injectable ID factory (for example `requestIdFactory`) so tests are deterministic instead of mocking the ID library globally.
- Server receipt: inspect the actual route registration/middleware chain for the affected endpoint. Do not assume a global logging middleware runs just because it exists; server-rendered or manually registered routes may bypass shared middleware slices.
- Logging/context propagation: add or verify a receive-side test that sets the header and asserts the request ID is placed in context and/or included in the request log fields expected by operators. Prefer testing the exact user-cited route/path, not only a generic dummy handler, so route-registration gaps are caught.
- Consistent behavior without edge-case coupling: when a web/HTMX route should behave like regular API requests, first inspect whether the shared middleware naturally applies to that route. If it does not, do not exploit unrelated router edge cases (for example changing `routes == 0` behavior or wrapping the full composed router just to reuse a helper). Prefer an explicit, local wrapper at the affected route group, or extract a small shared helper with a clear name and direct call site.
- Simplicity over clever reuse: avoid broad middleware moves that require static/file-server carve-outs or nil/zero-value fallbacks just to preserve old behavior. Carve-outs are a signal that the abstraction boundary is wrong. Add tests proving the exact affected route logs/propagates the ID and unaffected static routes remain untouched.
- Dependency-injection expectations: do not add nil fallbacks for dependencies supplied by Fx/Uber DI just to make router construction optional; DI should fail startup when required dependencies are missing. Tests should construct the required dependencies explicitly.
- Fallback behavior: if the server generates an ID when the header is missing, cover that path separately from the client-supplied header path.

A PR that only proves the browser sends `X-Request-ID` may still fail the user-facing observability requirement if the receiving route does not pass through the logger that reads that header.

### Go object-comparison pitfalls

When comparing SDK or generated structs, `go-cmp` may panic on unexported internal fields. Use an explicit ignore option for those types instead of falling back to many field-level assertions:

```go
want := snstypes.PublishBatchRequestEntry{
    Id:      new("1"),
    Message: new(expectedMessage),
    MessageAttributes: map[string]snstypes.MessageAttributeValue{
        "action": {DataType: new("String"), StringValue: new("UPDATE")},
    },
}
if diff := cmp.Diff(got, want, cmpopts.IgnoreUnexported(
    snstypes.PublishBatchRequestEntry{},
    snstypes.MessageAttributeValue{},
)); diff != "" {
    t.Fatalf("request entry mismatch (-got +want):\n%s", diff)
}
```

Prefer literal expected values over calling the same production helper used to produce `got`; otherwise the test may mirror the implementation and miss regressions. If the project lints against AWS SDK pointer helpers, use Go `new(expr)` instead of `aws.String(...)` in expected structs.

For a fuller Go example with AWS SNS batch request entries, unexported smithy fields, and stringified routing attributes, see `references/go-full-object-assertions.md`.

## Final Rule

```
Production code → test exists and failed first
Otherwise → not TDD
```

No exceptions without the user's explicit permission.
