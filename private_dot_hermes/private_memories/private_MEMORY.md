Hermes AWS: DO IPs 45.55.44.155, 10.108.0.3, 2604:a880:800:14:0:2:e6b7:f000. Roles Anywhere profiles: `gamma`=165569969323/HermesAgentPowerUser, `production`=928004597368/HermesAgentReadOnly; certs in /root/.aws/rolesanywhere, leaf expires 2026-10-31. AWS-side IAM/RA resources live in Pulumi /root/code/zeus/main/iac/nerv; public CA cert ok in repo, private keys not.
§
Incident workflow: Do not treat alert downgrades/suppression or hypotheses as fixes. For app incidents (incl. Intercom token 502s), identify concrete backend/product cause from logs/replay first; if evidence is insufficient, add bounded diagnostics. Fix only after dynamic reproduction+verification.
§
Transformity: worktrees beside main; pd-=PD. FE repro mise node22; BE Java17 bootRun. Kurama verify via proxy+local gamma POS creds; never print UI creds. POS prod DB RO: prod/jay_hermes/postgres/AWS SSL/BEGIN RO/helper. pos-db contracts: dynamic public checks; allowlist missing cohort_id/created_at/updated_at/update triggers.
§
Incident workflow completion criterion: after an incident PR has passing status checks and the issue has been dynamically verified fixed, the agent is done. It should not wait for merge/deploy verification unless separately requested.
§
PagerDuty automation: use jay@transformity.tech as REST API From; Sentry org transformity. Dedupe means broad all-open PD + unresolved Sentry dry-run/enrichment, not just canaries; merge confident duplicates after approval; resolve inactive >60d if applicable.
§
Hermes incident gateway local patches/quirks: /usr/local/lib/hermes-agent/gateway/platforms/webhook.py validates PagerDuty Webhooks V3 via X-PagerDuty-Signature `v1=<hex HMAC-SHA256(raw body, route secret)>`; invalid signatures tested 401 and valid 202 at https://hermes.usemargin.dev/webhooks/pagerduty-incidents. Webhook approval prompts now delegate through the configured delivery target’s `send_exec_approval(..., session_key=<webhook key>)`, and PagerDuty route `pagerduty-incidents` is configured with `deliver: slack` so Slack approval buttons can unblock webhook-run dangerous-command prompts.
§
PagerDuty→Slack incident thread mapping should be stored as JSONL, not JSON.