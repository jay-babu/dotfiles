#!/usr/bin/env bash
set -euo pipefail

# Install AWS IAM Roles Anywhere credential helper for Hermes AWS profiles.
# This is intentionally global because aws_signing_helper is not available via mise/asdf.

if [ "$(uname -s)" != "Linux" ] || [ "$(uname -m)" != "x86_64" ]; then
  echo "Skipping aws_signing_helper install: unsupported platform $(uname -s)/$(uname -m)"
  exit 0
fi

version="1.8.2"
url="https://rolesanywhere.amazonaws.com/releases/${version}/X86_64/Linux/Amzn2023/aws_signing_helper"
expected_sha256="7addb6eb6e84fcee6c9c013b895ea6ad01672188f1a52a61118d22c977c4432e"
dest="/usr/local/bin/aws_signing_helper"

if [ -x "$dest" ]; then
  current_sha256="$(sha256sum "$dest" | awk '{print $1}')"
  if [ "$current_sha256" = "$expected_sha256" ]; then
    exit 0
  fi
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
curl -fsSL "$url" -o "$tmp"
actual_sha256="$(sha256sum "$tmp" | awk '{print $1}')"
if [ "$actual_sha256" != "$expected_sha256" ]; then
  echo "aws_signing_helper checksum mismatch: got $actual_sha256 expected $expected_sha256" >&2
  exit 1
fi
install -m 0755 "$tmp" "$dest"
