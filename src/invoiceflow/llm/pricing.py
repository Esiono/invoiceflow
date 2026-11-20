"""Token prices and cost per call.

Claude API list prices in USD per million tokens (MTok), checked 2026-11-19 against
Anthropic's pricing docs and launch notes. Cache-write prices for Haiku and Opus 1h are
derived from the standard multipliers (5m write = 1.25x input, 1h write = 2x input);
confirm on the pricing page. Bedrock prices are not verified yet: Bedrock cost computed
here is an estimate until reconciled with Cost Explorer (milestone M3).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

PER_MTOK = Decimal(1_000_000)


@dataclass(frozen=True)
class Rates:
    input: Decimal
    output: Decimal
    cache_write_5m: Decimal
    cache_write_1h: Decimal
    cache_read: Decimal


@dataclass(frozen=True)
class ModelPricing:
    base: Rates
    long_context: Rates | None = None
    # If total prompt tokens exceed this, long_context rates apply to the WHOLE request.
    long_context_threshold: int | None = None

    def rates_for(self, prompt_tokens: int) -> Rates:
        if (
            self.long_context is not None
            and self.long_context_threshold is not None
            and prompt_tokens > self.long_context_threshold
        ):
            return self.long_context
        return self.base


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0  # uncached input only
    output_tokens: int = 0
    cache_write_5m_tokens: int = 0
    cache_write_1h_tokens: int = 0
    cache_read_tokens: int = 0

    @property
    def prompt_tokens(self) -> int:
        """Full prompt length: uncached + written to cache + read from cache."""
        return (
            self.input_tokens
            + self.cache_write_5m_tokens
            + self.cache_write_1h_tokens
            + self.cache_read_tokens
        )


def _rates(input_: str, output: str, write_5m: str, write_1h: str, read: str) -> Rates:
    return Rates(
        Decimal(input_), Decimal(output), Decimal(write_5m), Decimal(write_1h), Decimal(read)
    )


PRICING: dict[str, ModelPricing] = {
    "haiku": ModelPricing(
        base=_rates("0.10", "0.50", "0.125", "0.20", "0.01"),
        long_context=_rates("0.50", "2.50", "0.625", "1.00", "0.05"),
        long_context_threshold=100_000,
    ),
    "haiku-4-5": ModelPricing(base=_rates("1.00", "5.00", "1.25", "2.00", "0.10")),
    "sonnet": ModelPricing(base=_rates("2.00", "10.00", "2.50", "4.00", "0.10")),
    "opus": ModelPricing(base=_rates("4.00", "20.00", "5.00", "8.00", "0.20")),
}


def cost_usd(tier: str, usage: TokenUsage) -> Decimal:
    """Cost of one call in USD. Decimal avoids float rounding on tiny amounts."""
    try:
        pricing = PRICING[tier]
    except KeyError as exc:
        raise ValueError(f"No pricing for tier {tier!r}") from exc
    r = pricing.rates_for(usage.prompt_tokens)
    total = (
        usage.input_tokens * r.input
        + usage.output_tokens * r.output
        + usage.cache_write_5m_tokens * r.cache_write_5m
        + usage.cache_write_1h_tokens * r.cache_write_1h
        + usage.cache_read_tokens * r.cache_read
    )
    return total / PER_MTOK
