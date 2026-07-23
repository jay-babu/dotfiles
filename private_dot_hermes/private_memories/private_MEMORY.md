AWS profiles: gamma=165569969323/HermesAgentPowerUser; production=928004597368/HermesAgentReadOnly. Nerv IaC: /root/code/zeus/main/iac/nerv.
§
Incident workflow: fixes require a concrete backend/product cause, dynamic reproduction, and verification; insufficient evidence warrants bounded diagnostics.
§
POS/Zeus permissions: source=`permissionDualWrite.ts` RHS. Aggregates: All=`*`, Read=Get+List, Write=Create+Update, Delete=Delete. `*` globs anywhere; drop subsumed same-namespace grants; OWNER/ADMIN use `*`. Rollout: canonicalize/stop legacy writes → deploy → clean DB → reject legacy. Kurama APIs favor generated Bob + direct `expandparam` preloads, never SQLC/manual expand checks. Tests: external `_test`, `t.Context()`, whole-value `testkit.MustEqual`. Errors use `httpproblem`; preserve causes/classify via `errors.AsType[*problem.Problem]`. PRs rebase `origin/main`.
§
PagerDuty automation: From=jay@transformity.tech; Sentry org=transformity. Dedupe against all-open PD plus unresolved Sentry enrichment; merge confident duplicates after approval; resolve inactive >60d when applicable.
§
Hermes incident gateway: PagerDuty V3 webhook uses `X-PagerDuty-Signature` HMAC-SHA256 with route secret; route `pagerduty-incidents` delivers to Slack, whose approval buttons unblock webhook dangerous-command prompts.
§
PD→Slack incident thread mapping: JSONL not JSON. Plivo creds: Bitwarden Secrets Manager, not files.
§
Stripe PM sync: `customer_id` is expected for `card_present` with `generated_card`, not plain `card`; never silently skip the former when missing. `card_present` without `generated_card` may skip.
§
Discuss before scope/push. DB migrations: static SQL, split lock-taking DDL per table. POSBackend skill only for POSBackend.
§
Kakashi: production requires `audit.audit_log_gin_cohort_idx`; performance fixes must preserve it.
§
Sales-channel inventory sync discards stale entity-item events and events whose matching channel-item relation exists; prefer fetching the row over custom SQL EXISTS.
§
POS-device upserts key on cohort+entity+metadata.external_id; generate insert TypeID, preserve matched ID, unarchive, increment version, and use updated audit reason.