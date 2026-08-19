AWS: gamma=165569969323/HermesAgentPowerUser; production=928004597368/HermesAgentReadOnly. Nerv IaC=/root/code/zeus/main/iac/nerv.
§
Incidents: prove cause/repro/verification; distinguish deployment failures from merged code bugs—don't open code-fix PRs for rollout-only failures. Prefer targeted validation over broad builds.
§
Permissions: Casbin v2=namespace/v3=action; nullable namespace is metadata; legacy rows have canonical copies. All=`*`; Read=Get+List; Write=Create+Update; Delete=Delete; action globs/subsumption stay in namespace. Token ops: absent=unscoped; present empty/blank/malformed=none. POSBackend defaults named roles; OWNER/ADMIN=`*`.
§
Plivo creds: Bitwarden Secrets Manager, not files.
§
Stripe PM sync: `customer_id` is required for `card_present` + `generated_card`, not plain `card`; never skip the former when missing. `card_present` without `generated_card` may skip.
§
Jay expects a plan before first prod automation run/schedule; PR≠operational approval. DB migrations: static SQL, split lock DDL/table. POSBackend skill only for POSBackend.
§
Kakashi: logged ingest → permanent unpartitioned `audit_log`; never drop history. Ingest: `txid xid8 NOT NULL DEFAULT 0`; `changed_at timestamptz NOT NULL DEFAULT statement_timestamp()`. Preserve prod GIN cohort index/32MiB pending.
§
Sales-channel inventory: discard stale events and rows with matching channel-item relation; fetch via SQL EXISTS. Provi JSONL is unfiltered; `verified_in_stock=false` can be orderable (unverified, not OOS). Alt-Hero retains true/false/missing/null.
§
POS-device upserts key on cohort+entity+metadata.external_id; generate insert TypeID, preserve matched ID, unarchive, increment version, and use updated audit reason.
§
PL: switch+profit; low-pop≤cost→50%; Tito/Goose/Ketel. Wine WS-exact; Bezel≠Sonoma. Spirits base/style; Beefeater≠low-pop. Rum: Port Hawk Silver<Bacardi Superior; Sailor Jerry Spiced≥Captain Morgan.
§
Transformity DB FK convention: referenced composite keys are named UNIQUE constraints backed by concurrently built indexes (`UNIQUE USING INDEX`), not bare unique indexes.
§
Sales channels: allow_negative_inventory makes negative stock in stock, but never zero.