"""No network: admission covers bulk requests/pages and restores default behavior."""

import asyncio
from types import SimpleNamespace

import pytest
from openbb_core.provider.utils import helpers
from openbb_core.provider.utils.request_policy import policy_for, request_policy


class Session:
    def __init__(self, status=200):
        self.status = status
        self.calls = []
        self.closed = False

    async def request(self, method, url, **kwargs):
        self.calls.append(url)

        async def payload():
            return [{"row": 1}]

        return SimpleNamespace(status=self.status, headers={"Retry-After": "12"}, json=payload)

    async def close(self):
        self.closed = True


def test_bulk_requests_admitted_individually_without_exposing_query(monkeypatch):
    session = Session()

    async def factory(**kwargs):
        return session

    monkeypatch.setattr(helpers, "get_async_requests_session", factory)
    events = []

    def before():
        events.append("before")

    def after(status, retry_after):
        events.append((status, retry_after))

    async def execute():
        return await asyncio.gather(
            *[
                helpers.amake_request(
                    f"https://financialmodelingprep.com/stable/test?page={i}&apikey=secret", session=session
                )
                for i in range(3)
            ]
        )

    with request_policy({"financialmodelingprep.com"}, before, after):
        asyncio.run(execute())
        assert policy_for("https://another.example/x") is None
        assert policy_for("https://financialmodelingprep.com.evil.example/x") is None
        with pytest.raises(RuntimeError, match="already"):
            with request_policy({"financialmodelingprep.com"}, before, after):
                pass
    assert events == ["before", (200, "12")] * 3
    assert len(session.calls) == 3
    assert "secret" not in repr(events)
    assert policy_for("https://financialmodelingprep.com/x") is None


def test_denied_request_never_sent_and_policy_restored(monkeypatch):
    session = Session()

    async def factory(**kwargs):
        return session

    monkeypatch.setattr(helpers, "get_async_requests_session", factory)

    def denied():
        raise RuntimeError("budget exhausted")

    with pytest.raises(RuntimeError, match="budget"):
        with request_policy({"financialmodelingprep.com"}, denied, lambda *_: None):
            asyncio.run(helpers.amake_request("https://financialmodelingprep.com/x", session=session))
    assert session.calls == []
    assert policy_for("https://financialmodelingprep.com/x") is None


def test_429_recorded_before_provider_callback(monkeypatch):
    session = Session(429)

    async def factory(**kwargs):
        return session

    monkeypatch.setattr(helpers, "get_async_requests_session", factory)

    def after(status, retry_after):
        if status == 429:
            assert retry_after == "12"
            raise RuntimeError("retry later")
        assert status == 0

    with request_policy({"financialmodelingprep.com"}, lambda: None, after):
        with pytest.raises(RuntimeError, match="retry later"):
            asyncio.run(helpers.amake_request("https://financialmodelingprep.com/x", session=session))
    assert len(session.calls) == 1


def test_provider_callback_failure_is_visible_even_if_bulk_caller_discards_page(monkeypatch):
    session = Session()

    async def factory(**kwargs):
        return session

    monkeypatch.setattr(helpers, "get_async_requests_session", factory)
    statuses = []

    async def malformed(*_):
        raise ValueError("invalid vendor payload")

    with request_policy({"financialmodelingprep.com"}, lambda: None, lambda status, _: statuses.append(status)):
        with pytest.raises(ValueError):
            asyncio.run(
                helpers.amake_request("https://financialmodelingprep.com/x", session=session, response_callback=malformed)
            )
    assert statuses == [200, 0]
