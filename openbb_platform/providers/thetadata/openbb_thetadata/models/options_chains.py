"""ThetaData Options Chains Model."""

# pylint: disable=unused-argument

from datetime import date as dateType, datetime
from typing import Any, Literal

import pandas as pd
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.options_chains import (
    OptionsChainsData,
    OptionsChainsQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError
from pydantic import Field, model_validator

from openbb_thetadata.utils.helpers import (
    extract_records,
    normalize_thetadata_option_chain,
    resolve_thetadata_client,
)


_UNSUPPORTED_CONTRACT_FILTERS = (
    "dte",
    "min_dte",
    "max_dte",
    "expiration",
    "right",
    "option_type",
    "strike",
    "strike_range",
    "min_strike",
    "max_strike",
    "moneyness",
    "min_moneyness",
    "max_moneyness",
    "max_abs_moneyness",
    "delta",
    "min_delta",
    "max_delta",
    "bid",
    "ask",
    "require_bid_ask",
    "min_bid",
    "min_ask",
    "volume",
    "min_volume",
    "open_interest",
    "min_open_interest",
    "liquidity",
)


class ThetaDataOptionsChainsQueryParams(OptionsChainsQueryParams):
    """ThetaData Options Chains Query Parameters."""

    date: dateType | None = Field(
        default=None,
        description="End-of-day snapshot date. If omitted, today is used.",
    )
    start_date: dateType | None = Field(
        default=None,
        description="Start date for the requested historical range.",
    )
    end_date: dateType | None = Field(
        default=None,
        description="End date for the requested historical range.",
    )
    expiration: str = Field(
        default="*",
        description="Expiration to request. Use '*' for all expirations.",
    )
    strike: str = Field(
        default="*",
        description="Strike to request. Use '*' for all strikes.",
    )
    right: Literal["call", "put", "both"] = Field(
        default="both",
        description="Option side to request.",
    )
    max_dte: int | None = Field(
        default=None,
        description="Maximum days to expiration.",
    )
    strike_range: int | None = Field(
        default=None,
        description="Strike window around the underlying price.",
    )
    include_greeks: bool = Field(
        default=False,
        description="Use ThetaData's EOD Greeks history endpoint, which includes Greeks, IV, and the underlying price.",
    )
    annual_dividend: float | None = Field(
        default=None,
        description="Annual dividend input for ThetaData Greeks calculations.",
    )
    rate_type: str | None = Field(
        default="sofr",
        description="ThetaData interest-rate curve type for Greeks calculations.",
    )
    rate_value: float | None = Field(
        default=None,
        description="Explicit interest-rate value for ThetaData Greeks calculations.",
    )
    version: str | None = Field(
        default="latest",
        description="ThetaData Greeks endpoint version.",
    )
    underlyer_use_nbbo: bool = Field(
        default=False,
        description="Use underlying NBBO in ThetaData Greeks calculations.",
    )
    dataframe_type: Literal["pandas", "polars"] = Field(
        default="pandas",
        description="Return a pandas or polars dataframe from ThetaData.",
    )
    require_bid_ask: bool = Field(
        default=False,
        description="Must remain False; ThetaData option-chain routes return full chains.",
    )
    min_ask: float = Field(
        default=0.0,
        description="Must remain 0.0; ThetaData option-chain routes return full chains.",
    )

    @model_validator(mode="after")
    def _reject_filtered_query(self) -> "ThetaDataOptionsChainsQueryParams":
        _reject_contract_filters(self.model_dump())
        return self


class ThetaDataOptionsChainsData(OptionsChainsData):
    """ThetaData Options Chains Data."""

    __doc__ = OptionsChainsData.__doc__
    __alias_dict__ = {
        "underlying_symbol": "underlying_symbol",
        "eod_date": "eod_date",
        "expiration": "expiration",
        "strike": "strike",
        "option_type": "option_type",
        "contract_symbol": "contract_symbol",
        "last_trade_price": "last_trade_price",
        "last_trade_time": "last_trade_time",
        "volume": "volume",
        "bid": "bid",
        "ask": "ask",
        "bid_size": "bid_size",
        "ask_size": "ask_size",
        "bid_exchange": "bid_exchange",
        "ask_exchange": "ask_exchange",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "close_size": "close_size",
        "prev_close": "prev_close",
        "change": "change",
        "change_percent": "change_percent",
        "mark": "mark",
        "theoretical_price": "theoretical_price",
        "implied_volatility": "implied_volatility",
        "delta": "delta",
        "gamma": "gamma",
        "theta": "theta",
        "vega": "vega",
        "rho": "rho",
    }


class ThetaDataOptionsChainsFetcher(
    Fetcher[ThetaDataOptionsChainsQueryParams, ThetaDataOptionsChainsData]
):
    """ThetaData Options Chains Fetcher."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> ThetaDataOptionsChainsQueryParams:
        """Transform the query parameters."""
        _reject_contract_filters(params)
        transformed = dict(params)
        today = datetime.now().date()
        if transformed.get("date") is None and transformed.get("start_date") is None and transformed.get("end_date") is None:
            transformed["date"] = today
        if transformed.get("date") is not None:
            transformed.setdefault("start_date", transformed["date"])
            transformed.setdefault("end_date", transformed["date"])
        if transformed.get("start_date") is not None and transformed.get("end_date") is None:
            transformed["end_date"] = transformed["start_date"]
        if transformed.get("end_date") is not None and transformed.get("start_date") is None:
            transformed["start_date"] = transformed["end_date"]
        return ThetaDataOptionsChainsQueryParams(**transformed)

    @staticmethod
    async def aextract_data(
        query: ThetaDataOptionsChainsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from ThetaData."""
        from asyncio import to_thread

        _reject_contract_filters(query.model_dump())
        client = resolve_thetadata_client(
            credentials=credentials,
            dataframe_type=query.dataframe_type,
        )

        start_date = query.start_date or query.date or datetime.now().date()
        end_date = query.end_date or query.date or start_date

        def _download() -> pd.DataFrame:
            request_dates = [start_date]
            if query.expiration == "*" and start_date != end_date:
                request_dates = [ts.date() for ts in pd.date_range(start_date, end_date, freq="B")]

            frames: list[pd.DataFrame] = []
            for request_date in request_dates:
                request_start = request_date if query.expiration == "*" else start_date
                request_end = request_date if query.expiration == "*" else end_date
                if query.include_greeks:
                    raw = client.option_history_greeks_eod(
                        symbol=query.symbol,
                        expiration=query.expiration,
                        start_date=request_start,
                        end_date=request_end,
                        strike=query.strike,
                        right=query.right,
                        annual_dividend=query.annual_dividend,
                        rate_type=query.rate_type,
                        rate_value=query.rate_value,
                        version=query.version,
                        underlyer_use_nbbo=query.underlyer_use_nbbo,
                        max_dte=query.max_dte,
                        strike_range=query.strike_range,
                    )
                else:
                    raw = client.option_history_eod(
                        start_date=request_start,
                        end_date=request_end,
                        symbol=query.symbol,
                        expiration=query.expiration,
                        strike=query.strike,
                        right=query.right,
                        max_dte=query.max_dte,
                        strike_range=query.strike_range,
                    )
                frame = extract_records(raw)
                if not frame.empty:
                    frames.append(frame)
            if not frames:
                return pd.DataFrame()
            return pd.concat(frames, ignore_index=True, sort=False)

        frame = await to_thread(_download)
        if frame.empty:
            raise EmptyDataError("No data was returned for the given symbol.")
        return frame.to_dict(orient="records")

    @staticmethod
    def transform_data(
        query: ThetaDataOptionsChainsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> ThetaDataOptionsChainsData:
        """Return the transformed data."""
        if not data:
            raise EmptyDataError("No data was returned for the given symbol.")

        frame = pd.DataFrame.from_records(data)
        frame = normalize_thetadata_option_chain(
            frame,
            snapshot_date=query.date,
            require_bid_ask=query.require_bid_ask,
            min_ask=query.min_ask,
        )
        if frame.empty:
            raise EmptyDataError("No data was returned for the given symbol.")

        return ThetaDataOptionsChainsData.model_validate(frame.to_dict(orient="list"))


def _reject_contract_filters(params: dict[str, Any]) -> None:
    violations: list[str] = []
    for key in _UNSUPPORTED_CONTRACT_FILTERS:
        if key not in params:
            continue
        value = params[key]
        if key in {"expiration", "strike"}:
            if value not in (None, "", "*"):
                violations.append(key)
        elif key == "right":
            if value not in (None, "", "both"):
                violations.append(key)
        elif key == "require_bid_ask":
            if bool(value):
                violations.append(key)
        elif key == "min_ask":
            if value not in (None, "", 0, 0.0):
                violations.append(key)
        elif value is not None:
            violations.append(key)

    if violations:
        detail = ", ".join(sorted(violations))
        raise ValueError(
            "ThetaData option-chain requests are full-chain-only. "
            f"Remove contract query filter(s): {detail}. "
            "Filter contracts only after loading the complete chain."
        )
