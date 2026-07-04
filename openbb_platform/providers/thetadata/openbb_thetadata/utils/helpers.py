"""ThetaData helper utilities."""

from __future__ import annotations

from datetime import date as dateType
from typing import Any

import pandas as pd

from openbb_core.app.model.abstract.error import OpenBBError
from openbb_core.provider.utils.errors import EmptyDataError


def resolve_thetadata_api_key(credentials: dict[str, str] | None) -> str:
    """Resolve the ThetaData API key from OpenBB credentials or the environment."""
    import os

    api_key = ""
    if credentials:
        api_key = (
            credentials.get("thetadata_api_key")
            or credentials.get("api_key")
            or credentials.get("THETADATA_API_KEY")
            or ""
        )
    api_key = str(api_key or os.getenv("THETADATA_API_KEY") or "").strip()
    if not api_key:
        raise OpenBBError("ThetaData API key is required.")
    return api_key


def resolve_thetadata_client(
    *,
    credentials: dict[str, str] | None,
    dataframe_type: str = "pandas",
) -> Any:
    """Return an authorized ThetaData SDK client."""
    from thetadata import ThetaClient

    return ThetaClient(api_key=resolve_thetadata_api_key(credentials), dataframe_type=dataframe_type)


def _normalize_snapshot_date(value: Any) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return pd.Timestamp(ts).normalize()


def normalize_thetadata_option_chain(
    df: pd.DataFrame,
    *,
    snapshot_date: dateType | str | pd.Timestamp | None = None,
    require_bid_ask: bool = True,
    min_ask: float = 0.01,
) -> pd.DataFrame:
    """Normalize ThetaData option history into OpenBB-compatible rows."""
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    out.columns = [str(col).strip().lower() for col in out.columns]
    out = out.rename(
        columns={
            "symbol": "underlying_symbol",
            "right": "option_type",
            "created": "snapshot_date",
            "timestamp": "snapshot_date",
            "last_trade": "last_trade_time",
            "close": "last_trade_price",
            "open": "open",
            "high": "high",
            "low": "low",
            "implied_vol": "implied_volatility",
        }
    )

    if "snapshot_date" not in out.columns:
        out["snapshot_date"] = snapshot_date
    if snapshot_date is not None:
        out["snapshot_date"] = snapshot_date
    out["snapshot_date"] = pd.to_datetime(out["snapshot_date"], errors="coerce").dt.normalize()
    if out["snapshot_date"].isna().all():
        out["snapshot_date"] = pd.Timestamp.today().normalize()

    out["underlying_symbol"] = out["underlying_symbol"].astype(str).str.upper()
    out["option_type"] = (
        out["option_type"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"call": "call", "put": "put", "c": "call", "p": "put"})
    )
    out["expiration"] = pd.to_datetime(out["expiration"], errors="coerce").dt.normalize()
    out["strike"] = pd.to_numeric(out["strike"], errors="coerce")
    for col in (
        "bid",
        "ask",
        "open",
        "high",
        "low",
        "last_trade_price",
        "volume",
        "count",
        "underlying_price",
        "implied_volatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "rho",
    ):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    if "last_trade_time" in out.columns:
        out["last_trade_time"] = pd.to_datetime(out["last_trade_time"], errors="coerce")

    valid = out["expiration"].notna() & out["strike"].notna() & out["option_type"].isin({"call", "put"})
    out = out.loc[valid].copy()
    if out.empty:
        return out

    if require_bid_ask:
        if "bid" not in out.columns:
            out["bid"] = pd.NA
        if "ask" not in out.columns:
            out["ask"] = pd.NA
        out = out.loc[out["bid"].notna() & out["ask"].notna() & (out["ask"] >= float(min_ask))].copy()
    elif "ask" in out.columns:
        out = out.loc[(out["ask"].isna()) | (out["ask"] >= float(min_ask))].copy()

    if out.empty:
        return out

    if "bid" in out.columns and "ask" in out.columns:
        out["mark"] = (pd.to_numeric(out["bid"], errors="coerce") + pd.to_numeric(out["ask"], errors="coerce")) / 2.0
    else:
        out["mark"] = pd.NA

    if "last_trade_price" not in out.columns:
        out["last_trade_price"] = out["mark"]
    if "open" in out.columns and "close" not in out.columns:
        out["close"] = out["last_trade_price"]

    if "count" in out.columns and "close_size" not in out.columns:
        out["close_size"] = out["count"]

    if "snapshot_date" in out.columns:
        out["eod_date"] = out["snapshot_date"]
    else:
        out["eod_date"] = pd.Timestamp.today().normalize()

    expiration_dates = pd.to_datetime(out["expiration"], errors="coerce").dt.date
    eod_dates = pd.to_datetime(out["eod_date"], errors="coerce").dt.date
    out["expiration"] = expiration_dates
    out["eod_date"] = eod_dates
    out["dte"] = [
        (exp - eod).days if not pd.isna(exp) and not pd.isna(eod) else pd.NA
        for exp, eod in zip(expiration_dates, eod_dates, strict=False)
    ]
    out["dte"] = pd.to_numeric(out["dte"], errors="coerce")

    out["contract_size"] = 100
    out["contract_symbol"] = out.apply(_build_contract_symbol, axis=1)
    if "underlying_price" not in out.columns:
        out["underlying_price"] = pd.NA

    column_order = [
        "underlying_symbol",
        "underlying_price",
        "contract_symbol",
        "eod_date",
        "expiration",
        "dte",
        "strike",
        "option_type",
        "contract_size",
        "open_interest",
        "volume",
        "theoretical_price",
        "last_trade_price",
        "last_trade_size",
        "last_trade_time",
        "tick",
        "bid",
        "bid_size",
        "bid_time",
        "bid_exchange",
        "ask",
        "ask_size",
        "ask_time",
        "ask_exchange",
        "mark",
        "open",
        "open_bid",
        "open_ask",
        "high",
        "bid_high",
        "ask_high",
        "low",
        "bid_low",
        "ask_low",
        "close",
        "close_size",
        "close_time",
        "close_bid",
        "close_bid_size",
        "close_bid_time",
        "close_ask",
        "close_ask_size",
        "close_ask_time",
        "prev_close",
        "change",
        "change_percent",
        "implied_volatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "rho",
        "snapshot_date",
    ]
    for col in column_order:
        if col not in out.columns:
            out[col] = pd.NA

    out["theoretical_price"] = out["mark"]
    if "close" in out.columns:
        out["change"] = pd.to_numeric(out["last_trade_price"], errors="coerce") - pd.to_numeric(out["open"], errors="coerce")
        out["change_percent"] = pd.to_numeric(out["change"], errors="coerce") / pd.to_numeric(out["open"], errors="coerce")

    out["change_percent"] = pd.to_numeric(out["change_percent"], errors="coerce")
    out["change"] = pd.to_numeric(out["change"], errors="coerce")
    out["bid"] = pd.to_numeric(out["bid"], errors="coerce")
    out["ask"] = pd.to_numeric(out["ask"], errors="coerce")
    if "bid_exchange" in out.columns:
        out["bid_exchange"] = out["bid_exchange"].astype("string")
    if "ask_exchange" in out.columns:
        out["ask_exchange"] = out["ask_exchange"].astype("string")
    out["mark"] = pd.to_numeric(out["mark"], errors="coerce")
    out["theoretical_price"] = pd.to_numeric(out["theoretical_price"], errors="coerce")
    out["volume"] = pd.to_numeric(out["volume"], errors="coerce")
    out["contract_size"] = pd.to_numeric(out["contract_size"], errors="coerce").astype("Int64")

    out = out.replace({pd.NaT: None})
    return out.loc[:, column_order]


def _build_contract_symbol(row: pd.Series) -> str:
    underlying = str(row.get("underlying_symbol") or "").strip().upper()
    expiration = pd.to_datetime(row.get("expiration"), errors="coerce")
    option_type = str(row.get("option_type") or "").strip().lower()
    strike = pd.to_numeric(pd.Series([row.get("strike")]), errors="coerce").iloc[0]
    if pd.isna(expiration) or not underlying or option_type not in {"call", "put"} or pd.isna(strike):
        return ""
    strike_code = f"{int(round(float(strike) * 1000)):08d}"
    option_code = "C" if option_type == "call" else "P"
    return f"{underlying}{expiration.strftime('%y%m%d')}{option_code}{strike_code}"


def extract_records(data: pd.DataFrame | list[dict] | dict[str, Any] | None) -> pd.DataFrame:
    """Return a DataFrame from raw ThetaData output."""
    if data is None:
        return pd.DataFrame()
    if isinstance(data, pd.DataFrame):
        return data.copy()
    if isinstance(data, dict):
        return pd.DataFrame(data)
    if isinstance(data, list):
        return pd.DataFrame.from_records(data)
    raise EmptyDataError("No data was returned from ThetaData.")
