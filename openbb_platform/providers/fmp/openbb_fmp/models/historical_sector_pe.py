"""FMP Historical Sector P/E Model."""

# pylint: disable=unused-argument

from datetime import datetime
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.historical_sector_pe import (
    HistoricalSectorPEData,
    HistoricalSectorPEQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError


class FMPHistoricalSectorPEQueryParams(HistoricalSectorPEQueryParams):
    """FMP Historical Sector P/E Query."""


class FMPHistoricalSectorPEData(HistoricalSectorPEData):
    """FMP Historical Sector P/E Data."""


class FMPHistoricalSectorPEFetcher(
    Fetcher[
        FMPHistoricalSectorPEQueryParams,
        list[FMPHistoricalSectorPEData],
    ]
):
    """FMP Historical Sector P/E Fetcher."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> FMPHistoricalSectorPEQueryParams:
        """Transform the query params."""
        return FMPHistoricalSectorPEQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FMPHistoricalSectorPEQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_fmp.utils.helpers import get_data_urls

        api_key = credentials.get("fmp_api_key") if credentials else ""
        params = [
            f"sector={query.sector}",
            f"exchange={query.exchange}",
            f"apikey={api_key}",
        ]
        if query.start_date is not None:
            params.append(f"from={query.start_date.isoformat()}")
        if query.end_date is not None:
            params.append(f"to={query.end_date.isoformat()}")

        url = "https://financialmodelingprep.com/stable/historical-sector-pe?" + "&".join(params)
        return await get_data_urls([url], **kwargs)  # type: ignore

    @staticmethod
    def transform_data(
        query: FMPHistoricalSectorPEQueryParams,
        data: list,
        **kwargs: Any,
    ) -> list[FMPHistoricalSectorPEData]:
        """Return the transformed data."""
        if not data:
            raise EmptyDataError("No data was returned for the given sector.")
        return [
            FMPHistoricalSectorPEData.model_validate(item)
            for item in sorted(data, key=lambda x: x.get("date") or datetime.min.date())
        ]

