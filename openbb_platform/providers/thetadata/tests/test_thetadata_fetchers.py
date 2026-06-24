from __future__ import annotations

import asyncio
from datetime import date

import pandas as pd

from openbb_thetadata.models.options_chains import (
    ThetaDataOptionsChainsFetcher,
    ThetaDataOptionsChainsQueryParams,
)
from openbb_thetadata.utils.helpers import normalize_thetadata_option_chain


def _raw_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "expiration": "2024-11-15",
                "strike": 220.0,
                "right": "PUT",
                "created": "2024-11-04 17:16:56.205000-05:00",
                "last_trade": "2024-11-04 15:59:33.359000-05:00",
                "open": 4.03,
                "high": 4.60,
                "low": 2.87,
                "close": 3.20,
                "volume": 4816,
                "count": 1108,
                "bid_size": 155,
                "bid_exchange": 9,
                "bid": 3.15,
                "bid_condition": 50,
                "ask_size": 43,
                "ask_exchange": 43,
                "ask": 3.25,
                "ask_condition": 50,
            },
            {
                "symbol": "AAPL",
                "expiration": "2024-11-15",
                "strike": 220.0,
                "right": "PUT",
                "created": "2024-11-04 17:16:56.205000-05:00",
                "last_trade": "2024-11-04 15:59:33.359000-05:00",
                "open": 4.03,
                "high": 4.60,
                "low": 2.87,
                "close": 3.20,
                "volume": 4816,
                "count": 1108,
                "bid_size": 155,
                "bid_exchange": 9,
                "bid": None,
                "bid_condition": 50,
                "ask_size": 43,
                "ask_exchange": 43,
                "ask": 3.25,
                "ask_condition": 50,
            },
        ]
    )


def test_normalize_thetadata_option_chain_builds_contract_symbol() -> None:
    frame = normalize_thetadata_option_chain(_raw_frame())
    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["contract_symbol"] == "AAPL241115P00220000"
    assert row["underlying_symbol"] == "AAPL"
    assert row["option_type"] == "put"
    assert row["eod_date"] == date(2024, 11, 4)
    assert row["dte"] == 11
    assert row["mark"] == 3.2


def test_transform_query_fills_single_day_defaults() -> None:
    query = ThetaDataOptionsChainsFetcher.transform_query({"symbol": "aapl"})
    assert query.symbol == "AAPL"
    assert query.start_date is not None
    assert query.end_date is not None


def test_transform_data_produces_standard_rows() -> None:
    query = ThetaDataOptionsChainsQueryParams(
        symbol="AAPL",
        date=date(2024, 11, 4),
        start_date=date(2024, 11, 4),
        end_date=date(2024, 11, 4),
    )
    result = ThetaDataOptionsChainsFetcher.transform_data(query, _raw_frame().to_dict(orient="records"))
    data = result.model_dump()
    assert data[0]["contract_symbol"] == "AAPL241115P00220000"
    assert data[0]["expiration"] == date(2024, 11, 15)
    assert data[0]["strike"] == 220.0
    assert data[0]["option_type"] == "put"
    assert data[0]["last_trade_price"] == 3.2


def test_aextract_data_uses_thetadata_client(monkeypatch) -> None:
    class FakeClient:
        def option_history_eod(self, **kwargs):
            assert kwargs["symbol"] == "AAPL"
            assert kwargs["start_date"] == date(2024, 11, 4)
            assert kwargs["end_date"] == date(2024, 11, 4)
            return _raw_frame().iloc[[0]]

    monkeypatch.setattr(
        "openbb_thetadata.models.options_chains.resolve_thetadata_client",
        lambda **kwargs: FakeClient(),
    )
    query = ThetaDataOptionsChainsFetcher.transform_query(
        {"symbol": "AAPL", "date": date(2024, 11, 4)}
    )
    rows = asyncio.run(
        ThetaDataOptionsChainsFetcher.aextract_data(query, {"thetadata_api_key": "test-key"})
    )
    assert len(rows) == 1
    assert rows[0]["symbol"] == "AAPL"
