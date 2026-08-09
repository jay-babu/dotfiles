AWS: gamma=165569969323/HermesAgentPowerUser; production=928004597368/HermesAgentReadOnly. Nerv IaC=/root/code/zeus/main/iac/nerv.
§
Incidents need concrete cause/repro/verification; otherwise bounded diagnostics. Jay prefers lightweight targeted validation; avoid broad builds when spec-level tests suffice.
§
Permissions: Casbin v2=namespace/v3=action; nullable namespace is metadata; legacy rows have canonical copies. All=`*`; Read=Get+List; Write=Create+Update; Delete=Delete; action globs/subsumption stay in namespace. Token ops: absent=unscoped; present empty/blank/malformed=none. POSBackend defaults named roles; OWNER/ADMIN=`*`.
§
Plivo creds: Bitwarden Secrets Manager, not files.
§
Stripe PM sync: `customer_id` is required for `card_present` + `generated_card`, not plain `card`; never skip the former when missing. `card_present` without `generated_card` may skip.
§
Jay expects a plan before first prod automation run/schedule; PR≠operational approval. DB migrations: static SQL, split lock DDL/table. POSBackend skill only for POSBackend.
§
Kakashi: target is logged ephemeral ingest feeding permanent unpartitioned `audit_log`; never drop history. Preserve prod `audit_log_gin_cohort_idx`. Gamma 0.0002 insert-vacuum: 4.4x/avoided 82s stall, but cleanup took 108s—not sustained-proof; keep 32MiB GIN pending.
§
Sales-channel inventory: discard stale events and rows with matching channel-item relation; fetch via SQL EXISTS. Provi JSONL is unfiltered; `verified_in_stock=false` can be orderable (unverified, not OOS). Alt-Hero retains true/false/missing/null.
§
POS-device upserts key on cohort+entity+metadata.external_id; generate insert TypeID, preserve matched ID, unarchive, increment version, and use updated audit reason.
§
PL: switch+profit; POS irrelevant. Low-pop ≤cost→50%. Tito/Goose/Ketel private. Wine: WS-exact; Bezel≠Sonoma; Chalk Hill national. Spirits: base/style; Beefeater≠low-pop.
§
Transformity DB FK convention: referenced composite keys are named UNIQUE constraints backed by concurrently built indexes (`UNIQUE USING INDEX`), not bare unique indexes.
§
Sales channels: allow_negative_inventory makes negative stock in stock, but never zero.