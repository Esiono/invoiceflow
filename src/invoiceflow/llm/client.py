"""Every Claude call goes through complete(): pick the model, call, check stop_reason, price it."""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

import anthropic

from invoiceflow.llm.pricing import TokenUsage, cost_usd

Provider = Literal["bedrock", "anthropic"]

# Pinned model IDs. Change them only here, and only after an eval run.
# Bedrock IDs checked 2026-11-19 at:
# platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock
MODEL_IDS: dict[str, dict[str, str]] = {
    "bedrock": {
        "haiku": "anthropic.claude-haiku-5-5",
        "haiku-4-5": "anthropic.claude-haiku-4-5",
        "sonnet": "anthropic.claude-sonnet-5-5",
        "opus": "anthropic.claude-opus-5-5",
    },
    "anthropic": {
        "haiku": "claude-haiku-5-5",
        "haiku-4-5": "claude-haiku-4-5",
        "sonnet": "claude-sonnet-5-5",
        "opus": "claude-opus-5-5",
    },
}

# stop_reason values returned normally. Everything else raises.
NORMAL_STOP_REASONS = frozenset({"end_turn", "stop_sequence", "tool_use"})


@dataclass(frozen=True)
class LLMResult:
    provider: str
    tier: str
    model: str
    text: str
    stop_reason: str
    usage: TokenUsage
    cost_usd: Decimal
    latency_ms: int
    request_id: str | None


class LLMError(Exception):
    """Carries the result, because a refused or truncated call still costs money."""

    def __init__(self, message: str, result: LLMResult) -> None:
        super().__init__(message)
        self.result = result


class RefusalError(LLMError):
    """stop_reason == 'refusal': the model declined. Do not retry the same input."""


class IncompleteResponseError(LLMError):
    """stop_reason == 'max_tokens': output was cut off. Caller decides: raise limit or fail."""


class UnexpectedStopReasonError(LLMError):
    """Any stop_reason this code does not handle yet (e.g. pause_turn)."""


def usage_from_sdk(usage: Any) -> TokenUsage:
    """Convert the SDK usage object. Cache fields may be missing or None."""
    cache_creation = getattr(usage, "cache_creation", None)
    if cache_creation is not None:
        write_5m = getattr(cache_creation, "ephemeral_5m_input_tokens", 0) or 0
        write_1h = getattr(cache_creation, "ephemeral_1h_input_tokens", 0) or 0
    else:
        write_5m = getattr(usage, "cache_creation_input_tokens", 0) or 0
        write_1h = 0
    return TokenUsage(
        input_tokens=usage.input_tokens or 0,
        output_tokens=usage.output_tokens or 0,
        cache_write_5m_tokens=write_5m,
        cache_write_1h_tokens=write_1h,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
    )


def make_client(
    provider: Provider,
    *,
    aws_region: str = "us-west-2",
    api_key: str | None = None,
    max_retries: int = 4,
    timeout_s: float = 60.0,
) -> Any:
    """SDK retries 408/409/429/>=500 and connection errors with backoff; never 400/401."""
    if provider == "bedrock":
        # SigV4 via the standard AWS credential chain (our SSO profile).
        return anthropic.AnthropicBedrockMantle(
            aws_region=aws_region, max_retries=max_retries, timeout=timeout_s
        )
    if provider == "anthropic":
        if not api_key:
            raise ValueError("api_key is required for the Claude API")
        return anthropic.Anthropic(api_key=api_key, max_retries=max_retries, timeout=timeout_s)
    raise ValueError(f"Unknown provider {provider!r}")


def complete(
    client: Any,
    *,
    provider: Provider,
    tier: str,
    messages: list[dict[str, Any]],
    system: str | None = None,
    max_tokens: int = 1024,
) -> LLMResult:
    try:
        model = MODEL_IDS[provider][tier]
    except KeyError as exc:
        raise ValueError(f"No model for provider={provider!r} tier={tier!r}") from exc

    kwargs: dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system is not None:
        kwargs["system"] = system

    started = time.perf_counter()
    message = client.messages.create(**kwargs)
    latency_ms = int((time.perf_counter() - started) * 1000)

    usage = usage_from_sdk(message.usage)
    text = "".join(b.text for b in message.content if getattr(b, "type", None) == "text")
    result = LLMResult(
        provider=provider,
        tier=tier,
        model=message.model,
        text=text,
        stop_reason=message.stop_reason,
        usage=usage,
        cost_usd=cost_usd(tier, usage),
        latency_ms=latency_ms,
        request_id=getattr(message, "_request_id", None),
    )

    if message.stop_reason in NORMAL_STOP_REASONS:
        return result
    if message.stop_reason == "max_tokens":
        raise IncompleteResponseError(f"Output truncated at max_tokens={max_tokens}", result)
    if message.stop_reason == "refusal":
        raise RefusalError("Model refused the request", result)
    raise UnexpectedStopReasonError(f"Unhandled stop_reason {message.stop_reason!r}", result)
