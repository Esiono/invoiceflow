"""Call Claude once per provider and print one JSON line per call (cost, tokens, latency)."""

from __future__ import annotations

import argparse
import json
import sys

import anthropic

from invoiceflow import config
from invoiceflow.llm.client import LLMError, complete, make_client

PROMPT = "Reply with the single word OK."


def run(provider: str, tier: str) -> dict[str, object]:
    if provider == "bedrock":
        client = make_client("bedrock", aws_region=config.aws_region())
    else:
        client = make_client("anthropic", api_key=config.anthropic_api_key())
    r = complete(
        client,
        provider=provider,
        tier=tier,
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=16,
    )
    return {
        "provider": r.provider,
        "model": r.model,
        "stop_reason": r.stop_reason,
        "text": r.text,
        "input_tokens": r.usage.input_tokens,
        "output_tokens": r.usage.output_tokens,
        "cost_usd": str(r.cost_usd),
        "latency_ms": r.latency_ms,
        "request_id": r.request_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["bedrock", "anthropic", "both"], default="both")
    parser.add_argument("--tier", default="haiku")
    args = parser.parse_args()

    providers = ["bedrock", "anthropic"] if args.provider == "both" else [args.provider]
    failures = 0
    for provider in providers:
        try:
            print(json.dumps(run(provider, args.tier)))
        except LLMError as e:
            failures += 1
            print(
                json.dumps(
                    {
                        "provider": provider,
                        "error": type(e).__name__,
                        "stop_reason": e.result.stop_reason,
                        "cost_usd": str(e.result.cost_usd),
                    }
                )
            )
        except anthropic.APIStatusError as e:
            failures += 1
            print(
                json.dumps(
                    {
                        "provider": provider,
                        "error": type(e).__name__,
                        "status": e.status_code,
                        "message": str(e)[:300],
                    }
                )
            )
        except anthropic.APIConnectionError as e:
            failures += 1
            print(
                json.dumps(
                    {"provider": provider, "error": "APIConnectionError", "message": str(e)[:300]}
                )
            )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
