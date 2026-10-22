"""Offline pagination contract: explicit limits bound requests; absent limits keep all pages."""

from urllib.parse import parse_qs, urlparse

import pytest
from openbb_fmp.models.government_trades import FMPGovernmentTradesFetcher as Model


@pytest.mark.asyncio
@pytest.mark.parametrize("limit,expected_rows,expected_requests", [(2, 2, 1), (None, 102, 2)])
async def test_symbol_pagination_respects_explicit_limit_without_truncating_default(
    monkeypatch, limit, expected_rows, expected_requests
):
    """Avoid downloading every page only to discard it after transformation."""
    calls = []

    async def request(url, **kwargs):
        query = parse_qs(urlparse(url).query)
        page = int(query["page"][0])
        size = int(query["limit"][0])
        calls.append((page, size))
        count = size if page == 0 else 2
        return [
            {
                "ticker": "AAPL",
                "disclosureDate": f"2026-10-{21 - (i % 20):02d}",
                "transactionDate": "2026-09-01",
                "office": str(page * 100 + i),
                "type": "Purchase",
            }
            for i in range(count)
        ]

    monkeypatch.setattr("openbb_core.provider.utils.helpers.amake_request", request)
    q = Model.transform_query({"symbol": "AAPL", "chamber": "house", "limit": limit})
    raw = await Model.aextract_data(q, {"fmp_api_key": "fixture"})
    assert len(raw) == expected_rows
    assert len(calls) == expected_requests
