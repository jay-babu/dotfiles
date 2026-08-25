AWS: gamma=165569969323/HermesAgentPowerUser; production=928004597368/HermesAgentReadOnly. Nerv IaC=/root/code/zeus/main/iac/nerv.
§
Incidents: prove cause/repro/verification; deployment failures ≠ merged-code bugs, so no code-fix PR for rollout-only failures. Prefer targeted validation.
§
Permissions: Casbin v2=namespace/v3=action; nullable namespace metadata; legacy canonical copies. All=*; Read=Get+List; Write=Create+Update; Delete=Delete; globs stay in namespace. Tokens: absent=unscoped; empty/invalid=none. POSBackend named roles; OWNER/ADMIN=*.
§
Plivo creds: Bitwarden Secrets Manager, not files.
§
Stripe PM sync: customer_id required for card_present+generated_card, not plain card; never skip the former if missing. card_present without generated_card may skip.
§
Jay expects a plan before first prod automation run/schedule; PR≠approval. DB migrations: static SQL, split lock DDL/table. POSBackend skill only for POSBackend.
§
Audit: permanent unpartitioned audit_log; txid xid8 NOT NULL DEFAULT 0; changed_at timestamptz NOT NULL DEFAULT statement_timestamp(). Preserve prod GIN cohort index/32MiB pending.
§
Sales-channel inventory: discard stale/matching-relation events via SQL EXISTS. Provi JSONL unfiltered; verified false may be orderable. Alt-Hero preserves booleans/missing/null. DoorDash approved identical full composite size strings and pack-only fallback without size/UOM.
§
POS-device upserts key on cohort+entity+metadata.external_id; generate insert TypeID, preserve matched ID, unarchive, increment version, and use updated audit reason.
§
PL: switch+profit; low-pop≤cost→50%; Tito/Goose/Ketel. Wine WS-exact; Bezel≠Sonoma. Spirits base/style; Beefeater≠low-pop. Rum: Port Hawk Silver<Bacardi Superior; Sailor Jerry Spiced≥Captain Morgan.
§
Transformity DB FK convention: referenced composite keys are named UNIQUE constraints backed by concurrently built indexes (`UNIQUE USING INDEX`), not bare unique indexes.
§
Zeus: Bob only; prefer generated typed Where helpers when equivalent; TypeSpec follows existing Lifecycle/MergePatch/expand/readapi patterns; no @operationId.
§
Kurama’s runtime DB role is naruto; local developer processes may use a different role.