"""FMP complete company-symbol directory through the existing EquitySearch API."""

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_search import EquitySearchData, EquitySearchQueryParams
from pydantic import Field


class FMPEquitySearchQueryParams(EquitySearchQueryParams):
    """Empty query returns the untruncated provider directory, not a screener sample."""

    directory: Literal["company", "financial_statements"] = "company"


class FMPEquitySearchData(EquitySearchData):
    """FMP directory records."""

    instrument_type: str | None = Field(
        default=None, description="Vendor type, if supplied; unknown is not equity certification."
    )
    exchange: str | None = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict, description="Complete provider directory row.")


class FMPEquitySearchFetcher(Fetcher[FMPEquitySearchQueryParams, list[FMPEquitySearchData]]):
    """Fetch the complete provider company directory."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> FMPEquitySearchQueryParams:
        """Transform query."""
        return FMPEquitySearchQueryParams(**params)

    @staticmethod
    async def aextract_data(query, credentials, **kwargs):
        """Aextract data."""
        from openbb_fmp.utils.helpers import get_data

        route = "stock-list" if query.directory == "company" else "financial-statement-symbol-list"
        key = credentials.get("fmp_api_key", "") if credentials else ""
        result = await get_data(f"https://financialmodelingprep.com/stable/{route}?apikey={key}", **kwargs)
        if (
            not isinstance(result, list)
            or not result
            or any(not isinstance(r, dict) or not r.get("symbol") for r in result)
        ):
            raise ValueError("Incomplete or invalid FMP symbol directory")
        return result

    @staticmethod
    def transform_data(query, data, **kwargs):
        """Transform data."""
        rows = []
        for record in data:
            symbol = str(record["symbol"]).strip()
            name = record.get("companyName") or record.get("name")
            if query.query and query.query.casefold() not in (symbol if query.is_symbol else str(name or "")).casefold():
                continue
            rows.append(
                FMPEquitySearchData(
                    symbol=symbol,
                    name=name,
                    instrument_type=record.get("type"),
                    exchange=record.get("exchangeShortName") or record.get("exchange"),
                    raw_metadata=record,
                )
            )
        return rows
