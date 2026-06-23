Hermes AWS: AWS_PROFILE gamma/production; fish `dev_t` exports AWS creds + PG env for RDS. Roles Anywhere `gamma`=165569969323/HermesAgentPowerUser, `production`=928004597368/HermesAgentReadOnly; certs /root/.aws/rolesanywhere, leaf expires 2026-10-31. IAM/RA IaC /root/code/zeus/main/iac/nerv; public CA cert ok in repo, private keys not.
§
Incident workflow: Do not treat alert downgrades/suppression or hypotheses as fixes. For app incidents (incl. Intercom token 502s), identify concrete backend/product cause from logs/replay first; if evidence is insufficient, add bounded diagnostics. Fix only after dynamic reproduction+verification.
§
POS permission migrations: gist review before PRs; reconcile FE/BE/Zeus + prod casbin distinct perms (parquet ok) without dropping source-only; singular `Resource:Action`, CRUD-prefixed actions w/domain exceptions; split backfill vs later-delete PRs; handle `*`.
§
Incident workflow completion criterion: after an incident PR has passing status checks and the issue has been dynamically verified fixed, the agent is done. It should not wait for merge/deploy verification unless separately requested.
§
PagerDuty automation: From=jay@transformity.tech; Sentry org=transformity. Dedupe via all-open PD + unresolved Sentry dry-run/enrichment (not just canaries); merge confident duplicates after approval; resolve inactive >60d if applicable.
§
Hermes incident gateway local patches/quirks: /usr/local/lib/hermes-agent/gateway/platforms/webhook.py validates PagerDuty Webhooks V3 via X-PagerDuty-Signature `v1=<hex HMAC-SHA256(raw body, route secret)>`; invalid signatures tested 401 and valid 202 at https://hermes.usemargin.dev/webhooks/pagerduty-incidents. Webhook approval prompts now delegate through the configured delivery target’s `send_exec_approval(..., session_key=<webhook key>)`, and PagerDuty route `pagerduty-incidents` is configured with `deliver: slack` so Slack approval buttons can unblock webhook-run dangerous-command prompts.
§
PD→Slack incident thread mapping: JSONL not JSON. Plivo creds: Bitwarden Secrets Manager, not files.