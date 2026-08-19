---
name: plan
description: "Plan mode: write markdown plan to .hermes/plans/, no exec."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, plan-mode, implementation, workflow]
    related_skills: [writing-plans, subagent-driven-development]
---

# Plan Mode

Use this skill when the user wants a plan instead of execution.

## Core behavior

For this turn, you are planning only.

- Do not implement code.
- Do not edit project files except the plan markdown file.
- Do not run mutating terminal commands, commit, push, or perform external actions.
- You may inspect the repo or other context with read-only commands/tools when needed.
- If the repo already has a branch/worktree or partial implementation for the task, inspect its current diff/status before planning. The plan should explicitly account for existing work, generated/out-of-sync files, and unrelated dirty files that must not be touched or staged.
- When the user corrects the approach while iterating on a saved plan, update the markdown plan immediately and then run a targeted search/readback pass for stale terminology from the rejected approach (for example old API paths, old implementation mechanisms, or endpoint-specific helpers). Do not just summarize the correction; make the saved plan internally consistent before responding.
- When user rejects a proposed abstraction as harder to read, preserve or restore the simpler explicit shape unless the abstraction is technically necessary. For generated-code plans, prefer readable generated switch/case control flow over descriptor/table-driven indirection when both are viable.
- When user rejects compatibility shims/adapters/fallback preservation as lazy or asks to “pave” to a new stack, rewrite the plan around the target-native contract rather than a hybrid. Rename internal-only variables/APIs/configs to the new ecosystem’s idioms, make the full migration path primary, demote old-stack scripts only to temporary comparison if useful, and add stale-term checks so old compatibility language does not linger as implementation guidance.
- For code plans, encode reusable/generalized abstractions when the user asks for them instead of preserving a narrow endpoint-specific shape. Spell out the generic call shape, recursion/depth limits, validation gates, and representative examples from more than one root/context so future implementation does not regress to a one-off solution.
- When planning generated/codegen-backed API expand loaders, prefer type-safe generated dispatch over runtime reflection if the project owns the generator/ORM. See `references/type-safe-expand-loader-plans.md` for the Bob SelectThenLoad pattern and pitfalls.
- Your deliverable is a markdown plan saved inside the active workspace under `.hermes/plans/`.
- Your deliverable is a markdown plan saved inside the active workspace under `.hermes/plans/`.

## Output requirements

Write a markdown plan that is concrete and actionable.

Include, when relevant:
- Goal
- Current context / assumptions
- Proposed approach
- Step-by-step plan
- Files likely to change
- Tests / validation
- Risks, tradeoffs, and open questions

If the task is code-related, include exact file paths, likely test targets, and verification steps.

When planning API contract changes that involve `expand`, `include`, joins, or nested response models, explicitly trace the underlying relationship path before naming public expand/sort keys. Prefer recursive expand paths and nested response fields that mirror the data relationship (for example `participant -> loyalty_customer -> customer` should produce `expand=loyalty_customer.customer` and `participant.loyaltyCustomer.customer`, not a flat top-level `expand=customer` / `participant.customer`). If sorting depends on an optional expanded relationship, document whether the sort key requires the corresponding expand and reject surprise joins by default unless the user asks otherwise.

## Save location

Save the plan with `write_file` under:
- `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`

Treat that as relative to the active working directory / backend workspace. Hermes file tools are backend-aware, so using this relative path keeps the plan with the workspace on local, docker, ssh, modal, and daytona backends.

If the runtime provides a specific target path, use that exact path.
If not, create a sensible timestamped filename yourself under `.hermes/plans/`.

## Interaction style

- If the request is clear enough, write the plan directly.
- If the user says "let me know the plan first" or similar, treat it as plan mode even without `/plan`: do read-only repo/context inspection as needed, do not implement, and return a concise plan plus the saved path.
- Call out concrete defaults and assumptions that affect implementation (for example same-tab vs new-tab, relative vs absolute URLs, which field gates conditional UI) so the user can approve or adjust before mutation.
- If no explicit instruction accompanies `/plan`, infer the task from the current conversation context.
- If it is genuinely underspecified, ask a brief clarifying question instead of guessing.
- After saving the plan, reply briefly with what you planned and the saved path.
