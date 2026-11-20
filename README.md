# InvoiceFlow

Accounts-payable automation: evaluated invoice extraction, approval-gated agent writes,
tamper-evident audit log and cost per invoice. Built on AWS with Claude on Amazon Bedrock.

**Status:** Milestone 0 (foundations). The full README (demo, architecture, eval results,
cost per run, 5-minute setup) ships with v1.0.

- Planned architecture and milestones: [docs/architecture.md](docs/architecture.md)
- Decisions: [docs/adr/](docs/adr/)

## Quick start (Milestone 0)

```bash
uv sync
uv run pytest -q
aws login --profile invoiceflow && export AWS_PROFILE=invoiceflow AWS_REGION=us-east-2
uv run python scripts/smoke_llm.py --provider both --tier haiku
```
