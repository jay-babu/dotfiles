# AWS IAM Roles Anywhere for Hermes

This directory intentionally stores the local certificate material used by the `gamma` and `production` AWS CLI profiles in `~/.aws/config`.

Tracked by chezmoi:

- `~/.aws/config` profile definitions
- this README
- `run_once_install-aws-signing-helper.sh`, which installs `/usr/local/bin/aws_signing_helper`

Not tracked by chezmoi because it is secret or host-specific:

- `hermes-agent.key` — leaf private key used by the Hermes host
- `hermes-agent-ca.key` — private CA key; ideally move/export this to offline secret storage after setup
- `hermes-agent.crt` — leaf certificate, valid until 2026-10-31
- `hermes-agent-ca.crt` — public CA certificate uploaded as the Roles Anywhere trust anchor

AWS account/profile mapping:

- `gamma` → account `165569969323` / role `HermesAgentPowerUser` via IAM Roles Anywhere
- `production` → account `928004597368` / role `HermesAgentReadOnly` via IAM Roles Anywhere

Roles Anywhere resources are in `us-east-1` in each target account.

Verification:

```bash
aws sts get-caller-identity --profile gamma
aws sts get-caller-identity --profile production
```

Certificate rotation outline:

1. Use the CA key to issue a new leaf certificate with CN `hermes-agent.usemargin.dev`.
2. Replace `~/.aws/rolesanywhere/hermes-agent.crt` and `~/.aws/rolesanywhere/hermes-agent.key` on this host.
3. Keep permissions tight: private keys should be mode `600`, directory should be mode `700`.
4. Verify both AWS profiles with `aws sts get-caller-identity`.

Emergency revocation:

- Disable the `HermesAgentTrustAnchor` or `HermesAgentProfile` in the affected AWS account, or update the role trust policy to remove/alter the certificate subject constraints.
