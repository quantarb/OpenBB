"""FMP ETF Holdings Model."""

# pylint: disable=unused-argument

from datetime import (
    date as dateType,
    datetime,
)
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.nport_disclosure import (
    NportDisclosureData,
    NportDisclosureQueryParams,
)
from pydantic import Field, field_validator


class FMPNportDisclosureQueryParams(NportDisclosureQueryParams):
    """FMP ETF Holdings Query.

    Source: https://site.financialmodelingprep.com/developer/docs#holdings
    """


class FMPNportDisclosureData(NportDisclosureData):
    """FMP ETF Holdings Data."""

    __alias_dict__ = {
        "weight": "pctVal",
        "value": "valUsd",
        "asset_category": "assetCat",
        "issuer_category": "issuerCat",
        "country": "invCountry",
        "currency": "cur_cd",
        "as_of": "date",
        "accepted_date": "acceptedDate",
        "is_restricted": "isRestrictedSec",
        "fair_value_level": "fairValLevel",
    }

    as_of: dateType | None = Field(
        description="The acceptance datetime of the filing.",
        default=None,
    )

    accepted_date: datetime | None = Field(default=None, description="Original filing acceptance timestamp, unshifted.")

    @field_validator("weight", mode="before", check_fields=False)
    @classmethod
    def normalize_percent(cls, v):
        """Normalize percent values."""
        return float(v) / 100 if v else None

    @field_validator(
        "cusip",
        "isin",
        "balance",
        "name",
        "symbol",
        "value",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def replace_empty(cls, v):
        """Replace empty strings and 0s with None."""
        if isinstance(v, str):
            return v if v not in ("", "0", "-", "N/A") else None
        if isinstance(v, (float, int)):
            return v if v and v not in (0.0, 0) else None
        return v if v else None


class FMPNportDisclosureFetcher(
    Fetcher[
        FMPNportDisclosureQueryParams,
        list[FMPNportDisclosureData],
    ]
):
    """FMP NPORT Disclosure Fetcher."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> FMPNportDisclosureQueryParams:
        """Transform the query."""
        return FMPNportDisclosureQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FMPNportDisclosureQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError
        from openbb_fmp.utils.helpers import get_data_many

        api_key = credentials.get("fmp_api_key") if credentials else ""
        url = "https://financialmodelingprep.com/stable/funds/disclosure?"

        if query.symbol.isnumeric():
            url += f"cik={query.symbol}"
        else:
            url += f"symbol={query.symbol}"

        if query.year is None or query.quarter is None:
            # Calendar quarter-1 is not necessarily reported yet. Use vendor availability.
            from openbb_core.provider.utils.errors import EmptyDataError

            dates_url = (
                "https://financialmodelingprep.com/stable/funds/disclosure-dates?"
                + (f"cik={query.symbol}" if query.symbol.isnumeric() else f"symbol={query.symbol}")
                + f"&apikey={api_key}"
            )
            available = await get_data_many(dates_url, **kwargs)
            candidates = []
            for item in available:
                if not isinstance(item, dict):
                    raise OpenBBError("Invalid FMP disclosure-period availability response")
                reported = item.get("date")
                year, quarter = item.get("year"), item.get("quarter")
                if (year is None or quarter is None) and reported:
                    source_date = dateType.fromisoformat(str(reported)[:10])
                    year, quarter = source_date.year, (source_date.month - 1) // 3 + 1
                if year is None or quarter is None:
                    raise OpenBBError("FMP availability record lacks a reporting year/quarter")
                year, quarter = int(year), int(quarter)
                if not 1 <= quarter <= 4:
                    raise OpenBBError("Invalid FMP reporting quarter")
                if query.year is not None and year != query.year:
                    continue
                if query.quarter is not None and quarter != query.quarter:
                    continue
                candidates.append((year, quarter))
            if not candidates:
                raise EmptyDataError("No vendor-reported N-PORT periods for this fund and requested scope")
            query.year, query.quarter = max(candidates)

        url += f"&year={query.year}&quarter={query.quarter}&apikey={api_key}"

        return await get_data_many(url, **kwargs)  # type: ignore

    @staticmethod
    def transform_data(
        query: FMPNportDisclosureQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[FMPNportDisclosureData]:
        """Return the transformed data."""
        results: list[FMPNportDisclosureData] = []
        for d in data:
            new_d = dict(d)
            results.append(FMPNportDisclosureData.model_validate(new_d))

        return sorted(results, key=lambda x: x.weight or 0, reverse=True)
