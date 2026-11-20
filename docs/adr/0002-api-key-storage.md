# ADR-0002: Anthropic API key in SSM Parameter Store (SecureString)

Status: accepted (2026-11-19)

## Options
1. SSM Parameter Store SecureString, standard tier (free, KMS-encrypted with aws/ssm).
2. Secrets Manager (USD 0.40 per secret per month, managed rotation).

## Decision
Option 1. AWS cannot rotate an Anthropic key, so Secrets Manager adds cost without benefit.
The parameter is created with the AWS CLI, not Terraform, because Terraform would store the
plaintext value in state. Secrets Manager is used in M5 for QuickBooks OAuth tokens, which change.

## Consequences
Key rotation is manual: create a new key in the Claude Console, `put-parameter --overwrite`,
revoke the old key.
