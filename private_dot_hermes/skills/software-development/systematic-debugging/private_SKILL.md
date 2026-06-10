---
name: systematic-debugging
description: "4-phase root cause debugging: understand bugs before fixing."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, writing-plans, subagent-driven-development]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely
- Note line numbers, file paths, error codes

**Action:** Use `read_file` on the relevant source files. Use `search_files` to find the error string in the codebase.

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If not reproducible → gather more data, don't guess

**Action:** Use the `terminal` tool to run the failing test or trigger the bug:

```bash
# Run specific failing test
pytest tests/test_module.py::test_name -v

# Run with verbose output
pytest tests/test_module.py -v --tb=long
```

### 3. Check Recent Changes

- What changed that could cause this?
- Git diff, recent commits
- New dependencies, config changes

**Action:**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems

**Shell startup / prompt issues:** before proposing fixes, distinguish login vs interactive shell behavior and inspect initialization order. Useful probes include `getent passwd $USER`, `/etc/shells`, `~/.profile`, shell-specific config such as `~/.config/fish/config.fish`, and clean-environment reproductions like `env -i HOME=$HOME USER=$USER LOGNAME=$USER TERM=xterm-256color PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin fish -lic '...'`. For prompt-manager failures, check whether the prompt binary is available before version-manager activation (e.g. Starship installed by mise but initialized before `mise activate`). Verify by inspecting the loaded prompt function or equivalent (`functions fish_prompt` for fish) rather than relying only on visual prompt text.

**WHEN system has multiple components (API  service  database, CI  build  deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**

For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify the failing component.
THEN investigate that specific component.

**Webhook/public-ingress incidents:** separate local service health from public ingress before changing app/webhook code. Check local listener/health, public `/health`, reverse proxy/systemd status, and use a safe unsigned webhook POST where `401 Invalid signature` confirms routing reaches validation without processing an event. For Caddy/systemd/mise path failures and chezmoi hardening, see `references/hermes-webhook-ingress-outages.md`.

**Webhook-to-chat threading regressions:** if webhook events used to stay in one Slack/chat thread but now create top-level messages, distinguish delivery target selection from thread metadata. `deliver: slack` chooses Slack; it does not provide a `thread_ts`. Inspect route config, platform adapter metadata handling, and any durable external-object → chat-thread mapping. For PagerDuty and similar systems, key mappings by the stable parent object ID, not note/event IDs. See `references/webhook-slack-threading-regressions.md`.

**Hermes auxiliary/compression failures:** when the same warning appears across multiple Slack/webhook threads, treat it as a shared runtime/config issue before investigating individual threads. Correlate `agent.log` compression lifecycle lines (`context compression started`, `Auxiliary compression: using ...`, timeout/connection errors, fallback exhaustion, `context compression done`) with `~/.hermes/config.yaml` auxiliary settings. A completed compression can still mean summary generation failed and Hermes inserted a static fallback marker. See `references/hermes-auxiliary-compression-failures.md`.

### 5. Trace Data Flow

**WHEN error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### Phase 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypothesis formed

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

### 1. Find Working Examples

- Locate similar working code in the same codebase
- What works that's similar to what's broken?

**Action:** Use `search_files` to find comparable patterns:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. Compare Against References

- If implementing a pattern, read the reference implementation COMPLETELY
- Don't skim — read every line
- Understand the pattern fully before applying

### 3. Identify Differences

- What's different between working and broken?
- List every difference, however small
- Don't assume "that can't matter"

### 4. Understand Dependencies

- What other components does this need?
- What settings, config, environment?
- What assumptions does it make?

### 5. Correlate Resource-Exhaustion Logs

For incidents like DB pool starvation, connection timeouts, queue backlogs, or cascading 5xxs, do not assume the endpoint that emitted the final error is the root cause. Correlate error timestamps with nearby request-start/request-id logs and aggregate by path and query shape. A burst of one pathological request shape can make many unrelated endpoints fail secondarily; target the dominant upstream trigger, not the noisy downstream victims.

---

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form a Single Hypothesis

- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

### 2. Test Minimally

- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

### 3. Verify Before Continuing

- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

---

## Phase 4: Implementation

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case

- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use the `test-driven-development` skill

### 2. Implement Single Fix

- Address the root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

If an integration test fails before the test body runs because environment infrastructure cannot start (for example, Testcontainers migration/helper container timeout), classify it as a verification environment blocker rather than a product regression. Change strategy: inspect container/logs or use compile/unit tests plus remote CI status, and state precisely that the local test was blocked before execution.

For JVM/Kotlin integration tests that use Testcontainers, debug in layers: Docker client/API compatibility, service image/runtime behavior, migration/submodule setup, fixture/schema drift, and application config/DI. Read the generated `build/test-results/test/TEST-...xml` after each run because Gradle console output often truncates the nested cause. Avoid `latest` images and `withReuse(true)` while debugging, initialize schema submodules before running migrations, and do not advance a schema submodule pointer unless the parent repo's generated clients/types are updated too. See `references/testcontainers-kotlin-integration-debugging.md` for the detailed pattern.

For Go/Bob eager-loaded relationship mapping, keep responsibilities separated: the query/parent boundary decides what to preload based on API expands or sort needs, while nested response mappers should reflect loaded data. If a mapper receives a Bob model with `model.R.<Relation> != nil`, prefer mapping that relation directly instead of redundantly re-checking the original expand flag; otherwise sorted/preloaded relations can be silently dropped from the response.

For Go/Bob codegen/template debugging, inspect the consuming repo's Bob config before concluding a generated compile failure is a usage bug. Generated loader code must account for `relationship_codegen` filtering and `model_package_split` component packages: a target table can exist as a model but have no generated recursive `SelectThenLoad.<Target>` field, and a target with a loader may live in another component package. Terminal relationships should emit plain relation loads plus nested-child validation instead of blindly recursing. See `references/bob-codegen-expand-loader-debugging.md`.

For TypeSpec/OpenAPI read-model debugging, audit schema optionality against the concrete source model before adding pointer helpers in mappers. `@visibility(Lifecycle.Read)` does not make a field optional; if Bob/DB returns `int64` or `time.Time`, the TypeSpec read field should be `field: T`, not `field?: T`, so generated Go read models use concrete values. Regenerate and inspect the generated read structs, then map concrete fields directly and use `.Ptr()` only for nullable wrappers. See `references/typespec-read-model-nullability.md`.

For production incidents and user-reported bugs, automated tests are necessary but may not be sufficient. Also re-run the original dynamic reproduction path after the fix:

- API/backend/non-UI bug: repeat the failing API call, CLI command, integration script, or local service request and capture the before/after output.
- UI/interaction bug: repeat the browser/UI steps with Playwright/browser automation or manual click evidence when available. If an authenticated preview blocks direct verification but the behavior lives in a reusable component, build a temporary local probe using the real component and app CSS, browser-check DOM/computed styles/state transitions, then remove the probe before committing. See `references/authenticated-ui-local-component-probes.md`.
- Do not treat "disable the crashing feature" as a root-cause fix unless the user explicitly chooses that product tradeoff. For incident fixes, first ask/answer whether a package upgrade, library bug workaround, app-logic bug, or configuration change preserves the feature while avoiding the crash. If a temporary mitigation is unavoidable, label it as mitigation and continue root-cause investigation.
- Observability-noise incident: verify both behavior and instrumentation. If the incident is caused by a synthetic Sentry/PostHog exception during an expected fallback/loading state, add a regression test that preserves caller-visible fallback/error state while asserting the exception/analytics side effect is not emitted. See `references/mobile-sentry-noise-incidents.md` for the React Native/Expo mobile pattern and local Jest pitfalls.
- Mobile native SDK crash incident: if a React Native/Expo incident surfaces native Android/iOS stack symbols from an SDK feature (for example Sentry replay + Skia/Bitmap/PixelCopy), inspect SDK changelogs/types/native dependency wiring and prefer same-major upgrades plus documented configuration workarounds that preserve feature behavior. Keep the implementation narrow: only extract helpers or add parameters when they are necessary for the fix/test seam, and remove unused pass-through arguments before pushing. See `references/mobile-native-sdk-crash-incidents.md` for the Sentry replay Android pattern.
- Cross-repo business-rule audit: distinguish "field exists/syncs" from "business logic uses it." Trace the chosen value across DB migrations, generated API/types, frontend local/offline paths, service contracts, persistence payloads, and reports. If an API/service model accepts only a generic field (for example `cost`) and lacks the selector/config fields, the caller must preselect the effective value before that boundary. For Transformity POS cost-source/minimum-price/invoice self-managed-cost patterns, see `references/transformity-pos-cost-source-audits.md`.
- Report/API date-range bugs: distinguish filtering from grouping/bucket labeling before fixing. For selected-range charts, verify whether `interval=month` only labels buckets while the backend still filters exact `start`/`end`; if so, fix the frontend request builder so bucket interval does not expand selected day bounds. See `references/report-date-range-grouping-bugs.md`.
- Large HTML/HTMX payload bugs: first determine whether the endpoint is a compact API or a server-rendered partial. Trace handler → loader → SQL → template, quantify row counts and rendered text lengths with read-only aggregate probes, and check for unbounded list rendering where `row_count × repeated HTML/HTMX attributes` dominates payload size. Distinguish decoded response size from compressed transfer size. See `references/large-htmx-payload-investigations.md`.
- Latest-distinct list performance bugs: when a `LIMIT 50` endpoint is still slow, check whether SQL ranks/dedupes all child rows before applying the final limit (for example latest message per customer/conversation). Compare recent query shapes, test CTE materialization only as a narrow regression fix, and prefer newest-first indexed scans plus application-side dedupe when the user wants low-maintenance scaling without summary tables. See `references/latest-distinct-list-query-performance.md`.
- Conditional latest-message list optimization: when the expensive part is joining heavyweight message/body rows before a small page limit, rank lightweight link rows first and fetch bodies only after limiting. Preserve body-search semantics by keeping pre-rank body filtering only when a body-search parameter is active. If the user rejects adding a new sqlc query/method, rewrite the existing query in place with the same name, params, and row shape. See `references/conditional-latest-message-list-query.md`.
- Postgres SQL performance regressions after CTE/query-shape refactors: compare the current query to the last known-fast SQL, run read-only `EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT JSON)` on representative production parameters, and check whether a CTE stopped being referenced multiple times, causing Postgres to inline it and choose nested-loop amplification. Test `AS MATERIALIZED` as a minimal hypothesis before proposing indexes or broader rewrites. See `references/postgres-cte-materialization-regressions.md`.
- List/filter preview bugs: when a filter or tab changes which underlying row is relevant (latest inbound reply, latest failure, newest matching event), verify that the displayed preview fields come from that same row, not from the latest row overall. Trace template → handler/loader → SQL projection; aggregation such as `MAX(timestamp)` often loses the matching body/direction. See `references/list-filter-preview-bugs.md`.
- Phone-number search bugs: when bare digits match but pasted formats like Slack `tel:` links, `+1 (###) ###-####`, or hyphenated numbers do not, preserve the raw text predicate and add a separate normalized-digits predicate/search helper. Normalize both the user input and stored body representation, and test helper plus handler/query params. See `references/phone-number-search-normalization.md`.
- Message-list/latest-conversation query performance: for Postgres CTE-heavy “latest message per customer” lists, compare recent query shapes and `EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT JSON)` plans. A final `LIMIT` may not reduce upstream window/sort work, and removing a second CTE reference can make Postgres inline a CTE instead of materializing it, causing pathological nested-loop plans. Test `AS MATERIALIZED` as a narrow regression fix, but prefer a maintained conversation summary/projection for 10M-row scale. See `references/message-list-query-performance.md`.
- UI layout vs data bugs: when the complaint is visual spacing, oversized rows, wrapping, or whitespace — especially if it happens on both filtered and unfiltered views — inspect screenshot/DOM/computed CSS before changing backend data projections. Distinguish wrong preview value from shared CSS grid/flex stretching; grid defaults can stretch rows/items and make bubbles look like they contain random whitespace. See `references/ui-layout-vs-data-bugs.md`.
- Link-only entries inside tab-driven sidebars: before adding navigation links to a layout backed by controlled tabs and URL `?tab=` state, verify link items are not rendered as `TabsTrigger` values or included in tab-content/current-tab validation. Otherwise clicks can persist a link id as the active tab before navigation, causing Back to land on an empty panel. See `references/sidebar-link-tabs-state.md`.
- If the issue cannot be reproduced dynamically, do not claim it is fixed; report what is missing and what was statically validated.

### 4. If Fix Doesn't Work — The Rule of Three

- **STOP.**
- Count: How many fixes have you tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question the architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**
- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**
