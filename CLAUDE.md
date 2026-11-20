# CLAUDE.md

## Project
InvoiceFlow: invoices in (PDF, photo, CFDI XML) -> evaluated extraction -> agent proposes a bill ->
human approves -> idempotent write to QuickBooks sandbox -> hash-chained audit. AWS serverless, Terraform.
Plan and milestones: docs/architecture.md.

## Rules
- Python 3.12 with uv. Before calling a task done: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`.
- Terraform: `terraform fmt -recursive` and `terraform validate` in each stack.
- No secrets in code, tfvars, Terraform state, logs or test fixtures. The Anthropic key lives in SSM `/invoiceflow/dev/anthropic-api-key`.
- Model IDs only in `src/invoiceflow/llm/client.py`; prices only in `src/invoiceflow/llm/pricing.py`.
- Every LLM call goes through `invoiceflow.llm.client.complete`.
- Real invoices live in `data/private/` and are never committed.
- Explain every change in plain language. Eduardo must be able to explain each line. No new dependency without a reason.
