#!/usr/bin/env python3
"""Silently move selected Gmail notifications to Trash.

Used by a Hermes cron job for classes the user asked to always trash.
Prints nothing on success so the no_agent cron job stays silent.
"""

import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_PATH = Path.home() / ".hermes/google_token.json"

RULES = [
    {
        "name": "City Hive marketing campaign opportunities",
        "query": '-in:trash from:do-not-reply@cityhive.net subject:"Marketing Campaign Opportunity from City Hive"',
        "headers": ["From", "Subject"],
        "checks": {
            "from": "do-not-reply@cityhive.net",
            "subject": "Marketing Campaign Opportunity from City Hive",
        },
    },
    {
        "name": "GitHub TransformityPOSFrontend Stably Tests failed",
        "query": '-in:trash from:notifications@github.com to:TransformityPOSFrontend@noreply.github.com subject:"Run failed: Stably Tests (Main)"',
        "headers": ["From", "To", "Subject"],
        "checks": {
            "from": "notifications@github.com",
            "to": "TransformityPOSFrontend@noreply.github.com",
            "subject": "Run failed: Stably Tests (Main)",
        },
    },
]


def load_service():
    raw = json.loads(TOKEN_PATH.read_text())
    scopes = raw.get("scopes") or raw.get("scope", "").split()
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), scopes)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(json.dumps(json.loads(creds.to_json()), indent=2))
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def list_all(service, query):
    messages = []
    page_token = None
    while True:
        kwargs = {"userId": "me", "q": query, "maxResults": 100}
        if page_token:
            kwargs["pageToken"] = page_token
        resp = service.users().messages().list(**kwargs).execute()
        messages.extend(resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            return messages


def main():
    service = load_service()
    for rule in RULES:
        for meta in list_all(service, rule["query"]):
            msg = service.users().messages().get(
                userId="me",
                id=meta["id"],
                format="metadata",
                metadataHeaders=rule["headers"],
            ).execute()
            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
            # Gmail search tokenizes punctuation, so a query can return nearby-but-not-identical
            # subjects. Treat header checks as an allowlist and silently skip non-matches.
            if any(
                expected.lower() not in headers.get(header_name, "").lower()
                for header_name, expected in rule["checks"].items()
            ):
                continue
            service.users().messages().trash(userId="me", id=meta["id"]).execute()


if __name__ == "__main__":
    main()
