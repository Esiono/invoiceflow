from decimal import Decimal

import pytest

from invoiceflow.llm.pricing import TokenUsage, cost_usd


def test_haiku_short_prompt_uses_base_rates():
    usage = TokenUsage(input_tokens=1_000, output_tokens=500)
    # 1000 * 0.10 / 1e6 + 500 * 0.50 / 1e6
    assert cost_usd("haiku", usage) == Decimal("0.00035")


def test_haiku_long_prompt_uses_long_rates_for_whole_request():
    usage = TokenUsage(input_tokens=120_000, output_tokens=1_000)
    # 120000 * 0.50 / 1e6 + 1000 * 2.50 / 1e6
    assert cost_usd("haiku", usage) == Decimal("0.0625")


def test_cache_reads_count_toward_long_context_threshold():
    usage = TokenUsage(input_tokens=50_000, cache_read_tokens=60_000)
    # prompt = 110k > 100k -> long rates: 50000 * 0.50 + 60000 * 0.05, / 1e6
    assert cost_usd("haiku", usage) == Decimal("0.028")


def test_sonnet_with_cache_reads():
    usage = TokenUsage(input_tokens=2_000, output_tokens=300, cache_read_tokens=10_000)
    # 2000 * 2 + 300 * 10 + 10000 * 0.10, / 1e6
    assert cost_usd("sonnet", usage) == Decimal("0.008")


def test_zero_usage_costs_zero():
    assert cost_usd("opus", TokenUsage()) == Decimal("0")


def test_unknown_tier_raises():
    with pytest.raises(ValueError):
        cost_usd("gpt", TokenUsage())
