# ADR-0001: Region us-west-2 and the bedrock-mantle Messages API

Status: accepted (2026-11-19)

## Context
We need one AWS region and one way to call Claude on Bedrock, plus the Claude API for features
Bedrock lacks (Message Batches, server tools).

## Options
1. us-west-2 + bedrock-mantle Messages API (same request shape as the Claude API).
2. us-east-1 + bedrock-runtime Converse API (AWS-normalized request shape).
3. mx-central-1 (Queretaro), to keep data in Mexico.

## Decision
Option 1. us-west-2 is the closest region to Mexicali that supports in-region routing on mantle
and the services the portfolio needs. Mantle lets one wrapper (`complete()`) serve both providers.
Mantle does not need the Anthropic first-time-use form; we submitted it anyway for later
bedrock-runtime use (batch inference).

Option 3 rejected: Claude in mx-central-1 runs on global cross-Region inference only, so model
calls leave Mexico anyway; the mantle endpoint list does not include it; and fewer services are
there. The LFPDPPP allows international transfers with notice and consent, so in-country storage
is not required for this project. Revisit if a client requires data at rest in Mexico.

## Consequences
- Bedrock prices are estimates until reconciled with Cost Explorer (M3).
- Features missing on mantle (Message Batches, server tools, Files API, server-side fallback) go to the Claude API.
- Regional (pinned) endpoints cost 10% more; we use them only if a data-residency need appears.
