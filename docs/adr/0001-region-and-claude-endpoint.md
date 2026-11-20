# ADR-0001: Region us-east-2 and the bedrock-mantle Messages API

Status: accepted (2026-11-19, revised the same day)

## Context
We need one AWS region and one way to call Claude on Bedrock, plus the Claude API for features
Bedrock lacks (Message Batches, server tools).

The AWS account was created with "Sign up for AWS (new)". That experience puts resources in a
project whose region is assigned from the contact-address country: US East (Ohio) us-east-2
for the Americas. Regional resources can only be created in the project's region.

## Options
1. us-east-2 (assigned) + bedrock-mantle Messages API (same request shape as the Claude API).
2. us-west-2 (closest to Mexicali): requires "Activate advanced AWS features" or a separate
   "Sign up for AWS (advanced)" account.
3. mx-central-1 (Queretaro), to keep data in Mexico.

## Decision
Option 1. us-east-2 supports in-region routing on bedrock-mantle, so the code path is unchanged.
Network distance to Ohio adds tens of milliseconds, which is negligible next to model latency.
Mantle lets one wrapper (`complete()`) serve both providers. Mantle does not need the Anthropic
first-time-use form; we submitted it anyway for later bedrock-runtime use (batch inference).

Option 2 rejected for now: it adds account setup work with no benefit for this project. Revisit if
a needed service is unavailable in the new experience (checked per milestone).

Option 3 rejected: Claude in mx-central-1 runs on global cross-Region inference only, so model
calls leave Mexico anyway; the mantle endpoint list does not include it; and fewer services are
there. The LFPDPPP allows international transfers with notice and consent, so in-country storage
is not required for this project. Revisit if a client requires data at rest in Mexico.

## Consequences
- Bedrock prices are estimates until reconciled with Cost Explorer (M3).
- Features missing on mantle (Message Batches, server tools, Files API, server-side fallback) go to the Claude API.
- Regional (pinned) endpoints cost 10% more; we use them only if a data-residency need appears.
- Human access uses AWS Builder ID and `aws login` (temporary credentials), not IAM Identity Center,
  which the new experience does not offer. The project spend limit is the hard cost cap; the
  Terraform budget gives earlier email alerts.
