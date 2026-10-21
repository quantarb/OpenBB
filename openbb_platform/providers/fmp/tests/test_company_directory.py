# ruff: noqa: SIM117
"""Offline company-directory provider regression tests."""

import asyncio

import pytest
from openbb_fmp.models.equity_search import (
    FMPEquitySearchFetcher as F,
    FMPEquitySearchQueryParams as Q,
)


def test_full_directory_no_screener_limit_and_financial_list(monkeypatch):
    """Full directory no screener limit and financial list."""
    import openbb_fmp.utils.helpers as h

    calls = []

    async def data(url, **kwargs):
        """Return fixture directory records."""
        calls.append(url)
        return [{"symbol": "AAPL", "companyName": "Apple"}, {"symbol": "ETF", "name": "Fund", "type": "etf"}]

    monkeypatch.setattr(h, "get_data", data)
    query = Q()
    raw = asyncio.run(F.aextract_data(query, {"fmp_api_key": "fixture"}))
    assert len(F.transform_data(query, raw)) == 2
    assert "/stock-list?" in calls[0] and "limit=" not in calls[0]
    asyncio.run(F.aextract_data(Q(directory="financial_statements"), {}))
    assert "/financial-statement-symbol-list?" in calls[1]
    assert len(F.transform_data(Q(query="AAPL", is_symbol=True), raw)) == 1


def test_invalid_directory_payload_is_not_empty_success(monkeypatch):
    """Invalid directory payload is not empty success."""
    import openbb_fmp.utils.helpers as h

    async def data(*args, **kwargs):
        """Return fixture directory records."""
        return {"error": "not a complete directory"}

    monkeypatch.setattr(h, "get_data", data)
    with pytest.raises(ValueError, match="directory"):
        asyncio.run(F.aextract_data(Q(), {}))
