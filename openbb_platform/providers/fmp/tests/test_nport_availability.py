"""Availability-aware N-PORT selection, without vendor access."""

import pytest
from openbb_fmp.models.nport_disclosure import FMPNportDisclosureFetcher as Model


@pytest.mark.asyncio
async def test_default_uses_latest_vendor_reported_period_not_calendar_guess(monkeypatch):
    """A newly ended quarter must not be presumed filed."""
    calls = []

    async def get(url, **kwargs):
        calls.append(url)
        return (
            [{"date": "2026-03-31", "year": 2026, "quarter": 1}, {"date": "2026-06-30", "year": 2026, "quarter": 2}]
            if "disclosure-dates?" in url
            else []
        )

    monkeypatch.setattr("openbb_fmp.utils.helpers.get_data_many", get)
    q = Model.transform_query({"symbol": "VWO"})
    await Model.aextract_data(q, {"fmp_api_key": "fixture"})
    assert (q.year, q.quarter) == (2026, 2)
    assert len(calls) == 2 and "year=2026&quarter=2" in calls[1]


@pytest.mark.asyncio
async def test_explicit_period_is_honored_without_silent_fallback(monkeypatch):
    """No older substitution for an explicit period."""
    calls = []

    async def get(url, **kwargs):
        calls.append(url)
        return []

    monkeypatch.setattr("openbb_fmp.utils.helpers.get_data_many", get)
    q = Model.transform_query({"symbol": "VWO", "year": 2026, "quarter": 3})
    assert await Model.aextract_data(q, {"fmp_api_key": "fixture"}) == []
    assert len(calls) == 1 and "disclosure-dates" not in calls[0]


def test_acceptance_timestamp_is_preserved_alongside_reporting_date():
    """Retain both source dates with no invented lag."""
    q = Model.transform_query({"symbol": "VWO"})
    row = Model.transform_data(
        q,
        [
            {
                "symbol": "AAPL",
                "name": "Apple",
                "pctVal": 1,
                "valUsd": 123,
                "date": "2026-06-30",
                "acceptedDate": "2026-08-29T12:34:56Z",
            }
        ],
    )[0]
    assert str(row.as_of) == "2026-06-30"
    assert row.accepted_date.isoformat() == "2026-08-29T12:34:56+00:00"
