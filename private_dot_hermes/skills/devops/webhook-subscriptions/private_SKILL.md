---
name: webhook-subscriptions
description: "Webhook subscriptions: event-driven agent runs."
version: 1.1.0
metadata:
  hermes:
    tags: [webhook, events, automation, integrations, notifications, push]
---

# Webhook Subscriptions

Create dynamic webhook subscriptions so external services (GitHub, GitLab, Stripe, CI/CD, IoT sensors, monitoring tools) can trigger Hermes agent runs by POSTing events to a URL.

## Setup (Required First)

The webhook platform must be enabled before subscriptions can be created. Check with:
```bash
hermes webhook list
```

If it says "Webhook platform is not enabled", set it up:

### Option 1: Setup wizard
```bash
hermes gateway setup
```
Follow the prompts to enable webhooks, set the port, and set a global HMAC secret.

### Option 2: Manual config
Add to `~/.hermes/config.yaml`:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "generate-a-strong-secret-here"
```

### Option 3: Environment variables
Add to `~/.hermes/.env`:
```bash
WEBHOOK_ENABLED=true
WEBHOOK_PORT=8644
WEBHOOK_SECRET=generate-a-strong-secret-here
```

After configuration, start (or restart) the gateway:
```bash
hermes gateway run
# Or if using systemd:
systemctl --user restart hermes-gateway
```

Verify it's running:
```bash
curl http://localhost:8644/health
```

## Commands

All management is via the `hermes webhook` CLI command:

### Create a subscription
```bash
hermes webhook subscribe <name> \
  --prompt "Prompt template with {payload.fields}" \
  --events "event1,event2" \
  --description "What this does" \
  --skills "skill1,skill2" \
  --deliver telegram \
  --deliver-chat-id "12345" \
  --secret "optional-custom-secret"
```

Returns the webhook URL and HMAC secret. The user configures their service to POST to that URL.

### List subscriptions
```bash
hermes webhook list
```

### Remove a subscription
```bash
hermes webhook remove <name>
```

### Test a subscription
```bash
hermes webhook test <name>
hermes webhook test <name> --payload '{"key": "value"}'
```

## Prompt Templates

Prompts support `{dot.notation}` for accessing nested payload fields:

- `{issue.title}` — GitHub issue title
- `{pull_request.user.login}` — PR author
- `{data.object.amount}` — Stripe payment amount
- `{sensor.temperature}` — IoT sensor reading

If no prompt is specified, the full JSON payload is dumped into the agent prompt.

## Common Patterns

### GitHub: new issues
```bash
hermes webhook subscribe github-issues \
  --events "issues" \
  --prompt "New GitHub issue #{issue.number}: {issue.title}\n\nAction: {action}\nAuthor: {issue.user.login}\nBody:\n{issue.body}\n\nPlease triage this issue." \
  --deliver telegram \
  --deliver-chat-id "-100123456789"
```

Then in GitHub repo Settings → Webhooks → Add webhook:
- Payload URL: the returned webhook_url
- Content type: application/json
- Secret: the returned secret
- Events: "Issues"

### GitHub: PR reviews
```bash
hermes webhook subscribe github-prs \
  --events "pull_request" \
  --prompt "PR #{pull_request.number} {action}: {pull_request.title}\nBy: {pull_request.user.login}\nBranch: {pull_request.head.ref}\n\n{pull_request.body}" \
  --skills "github-code-review" \
  --deliver github_comment
```

### Stripe: payment events
```bash
hermes webhook subscribe stripe-payments \
  --events "payment_intent.succeeded,payment_intent.payment_failed" \
  --prompt "Payment {data.object.status}: {data.object.amount} cents from {data.object.receipt_email}" \
  --deliver telegram \
  --deliver-chat-id "-100123456789"
```

### CI/CD: build notifications
```bash
hermes webhook subscribe ci-builds \
  --events "pipeline" \
  --prompt "Build {object_attributes.status} on {project.name} branch {object_attributes.ref}\nCommit: {commit.message}" \
  --deliver discord \
  --deliver-chat-id "1234567890"
```

### Generic monitoring alert
```bash
hermes webhook subscribe alerts \
  --prompt "Alert: {alert.name}\nSeverity: {alert.severity}\nMessage: {alert.message}\n\nPlease investigate and suggest remediation." \
  --deliver origin
```

### PagerDuty incident remediation

- references/scraper-execution-dlq-incidents.md
- references/transformity-pagerduty-incident-automation.md
- For TransformityPOSFrontend incidents titled like `Stably tests failed on main` or pointing to a GitHub Actions Stably workflow, also load `references/stably-github-actions-incident-remediation.md`.
- For TransformityPOSFrontend/POS frontend incidents involving ServiceWorker registration/update failures or `InvalidStateError: Failed to update a ServiceWorker`, also load `references/transformity-pos-service-worker-incidents.md`.
- For TransformityPOSFrontend/POS frontend incidents involving Electric SQL/PGlite shape sync crashes, offline sync startup failures, or `SyntaxError: Cannot convert ... to a BigInt`, also load `references/transformity-pos-electric-pglite-sync-incidents.md`.
- For TransformityPOSFrontend/POS frontend incidents titled like `Error: Invalid number of in-store sales channels: 0` (or any non-1 count), with culprit/location `SalePageConfigProvider.tsx`, or affecting `/sale/` sales-channel initialization, also load `references/transformity-pos-in-store-sales-channel-incidents.md`.
- For TransformityPOSFrontend/POS frontend incidents titled like `AxiosError: GET /invoiceApi/list → 401`, tagged `api.normalized_url=/invoiceApi/list`, or showing unauthenticated invoice-list requests on `/signin` or `/register/open/`, also load `references/transformity-pos-invoice-list-401-incidents.md`.
- For rewards-service Lambda/container deployment-wiring incidents, also load `references/rewards-service-lambda-deploy-wiring.md`.
- For rewards-service listener DLQ incidents that may map to database role/grant problems, load `references/pos-db-rewards-service-role-incidents.md`.
- For rewards-service listener/canceller DLQ or Lambda errors with RDS IAM auth failures for `user=rewards_service`, also load `references/rewards-service-db-iam-auth.md`.
- For rewards-service listener DLQ incidents where auth succeeds but logs show `permission denied for table loyalty_redemption_offer` or `permission denied for table reward_option`, also load `references/rewards-service-db-role-permissions.md`.
- For POSBackend/Sentry incidents titled `IOException: Broken pipe`, `ClientAbortException`, `AsyncRequestNotUsableException`, or involving client disconnects during streaming endpoints such as `GET /items/exports`, also load `references/posbackend-client-abort-broken-pipe-incidents.md`.
- For POSBackend/Sentry incidents titled like `NullPointerException: Parameter specified as non-null is null: method com.transformity.pos.campaign.database.model.Campaign.setType`, involving `POST /api/v1/campaign`, `Campaign.kt`, or stack frames in `CampaignMapperImpl.create` / `CampaignService.create`, also load `references/posbackend-campaign-type-null-incidents.md`.
- For POSBackend/Sentry incidents titled `JpaSystemException: transaction timeout expired` or `TransactionTimedOutException` involving `PurchaseOrderService.streamCandidatePurchaseOrderItems`, `PurchaseOrderService.kt`, `/purchaseOrderCandidateItem/stream`, `PurchaseOrderItemTransferController`, or `createInventoryTransferFromPurchaseOrder`, also load `references/posbackend-purchase-order-candidate-timeout-incidents.md`.
- For POSBackend/Sentry or Axios incidents involving `TransactionTimedOutException`, `POST /purchaseOrderItemTransfer/createInventoryTransferFromPurchaseOrder/{id}`, `PurchaseOrderItemTransferController.kt`, or repeated `EntityItemRepository.findByEntity_IdAndCohortItem_Id` stack frames, also load `references/posbackend-inventory-transfer-timeout-incidents.md`.
- For POSBackend/Sentry incidents involving `Campaign.setType`, `CampaignMapperImpl.create`, `POST /api/v1/campaign`, or Kotlin null-parameter errors like `Parameter specified as non-null is null: method com.transformity.pos.campaign.database.model.Campaign.setType`, also load `references/posbackend-campaign-type-null-incidents.md`.
- For POSBackend/AWS CloudWatch incidents involving Hikari/HikariCP, `hikaricp.connections.*`, `PG Connections`, `Connection Limit Too Many`, or `Connection Limit Too Low`, also load `references/hikari-cloudwatch-missing-data-incidents.md`.
- For POS Shift DLQ / Step Functions incidents involving `pos-shift-*-dlq-*`, `pos-shift-orchestrator-dlq-*`, `pos-shift-inventory-complete-dlq-*`, EventBridge Step Functions failure rules, or state machines named `pos-shift-*-orchestrator-*`, also load `references/pos-shift-dlq-incidents.md`.
- For scraper-service CloudWatch/SQS/Step Functions incidents involving `scraper-execution-dlq-*`, `scraper-*-dlq-*`, `Service=scraper` queue tags, or state machines named `scraper-orchestrator-*`, also load `references/scraper-execution-dlq-incidents.md`.
- For PagerDuty incidents from `Zapier Automation Alerts` or email subjects like `ALERT: Zap Turned Off - ...`, also load `references/zapier-automation-alert-incidents.md`.
- For `Zapier Automation Alerts` incidents, especially `ALERT: Zap Turned Off - ...`, also load `references/zapier-automation-alert-incidents.md`.

Key defaults from that pattern:
- If the agent is running on a public VM/droplet, prefer a real HTTPS reverse proxy to `localhost:8644` over tunnel services.
- If the user says PagerDuty webhooks are reliable, do not add a polling fallback.
- The agent may comment on PagerDuty only if authorized; do not acknowledge or resolve incidents unless explicitly authorized.
- A fix is only a fix after dynamic reproduction and dynamic verification. API calls count for non-UI bugs; UI bugs should be reproduced with browser/UI automation where possible.
- Prefer PagerDuty V3's documented `X-PagerDuty-Signature: v1=<hmac>` verification over repurposing compatibility headers such as `X-Gitlab-Token`.
- For PagerDuty scope type, use Account for all services/incidents, Team only when coverage should be limited to a team, and Service only for one service.

- For PagerDuty V3 webhooks, prefer PagerDuty's native `X-PagerDuty-Signature` verification over compatibility headers. Verify `v1=<hex HMAC-SHA256(raw request body, route secret)>` against comma-separated signature values with constant-time comparison. Unauthenticated or invalid public POSTs should return `401 Invalid signature`.

### Direct delivery (no agent, zero LLM cost)

For use cases where you just want to push a notification through to a user's chat — no reasoning, no agent loop — add `--deliver-only`. The rendered `--prompt` template becomes the literal message body and is dispatched directly to the target adapter.

Use this for:
- External service push notifications (Supabase/Firebase webhooks → Telegram)
- Monitoring alerts that should forward verbatim
- Inter-agent pings where one agent is telling another agent's user something
Before creating a branch, modifying files, or adding more than a blocker/duplicate note, check for active work already tied to the same PagerDuty incident. Re-run this guard immediately before creating/editing a worktree or touching code, even if it passed earlier, because another webhook run may have started while enrichment/reproduction was in progress. Treat **any non-empty output** from the process/worktree checks as a stop signal unless you can prove it is only the current shell command itself; do not continue to branch creation while interpreting the output.

```bash
hermes webhook subscribe antenna-matches \
  --deliver telegram \
  --deliver-chat-id "123456789" \
  --deliver-only \
  --prompt "🎉 New match: {match.user_name} matched with you!" \
  --description "Antenna match notifications"
```

The POST returns `200 OK` on successful delivery, `502` on target failure — so upstream services can retry intelligently. HMAC auth, rate limits, and idempotency still apply.

Requires `--deliver` to be a real target (telegram, discord, slack, github_comment, etc.) — `--deliver log` is rejected because log-only direct delivery is pointless.

## Security

- Each subscription gets an auto-generated HMAC-SHA256 secret (or provide your own with `--secret`)
- The webhook adapter validates signatures on every incoming POST
- Static routes from config.yaml cannot be overwritten by dynamic subscriptions
- Subscriptions persist to `~/.hermes/webhook_subscriptions.json`
- When checking PagerDuty/GitHub/Sentry/AWS credentials during incident runs, never print raw `.env`, config, credential-helper, or environment values. Print only variable/key names or redact values inline (for `.env` lines, split on the first `=` and output `NAME=[REDACTED]`). A shell/Python probe that intends to redact must handle both YAML `key: value` and dotenv `KEY=value` formats before emitting output.

## How It Works

1. `hermes webhook subscribe` writes to `~/.hermes/webhook_subscriptions.json`
2. The webhook adapter hot-reloads this file on each incoming request (mtime-gated, negligible overhead)
3. When a POST arrives matching a route, the adapter formats the prompt and triggers an agent run
4. The agent's response is delivered to the configured target (Telegram, Discord, GitHub comment, etc.)

## Troubleshooting

If webhooks aren't working:

1. **Is the gateway running?** Check with `systemctl --user status hermes-gateway` or `ps aux | grep gateway`
2. **Is the webhook server listening?** `curl http://localhost:8644/health` should return `{"status": "ok"}`
3. **Check gateway logs:** `grep webhook ~/.hermes/logs/gateway.log | tail -20`
4. **Signature mismatch?** Verify the secret in your service matches the one from `hermes webhook list`. GitHub sends `X-Hub-Signature-256`, GitLab sends `X-Gitlab-Token`.
5. **Firewall/NAT?** The webhook URL must be reachable from the service. For local development, use a tunnel (ngrok, cloudflared).
6. **Wrong event type?** Check `--events` filter matches what the service sends. Use `hermes webhook test <name>` to verify the route works.

### Approval prompts from webhook runs

Before creating a branch, modifying files, or adding more than a blocker/duplicate note, check for active work already tied to the same PagerDuty incident. Re-run this guard immediately before creating/editing a worktree or touching code, even if it passed earlier, because another webhook run may have started while enrichment/reproduction was in progress. Treat **any non-empty output** from the process/worktree checks as a stop signal unless you can prove it is only the current shell command itself; do not continue to branch creation while interpreting the output.

```bash
hermes webhook list
```

- `Deliver: log` means approval prompts and final responses are only written to gateway logs. Change the subscription to a chat target (for example `slack`) if the user needs to see the prompt.
- Be careful updating an existing subscription with `hermes webhook subscribe <same-name>`: if `--secret` is omitted, the CLI may generate a new route secret and break upstream HMAC verification. Prefer editing `~/.hermes/webhook_subscriptions.json` while preserving `secret`, or pass the existing secret explicitly.
- Cross-platform approval is not the same as cross-platform notification. Posting the plain fallback text to Slack/Telegram does not necessarily let `/approve` unblock the webhook run, because approvals are keyed to the original webhook session (`webhook:<route>:<delivery_id>`), not the target chat's session. A robust Slack fix should use the target adapter's interactive approval method (e.g. Slack `send_exec_approval(..., session_key=<webhook-session-key>)`) so button clicks resolve the webhook session. Otherwise consider `approvals.mode: smart/off` only as a deliberate safety tradeoff.
- Python adapter changes require a gateway restart; subscription JSON changes hot-reload only for new deliveries. Restarting can interrupt active webhook runs, so check active incident/remediation work before restarting.
