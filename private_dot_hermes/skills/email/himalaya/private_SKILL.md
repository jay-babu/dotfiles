---
name: himalaya
description: "Himalaya CLI: IMAP/SMTP email from terminal."
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.

This skill is separate from the Hermes Email gateway adapter. The gateway
adapter lets people email the agent and uses Hermes' built-in IMAP/SMTP
adapter; this skill lets the agent operate a mailbox from terminal tools and
requires the external `himalaya` CLI.

## References

- `references/configuration.md` (config file setup + IMAP/SMTP authentication)
- `references/message-composition.md` (MML syntax for composing emails)
- `references/gmail-gws-oauth.md` (reuse Hermes Google Workspace OAuth client for Gmail IMAP/SMTP, including scope and feature pitfalls)
- `references/mise-cargo-features.md` (mise Cargo backend config and clean reinstall verification for `+oauth2 +keyring` builds)

## Prerequisites

1. Himalaya CLI installed (`himalaya --version` to verify)
   - For OAuth2 Gmail/Workspace auth, verify the binary includes `+oauth2 +keyring` in `himalaya --version`. The default Cargo feature set may omit these; reinstall with `cargo install himalaya --features oauth2 --locked --force` (or the equivalent mise Cargo backend config) if missing.
   - If managed by mise, configure the Cargo tool as `"cargo:himalaya" = { version = "latest", features = "oauth2" }` and validate with a clean `mise uninstall -y cargo:himalaya && mise install cargo:himalaya`; see `references/mise-cargo-features.md`.
2. A configuration file at `~/.config/himalaya/config.toml`
3. IMAP/SMTP credentials configured (password stored securely)

### Installation

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Configuration Setup

Run the interactive wizard to set up an account:

```bash
himalaya account configure
```

Or create `~/.config/himalaya/config.toml` manually:

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"

# Folder aliases (himalaya v1.2.0+ syntax). Required whenever the
# server's folder names don't match himalaya's canonical names
# (inbox/sent/drafts/trash). Gmail is the common case — see
# `references/configuration.md` for the `[Gmail]/Sent Mail` mapping.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

> **Heads up on the alias syntax.** Pre-v1.2.0 docs used a
> `[accounts.NAME.folder.alias]` sub-section (singular `alias`).
> v1.2.0 silently ignores that form — TOML parses fine, but the
> alias resolver never reads it, so every lookup falls through to
> the canonical name. On Gmail this means save-to-Sent fails *after*
> SMTP delivery succeeds, and `himalaya message send` exits non-zero.
> Any caller (agent, script, user) that retries on that exit code
> will re-run the entire send — including SMTP — producing duplicate
> emails to recipients. Always use `folder.aliases.X` (plural, dotted
> keys, directly under `[accounts.NAME]`).

## Gmail with Hermes Google Workspace OAuth

When a Hermes `google-workspace`/`gws` setup already exists, Himalaya can reuse the same Google OAuth **client** for Gmail IMAP/SMTP, but not necessarily the existing token. Gmail IMAP/SMTP XOAUTH2 requires the full mail scope `https://mail.google.com/`; typical Gmail API scopes such as `gmail.readonly`, `gmail.modify`, and `gmail.send` are insufficient. See `references/gmail-gws-oauth.md` for a config template and verification sequence.

## Hermes Integration Notes

- **Reading, listing, searching, moving, deleting** all work directly through the terminal tool
- **Composing/replying/forwarding** — piped input (`cat << EOF | himalaya template send`) is recommended for reliability. Interactive `$EDITOR` mode works with `pty=true` + background + process tool, but requires knowing the editor and its commands
- Use `--output json` for structured output that's easier to parse programmatically
- The `himalaya account configure` wizard requires interactive input — use PTY mode: `terminal(command="himalaya account configure", pty=true)`

## Common Operations

### List Folders

```bash
himalaya folder list
```

### List Emails

List emails in INBOX (default):

```bash
himalaya envelope list
```

List emails in a specific folder:

```bash
himalaya envelope list --folder "Sent"
```

List with pagination:

```bash
himalaya envelope list --page 1 --page-size 20
```

### Search Emails

```bash
himalaya envelope list from john@example.com subject meeting
```

### Read an Email

Read email by ID (shows plain text):

```bash
himalaya message read 42
```

Export raw MIME:

```bash
himalaya message export 42 --full
```

### Reply to an Email

To reply non-interactively from Hermes, read the original message, compose a reply, and pipe it:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Or build the reply manually:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Reply-all (interactive — needs $EDITOR, use template approach above instead):

```bash
himalaya message reply 42 --all
```

### Forward an Email

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### Write a New Email

**Non-interactive (use this from Hermes)** — pipe the message via stdin:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

Or with headers flag:

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Note: `himalaya message write` without piped input opens `$EDITOR`. This works with `pty=true` + background mode, but piping is simpler and more reliable.

### Move/Copy Emails

Move to folder:

```bash
himalaya message move 42 "Archive"
```

Copy to folder:

```bash
himalaya message copy 42 "Important"
```

### Delete an Email

```bash
himalaya message delete 42
```

### Manage Flags

Add flag:

```bash
himalaya flag add 42 --flag seen
```

Remove flag:

```bash
himalaya flag remove 42 --flag seen
```

## Multiple Accounts

List accounts:

```bash
himalaya account list
```

Use a specific account (in Himalaya v1.2.0, `--account` is a subcommand option, not a top-level option):

```bash
himalaya envelope list --account work
himalaya folder list --account work
```

## Attachments

Save attachments from a message:

```bash
himalaya attachment download 42
```

Save to specific directory:

```bash
himalaya attachment download 42 --dir ~/Downloads
```

## Output Formats

Most commands support `--output` for structured output:

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## Debugging

Enable debug logging:

```bash
RUST_LOG=debug himalaya envelope list
```

Full trace with backtrace:

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## Tips

- Use `himalaya --help` or `himalaya <command> --help` for detailed usage.
- Message IDs are relative to the current folder; re-list after folder changes.
- For composing rich emails with attachments, use MML syntax (see `references/message-composition.md`).
- Store passwords securely using `pass`, system keyring, or a command that outputs the password.
- For outbound sends, do not blindly retry after a timeout or non-zero exit: SMTP delivery can succeed before saving a copy to Sent or before the CLI returns. First verify by checking Sent/searching for the recipient+subject or using another configured mail backend (for example the Google Workspace Gmail API) before retrying, to avoid duplicate emails.
