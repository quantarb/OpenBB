"""Offline contract tests: no vendor request or credential lookup."""

import json

import pytest
from openbb_fmp.models.reported_financials import FMPReportedFinancialsFetcher as Model


def test_raw_values_dates_and_zeros_are_preserved():
    """Keep full raw filing fields and source dates."""
    query = Model.transform_query({"symbol": "aapl", "period": "annual", "limit": 2})
    raw = {"date": "2025-09-30", "period": "FY", "calendarYear": "2025", "us-gaap_Assets": 123, "us-gaap_Gain": 0}
    row = Model.transform_data(query, [raw])[0]
    assert str(row.period_ending) == "2025-09-30"
    assert json.loads(row.raw_metadata) == raw
    assert row.model_dump()["us-gaap_Gain"] == 0
    assert row.fiscal_year == 2025


@pytest.mark.asyncio
async def test_full_raw_route_uses_bounded_query_and_existing_helper(monkeypatch):
    """Exercise adapter dispatch without a network request."""
    calls = []

    async def get(url, **kwargs):
        calls.append(url)
        return []

    monkeypatch.setattr("openbb_fmp.utils.helpers.get_data_many", get)
    query = Model.transform_query({"symbol": "AAPL", "period": "quarter", "limit": 2, "statement_type": "full"})
    assert await Model.aextract_data(query, {"fmp_api_key": "fixture"}) == []
    assert "/stable/financial-statement-full-as-reported?" in calls[0]
    assert "period=quarter" in calls[0] and "limit=2" in calls[0]


def test_default_statement_family_matches_standard_sdk_default():
    """Preserve the existing route's default balance-sheet selection."""
    assert Model.transform_query({"symbol": "AAPL"}).statement_type == "balance"
