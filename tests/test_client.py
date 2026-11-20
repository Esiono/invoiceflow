from decimal import Decimal
from types import SimpleNamespace as NS

import pytest

from invoiceflow.llm.client import (
    IncompleteResponseError,
    RefusalError,
    UnexpectedStopReasonError,
    complete,
    usage_from_sdk,
)


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.messages = FakeMessages(response)


def make_message(stop_reason="end_turn", text="OK"):
    return NS(
        content=[NS(type="text", text=text)],
        stop_reason=stop_reason,
        model="claude-haiku-5-5",
        usage=NS(
            input_tokens=1_000,
            output_tokens=500,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
            cache_creation=None,
        ),
        _request_id="req_test",
    )


def call(client):
    return complete(
        client,
        provider="anthropic",
        tier="haiku",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=16,
    )


def test_end_turn_returns_text_cost_and_pinned_model():
    client = FakeClient(make_message())
    result = call(client)
    assert result.text == "OK"
    assert result.cost_usd == Decimal("0.00035")
    assert result.request_id == "req_test"
    sent = client.messages.calls[0]
    assert sent["model"] == "claude-haiku-5-5"
    assert "system" not in sent


def test_max_tokens_raises_but_keeps_cost():
    with pytest.raises(IncompleteResponseError) as exc:
        call(FakeClient(make_message(stop_reason="max_tokens")))
    assert exc.value.result.cost_usd == Decimal("0.00035")


def test_refusal_raises():
    with pytest.raises(RefusalError):
        call(FakeClient(make_message(stop_reason="refusal")))


def test_unhandled_stop_reason_raises():
    with pytest.raises(UnexpectedStopReasonError):
        call(FakeClient(make_message(stop_reason="pause_turn")))


def test_usage_reads_cache_write_breakdown():
    usage = NS(
        input_tokens=10,
        output_tokens=5,
        cache_read_input_tokens=None,
        cache_creation=NS(ephemeral_5m_input_tokens=100, ephemeral_1h_input_tokens=200),
    )
    u = usage_from_sdk(usage)
    assert (u.cache_write_5m_tokens, u.cache_write_1h_tokens, u.cache_read_tokens) == (100, 200, 0)
