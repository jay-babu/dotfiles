---
name: google-workspace
description: "Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python."
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials (downloaded from Google Cloud Console)
metadata:
  hermes:
    tags: [Google, Gmail, Calendar, Drive, Sheets, Docs, Contacts, Email, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

Gmail, Calendar, Drive, Contacts, Sheets, and Docs — through Hermes-managed OAuth and a thin CLI wrapper. When `gws` is installed, the skill uses it as the execution backend for broader Google Workspace coverage; otherwise it falls back to the bundled Python client implementation.

## References

- `references/gmail-search-syntax.md` — Gmail search operators (is:unread, from:, newer_than:, etc.)
- `references/gmail-bulk-trash.md` — safety pattern for bulk Gmail trash/delete requests using Gmail API `users.messages.trash`.
- `references/github-pr-bot-trash-filters.md` — pattern for replacing Gmail filters and trashing GitHub PR bot notifications from Copilot, Greptile, and Amplify with safety checks.
- `references/gmail-vendor-outreach.md` — workflow for user-preauthorized outbound vendor sourcing/procurement outreach: research contacts, draft safe business emails, send via Gmail, and verify sent/bounce status.
- `references/sheets-pos-parquet-enrichment.md` — pattern for updating Sheets from POS product hyperlinks plus local Postgres Parquet exports; covers hyperlink extraction, verifying whether `/item/<id>` is a cohort item vs entity item, DuckDB queries, approval prompts, and read-back verification.
- `references/sheets-in-cell-images.md` — pattern for adding actual in-cell images to Sheets with `IMAGE()` formulas, column insertion/formatting, visual QA of product images, and formula read-back verification.
- `references/private-label-outreach-sheets.md` — pattern for turning private-label/vendor sourcing research into a per-product Google Sheet tab with product rationale, approved outreach copy, and detailed outreach tracker.
- `references/public-ecommerce-scrape-to-sheets.md` — pattern for scraping public ecommerce product listings into a ranked Google Sheet, including anti-bot browser-cookie replay, shared-drive folder creation, grid expansion, methodology tabs, and verification.
- `references/google-meet-auto-artifacts.md` — pattern for enabling Google Meet recording, transcription, and Gemini smart notes from hosted Calendar events, including OAuth scope/API enablement, Meet space patching, captions limitation, and cron/webhook automation.
- `references/calendar-meet-auto-artifacts.md` — enabling Google Meet auto-recording, transcripts, and Gemini notes for Calendar-created Meet spaces via the Meet API.

## Scripts

- `scripts/setup.py` — OAuth2 setup (run once to authorize)
- `scripts/google_api.py` — compatibility wrapper CLI. It prefers `gws` for operations when available, while preserving Hermes' existing JSON output contract.

## First-Time Setup

The setup is fully non-interactive — you drive it step by step so it works
on CLI, Telegram, Discord, or any platform.

Define a shorthand first:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
```

### Step 0: Check if already set up

```bash
$GSETUP --check
```

If it prints `AUTHENTICATED`, skip to Usage — setup is already done.

### Step 1: Triage — ask the user what they need

Before starting OAuth setup, ask the user TWO questions:

**Question 1: "What Google services do you need? Just email, or also
Calendar/Drive/Sheets/Docs?"**

- **Email only** → They don't need this skill at all. Use the `himalaya` skill
  instead — it works with a Gmail App Password (Settings → Security → App
  Passwords) and takes 2 minutes to set up. No Google Cloud project needed.
  Load the himalaya skill and follow its setup instructions.

- **Email + Calendar** → Continue with this skill, but use
  `--services email,calendar` during auth so the consent screen only asks for
  the scopes they actually need.

- **Calendar/Drive/Sheets/Docs only** → Continue with this skill and use a
  narrower `--services` set like `calendar,drive,sheets,docs`.

- **Full Workspace access** → Continue with this skill and use the default
  `all` service set.

**Question 2: "Does your Google account use Advanced Protection (hardware
security keys required to sign in)? If you're not sure, you probably don't
— it's something you would have explicitly enrolled in."**

- **No / Not sure** → Normal setup. Continue below.
- **Yes** → Their Workspace admin must add the OAuth client ID to the org's
  allowed apps list before Step 4 will work. Let them know upfront.

### Step 2: Create OAuth credentials (one-time, ~5 minutes)

Tell the user. When the user needs to copy/paste links, print each URL on its own line or in its own `text` code block rather than embedding it only in prose:

> You need a Google Cloud OAuth client. This is a one-time setup:
>
> 1. Create or select a project:
>    https://console.cloud.google.com/projectselector2/home/dashboard
> 2. Enable the required APIs from the API Library:
>    https://console.cloud.google.com/apis/library
>    Enable: Gmail API, Google Calendar API, Google Drive API,
>    Google Sheets API, Google Docs API, People API, Google Meet API
> 3. Create the OAuth client here:
>    https://console.cloud.google.com/apis/credentials
>    Credentials → Create Credentials → OAuth 2.0 Client ID
> 4. Application type: "Desktop app" → Create
> 5. If the app is still in Testing, add the user's Google account as a test user here:
>    https://console.cloud.google.com/auth/audience
>    Audience → Test users → Add users
> 6. Download the JSON file and tell me the file path
>
> Important Hermes CLI note: if the file path starts with `/`, do NOT send only the bare path as its own message in the CLI, because it can be mistaken for a slash command. Send it in a sentence instead, like:
> `The JSON file path is: /home/user/Downloads/client_secret_....json`

Once they provide the path:

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

If they paste the raw client ID / client secret values instead of a file path,
write a valid Desktop OAuth JSON file for them yourself, save it somewhere
explicit (for example `~/Downloads/hermes-google-client-secret.json`), then run
`--client-secret` against that file.

### Step 3: Get authorization URL

Current `setup.py` authorizes the full Workspace scope set and does not accept `--services` or `--format` flags. Run:

```bash
$GSETUP --auth-url
```

This prints the authorization URL directly.

Agent rules for this step:
- Send the printed URL to the user as a single line.
- Tell the user that the browser will likely fail on `http://localhost:1` after approval, and that this is expected.
- Tell them to copy the ENTIRE redirected URL from the browser address bar.
- If the user gets `Error 403: access_denied`, send them directly to `https://console.cloud.google.com/auth/audience` to add themselves as a test user.

### Step 4: Exchange the code

The user will paste back either a URL like `http://localhost:1/?code=4/0A...&scope=...`
or just the code string. Either works. The `--auth-url` step stores a temporary
pending OAuth session locally so `--auth-code` can complete the PKCE exchange
later, even on headless systems:

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED"
```

Current `setup.py` does not accept `--format`; it prints a plain success/error message.

If `--auth-code` fails because the code expired, was already used, or came from
an older browser tab, it now returns a fresh `fresh_auth_url`. In that case,
immediately send the new URL to the user and have them retry with the newest
browser redirect only.

### Step 5: Verify

```bash
$GSETUP --check
```

Should print `AUTHENTICATED`. Setup is complete — token refreshes automatically from now on.

### Notes

- Token is stored at `~/.hermes/google_token.json` and auto-refreshes.
- Pending OAuth session state/verifier are stored temporarily at `~/.hermes/google_oauth_pending.json` until exchange completes.
- If `gws` is installed, `google_api.py` points it at the same `~/.hermes/google_token.json` credentials file. Users do not need to run a separate `gws auth login` flow.
- To revoke: `$GSETUP --revoke`

## Usage

All commands go through the API script. Set `GAPI` as a shorthand:

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
```

### Gmail

```bash
# Search (returns JSON array with id, from, subject, date, snippet)
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Read full message (returns JSON with body text)
$GAPI gmail get MESSAGE_ID

# Send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html
$GAPI gmail send --to user@example.com --subject "Hello" --from '"Research Agent" <user@example.com>' --body "Message text"

# The CLI currently expects the body as a --body value, not --body-file. For a
# longer saved draft, read the file in a small Python/shell wrapper and pass the
# string as --body rather than inventing unsupported flags.
```

After sending, verify with the returned Gmail message `id`/`threadId` using
`$GAPI gmail get MESSAGE_ID` when possible. Searching Sent by recipient/subject is
also useful, but search result metadata may be sparse for some sent messages;
the returned id is the strongest handle.

```bash
# Reply (automatically threads and sets In-Reply-To)
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
$GAPI gmail reply MESSAGE_ID --from '"Support Bot" <user@example.com>' --body "Thanks"

# Labels
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

**Gmail native filters:** Creating/managing Gmail Settings filters via
`users.settings.filters.*` requires the extra scope
`https://www.googleapis.com/auth/gmail.settings.basic`. If filter creation fails
with `403 insufficient authentication scopes`, either re-authorize after adding
that scope to the OAuth setup or use a Hermes cron watchdog that searches with
`gmail.modify` and moves matching messages to Trash. Gmail subject search is
tokenized and ignores some punctuation, so always re-fetch metadata and enforce
header allowlist checks before trashing messages. Gmail filters cannot be
patched in place through the API: to "update" one, create the replacement,
then delete the obsolete narrower filter and verify only the intended filter
remains. For GitHub PR bot notification cleanup (Copilot/Greptile/Amplify), see
`references/github-pr-bot-trash-filters.md`.

### Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (ISO 8601 with timezone required)
$GAPI calendar create --summary "Team Standup" --start 2026-03-01T10:00:00-06:00 --end 2026-03-01T10:30:00-06:00
$GAPI calendar create --summary "Lunch" --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z --location "Cafe"
$GAPI calendar create --summary "Review" --start 2026-03-01T14:00:00Z --end 2026-03-01T15:00:00Z --attendees "alice@co.com,bob@co.com"

# Delete event
$GAPI calendar delete EVENT_ID
```

### Google Meet auto-artifacts from Calendar events

When asked to auto-enable recording/transcription/Gemini notes for Calendar events, use the Meet API `spaces` resource rather than trying to patch the Calendar event itself. Calendar provides the Meet code/link; artifact toggles live in `Space.config.artifactConfig`. Required scope: `https://www.googleapis.com/auth/meetings.space.settings`, and the OAuth project must have the Google Meet API enabled. See `references/google-meet-auto-artifacts.md` for the verified patch body, update mask, caption limitation, and cron/webhook automation pattern.

#### Google Meet recording/transcript/Gemini notes for Calendar events

Calendar event fields can identify the Meet link/code and organizer, but the UI toggles for **Record the meeting**, **Transcribe the meeting**, and **Take notes with Gemini** are configured through the Google Meet API `spaces` resource. This requires the extra scope `https://www.googleapis.com/auth/meetings.space.settings`; a 403 `ACCESS_TOKEN_SCOPE_INSUFFICIENT` from `meet.googleapis.com/v2/spaces/...` means re-authorize with that scope rather than trying to patch Calendar event fields. See `references/calendar-meet-auto-artifacts.md` for the full one-event verification and patch workflow.

### Drive

```bash
# Search existing files
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5

# Get metadata for a single file
$GAPI drive get FILE_ID

# Upload a local file (auto-detects MIME type)
$GAPI drive upload /path/to/report.pdf
$GAPI drive upload /path/to/image.png --name "Logo.png" --parent FOLDER_ID

# Download (binary files download as-is; Google-native files export to a
# sensible default — Docs→pdf, Sheets→csv, Slides→pdf, Drawings→png)
$GAPI drive download FILE_ID
$GAPI drive download DOC_ID --output ~/doc.pdf
$GAPI drive download DOC_ID --export-mime text/plain --output ~/doc.txt

# Create a folder
$GAPI drive create-folder "Reports"
$GAPI drive create-folder "Q4" --parent FOLDER_ID

# Share
$GAPI drive share FILE_ID --email alice@example.com --role reader
$GAPI drive share FILE_ID --email alice@example.com --role writer --notify
$GAPI drive share FILE_ID --type anyone --role reader        # anyone with link
$GAPI drive share FILE_ID --type domain --domain example.com --role reader

# Delete — defaults to trash (reversible). Use --permanent to skip the trash.
$GAPI drive delete FILE_ID
$GAPI drive delete FILE_ID --permanent
```

### Contacts

```bash
$GAPI contacts list --max 20
```

### Sheets

```bash
# Create a new spreadsheet
$GAPI sheets create --title "Q4 Budget"
$GAPI sheets create --title "Inventory" --sheet-name "Stock"

# Read
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

### Sheets enrichment patterns

When enriching an existing Sheet from external data or local analysis:

- Resolve the actual tab title from spreadsheet metadata before writing ranges, especially when the user provides a `gid` or a copied sheet URL. The visible/tab title can differ from the name inferred from prior context; using the wrong title yields `Unable to parse range` even when the `gid` is valid.
- Prefer batched writes (`spreadsheets.values.batchUpdate`) for many cell updates. Use `valueInputOption: USER_ENTERED` when inserting formulas.
- To make an existing display cell clickable while preserving its visible text, write `=HYPERLINK("URL","Display Text")` to that cell, escaping embedded double quotes in both strings. Verify with `valueRenderOption=FORMULA`, not only formatted values, so you can confirm the formula exists.
- To show actual images in cells rather than plain image links, insert/reuse an image column and write `=IMAGE("URL",4,height,width)` formulas with `valueInputOption=USER_ENTERED`; format row heights/column width and verify formulas with `valueRenderOption=FORMULA`. When image quality matters (e.g. bottle front, not case or label), visually QA candidates before writing. See `references/sheets-in-cell-images.md`.
- When using existing hyperlinks as foreign-key hints, read full grid data (`includeGridData=true`) and extract URLs from `hyperlink`, `textFormatRuns[].format.link.uri`, or `userEnteredValue.formulaValue`. Verify what the embedded ID actually represents before joining external data; for POS product URLs, `/item/<id>` may be a shared/cohort item ID rather than an entity-specific item row. See `references/sheets-pos-parquet-enrichment.md`.
- For adding columns/formatting or working around grid limits, inspect `gridProperties(rowCount,columnCount)` first. If a range exceeds current grid limits, expand the grid or create/update the intended tab explicitly before writing beyond existing columns.
- For multi-tab Sheets created from external exports, use the Python Google API client directly (`from google_api import build_service`) when you need tab creation, chunked writes, filters, frozen rows, wrapping, and auto-resize in one workflow; the CLI is fine for simple single-range writes.
- When exporting analysis derived from raw external assets (for example S3 audio plus `analysis/findings.json` artifacts), include a `Coverage` tab showing raw asset counts and whether derived artifacts exist so missing analysis is explicit rather than silently omitted. See `references/aws-s3-analysis-to-sheets.md`.
- For public ecommerce product-ranking exports, put the popularity proxy and caveats in a `Methodology` tab, use Drive API `supportsAllDrives=True` for shared-drive folders, expand Sheet grid limits before writing thousands of rows, and verify the Drive parent plus top/tail rows. When the task asks for “private label” or similar retailer-controlled products, do not overclaim from a marketing proxy such as Direct/Exclusive; add classification/confidence/evidence columns and separate high-confidence, likely, manual-review, and excluded tabs. See `references/public-ecommerce-scrape-to-sheets.md`.
- When a Drive folder URL points at a shared drive, `drive search "'<folder_id>' in parents"` may return empty even though direct access works. Use the Python Drive client with `supportsAllDrives=True`, `includeItemsFromAllDrives=True`, and `corpora='allDrives'` for folder metadata/listing. To create a Google Sheet directly inside that shared-drive folder, use Drive `files().create(body={'name': title, 'mimeType': 'application/vnd.google-apps.spreadsheet', 'parents': [folder_id]}, supportsAllDrives=True)` rather than `spreadsheets.create`, then write tabs/values with Sheets API. Verify the created file’s `parents` contains the target folder.
- For combining and re-ranking product Sheets where review count should matter but the score must stay on a 0-5 rating scale, preserve source rank and original score columns, add a `Methodology` tab, and use a bounded Bayesian weighted-rating formula in the Sheet itself: `WR=(v*R+m*C)/(v+m)`, where `v` is review count, `R` is item rating, `C` is the mean rating across the combined dataset, and `m` is the chosen prior/credibility review count. Put `C` and `m` in methodology cells and have the score column reference those cells so the formula is auditable/tunable. Read back the formula with `valueRenderOption=FORMULA`, a named sanity-check item the user mentioned (e.g. item/rank/score), and the top rows before reporting completion.
- After updates, read back the target ranges and check for missing required fields (e.g. count rows where any enriched columns are blank) before reporting completion.
- For Sheets that track package shipments, see `references/package-tracking-for-sheets.md` for carrier lookup patterns (FedEx/UPS/USPS), grouping repeated tracking numbers, approval-before-write workflow, and verification steps.

### Docs

```bash
# Read
$GAPI docs get DOC_ID
```
# Create a new Doc (optionally seeded with body text)
$GAPI docs create --title "Meeting Notes"
$GAPI docs create --title "Draft" --body "First paragraph..."

# Append text to the end of an existing Doc
$GAPI docs append DOC_ID --text "Additional content to append"
```

## Output Format

All commands return JSON. Parse with `jq` or read directly. Key fields:

- **Gmail search**: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- **Gmail get**: `{id, threadId, from, to, subject, date, labels, body}`
- **Gmail send/reply**: `{status: "sent", id, threadId}`
- **Calendar list**: `[{id, summary, start, end, location, description, htmlLink}]`
- **Calendar create**: `{status: "created", id, summary, htmlLink}`
- **Drive search**: `[{id, name, mimeType, modifiedTime, webViewLink}]`
- **Drive get**: `{id, name, mimeType, modifiedTime, size, webViewLink, parents, owners}`
- **Drive upload**: `{status: "uploaded", id, name, mimeType, webViewLink}`
- **Drive download**: `{status: "downloaded", id, name, path, mimeType}`
- **Drive create-folder**: `{status: "created", id, name, webViewLink}`
- **Drive share**: `{status: "shared", permissionId, fileId, role, type}`
- **Drive delete**: `{status: "trashed" | "deleted", fileId, permanent}`
- **Contacts list**: `[{name, emails: [...], phones: [...]}]`
- **Sheets get**: `[[cell, cell, ...], ...]`
- **Sheets create**: `{status: "created", spreadsheetId, title, spreadsheetUrl}`
- **Docs create**: `{status: "created", documentId, title, url}`
- **Docs append**: `{status: "appended", documentId, inserted_at, characters}`

## Rules

1. **Never send email, create/delete calendar events, delete Drive files, share files, or modify Docs/Sheets without confirming with the user first.** Show what will be done (recipients, file IDs, content, share role) and ask for approval. If the user explicitly pre-authorizes a bounded class of outbound emails/forms in the task itself (for example: “you do not need to ask for permission to send emails / fill out forms”), treat that as the approval for those in-scope sends, but still keep the messages truthful, professional, and limited to the stated objective. For `drive delete`, prefer the default trash (reversible) over `--permanent`.
2. **Check auth before first use** — run `setup.py --check`. If it fails, guide the user through setup.
3. **Use the Gmail search syntax reference** for complex queries — load it with `skill_view("google-workspace", file_path="references/gmail-search-syntax.md")`.
4. **Calendar times must include timezone** — always use ISO 8601 with offset (e.g., `2026-03-01T10:00:00-06:00`) or UTC (`Z`).
5. **Respect rate limits** — avoid rapid-fire sequential API calls. Batch reads when possible.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Run setup Steps 2-5 above |
| `REFRESH_FAILED` | Token revoked or expired — redo Steps 3-5 |
| `HttpError 403: Insufficient Permission` | Missing API scope — `$GSETUP --revoke` then redo Steps 3-5 |
| `AUTHENTICATED (partial)` or "Token missing scopes" | New write capabilities (Gmail send/modify, Drive write/delete, Docs create/edit) require re-authorization. Run `$GSETUP --auth-url`, have the user approve the newest URL, then exchange with `$GSETUP --auth-code "PASTED_REDIRECT_URL"`; use `$GSETUP --revoke` first only if the normal consent refresh does not add the missing scopes. |
| `error[auth]: ... google_token.json: missing field type` while `$GSETUP --check` says authenticated | The `gws` backend may be reading Hermes' token file directly without the Python wrapper's token normalization. For a one-off command, force the Python client fallback by running `google_api.py` with a PATH that excludes the `gws` binary (but keeps Python), e.g. `PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin /abs/path/to/python google_api.py ...`. Alternatively normalize the token file only if you understand the credential format. |
| `HttpError 403: Access Not Configured` | API not enabled — user needs to enable it in Google Cloud Console |
| `ModuleNotFoundError` | Run `$GSETUP --install-deps` |
| Advanced Protection blocks auth | Workspace admin must allowlist the OAuth client ID |

## Revoking Access

```bash
$GSETUP --revoke
```
