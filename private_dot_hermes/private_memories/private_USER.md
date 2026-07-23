Jay prefers concise Slack bullets, uninterrupted execution, exact API tests, and candid PR readiness reports with failures disclosed.
§
Prefers mise, uv, and existing auth/creds.
§
Architecture-first; prefers one high-impact, low-maint change. Admin UI: visible controls, readable labels, minimal headers; warn before discarding edits.
§
POS/Kurama: accurate parser/nullability, cohort-scoped auth, exploded arrays, nested expands, total_pages, CRUD perms, generated Bob joins; user-access writes use row-level operations.
§
Jay direct: @mention <@U068K4E4DFC> in final review; no tags for webhook/cron. PRs: rebase main and verify GitHub mergeability/conflicts, not just CI.
§
Prefers direct DB migrations; don't add role-existence guards unless asked.
§
Jay prefers narrow, purpose-revealing package paths—not core/common/helper/utils or generic tools dumping grounds; favors internal/cmd/<command>. Prefers gomock and inferred mockgen package names.
§
Jay expects approved plan items tracked until completed or explicitly deferred; new wins don't replace agreed workstreams.
§
Transaction-report verification runs only in gamma, never production.
§
Jay expects public config names and allowed string values to match his requested contract exactly.
§
For authorized repo work, Jay prefers logical commits pushed incrementally and a PR maintained as work progresses.