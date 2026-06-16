# Remediation rules (shared gates for every PagerDuty→PR run)

Load this on every PagerDuty incident-remediation run, in addition to the matched
`references/<slug>-incidents.md` playbook. Each rule below is a **hard pre-condition on opening a
PR**. If a fix fails a gate, do not open the PR — post a diagnostic PagerDuty note with the
evidence instead. Before opening, run these against your own diff as a self-review.

These exist because auto-generated remediation PRs reliably fail in the same ways: band-aids that
suppress the symptom, no-ops that don't touch the failing path, duplicates of work already
merged, and changes to shared surfaces that no human will merge from a bot queue.

## 1. Fix-shape gate — prevent the bad operation, don't tolerate its failure

The strongest predictor of an accepted fix is that it stops the failing operation at the source
(guard the request, validate at write time, gate by permission) rather than swallowing, retrying,
or filtering the failure.

**Forbidden unless the matched playbook explicitly authorizes it AND the scope test passes:**
- `throwOnError: false`, empty/catch-all `.catch`, or removing a `throw`
- raising a timeout or adding `waitForLoadState("networkidle")` to "stabilize" a test
- broadening a Sentry `beforeSend` / `ignoreErrors` filter
- a blanket retry wrapper

**Scope test for an allowed suppression** (all three required):
1. targets one proven-benign signature (e.g. 404 only, an exact error string), not a whole class;
2. still `captureException`s everything else (honor the repo's "no silent errors" rule);
3. the benign event is still recorded somewhere (breadcrumb / metric) — prefer a Sentry
   **alert-rule** change over a code filter when the goal is only noise reduction.

Retries: only on truly retryable, idempotent operations. **401 ≠ 403** — 403 is an authorization
denial; retrying it (or refreshing a token) masks a permission bug and does not fix it.

## 2. Verify-the-path gate — don't ship a no-op

`git show` the base commit of the function you edited and confirm it is the path that emits the
symptom. If the error originates in a different handler (e.g. a global error handler, not the
call site you wrapped), your change does nothing. A reproduction test must exercise the **real**
library/runtime semantics, not a mock that encodes your assumed failure mode.

## 3. Blast-radius gate — escalate shared surfaces, don't auto-merge them

For changes to the shared HTTP client, global error boundary, `Sentry.init`, money/sale-path
storage, or any auth interceptor: open a **draft proposal for a human**, and grep for duplicated
copies of the logic before editing one of them. **Alarm / IaC / alert-threshold tuning is out of
scope** for incident remediation — post a diagnostic note, do not open a PR.

## 4. Behavior-change enumeration — for any narrow/optimize

List the result-set or side-effect differences in the PR body: `LEFT JOIN → INNER JOIN` drops
rows; "narrowing" an update can drop a side effect; scoping changes (entity→cohort) change which
rows match; selection-order changes pick a different winner. Forward and reverse operations must
stay symmetric (if a sale path stops writing X, the cancel path must stop restoring X).

## 5. Convention gate — match the repo from the first commit

**TransformityPOSFrontend:** no `any`; no `as` / `!` casts; never hand-edit `generated/`,
`spring-generated/`, or `kurama-generated/` (update the OpenAPI/TypeSpec spec and run
`bun run codegen`, never `@ts-expect-error`); Radix/Tailwind + shadcn, never Chakra; wrap
`mutateAsync` in try/catch with `extractAxios400ErrorMessage`; shared predicates in `utils/`.

**POSBackend:** MockK, not Mockito/Java test classes; extend `BaseIntegrationTest` with `given*`
helpers; assert whole objects with `usingRecursiveComparison`; never mock inputs (build the real
object); pick one of `BadRequestException` (400) / `ValidationException` (422) consistently with
sibling code; add `@RestResource(exported = false)` to new finders on `@RepositoryRestResource`
interfaces; `@Inject` not `@Autowired`; Kotlin services `open` + `@Named`; new APIs use a
`@RestController` (never a new `*ApiDelegateImpl`); migrations live in `pos-db`, idempotent.

**zeus / kurama:** every non-GET op needs an audit reason mapped to an `auditcode` constant;
cohort-scope every by-ID fetch/mutation (verify the resource belongs to the request's cohort —
do not trust a bare TypeID); edit TypeSpec source, never generated output.

## 6. Layer/ownership gate

Keep the fix in the owning repo and layer: pos-db migrations in pos-db (not a submodule bump in
the consumer), codegen fixes in the spec, frontend bugs get frontend fixes. A backend workaround
for a frontend caller (or vice-versa) is the wrong layer.

## 7. Stamp & escalate

Every PR carries the `hermes-remediation` trailer (see "Duplicate sibling-PR prevention" in
SKILL.md). If the only available change is a timeout bump or a suppression that fails the scope
test, file a diagnosis-rich PagerDuty note instead of a PR, and escalate suspected **product**
bugs (not test/infra) to a human rather than absorbing them into remediation code.
