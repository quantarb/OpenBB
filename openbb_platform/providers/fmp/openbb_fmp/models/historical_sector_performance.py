"""FMP Historical Sector Performance Model."""

# pylint: disable=unused-argument

from datetime import datetime
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.historical_sector_performance import (
    HistoricalSectorPerformanceData,
    HistoricalSectorPerformanceQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError


class FMPHistoricalSectorPerformanceQueryParams(HistoricalSectorPerformanceQueryParams):
    """FMP Historical Sector Performance Query."""


class FMPHistoricalSectorPerformanceData(HistoricalSectorPerformanceData):
    """FMP Historical Sector Performance Data."""

    __alias_dict__ = {
        "change_percent": "averageChange",
    }


class FMPHistoricalSectorPerformanceFetcher(
    Fetcher[
        FMPHistoricalSectorPerformanceQueryParams,
        list[FMPHistoricalSectorPerformanceData],
    ]
):
    """FMP Historical Sector Performance Fetcher."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> FMPHistoricalSectorPerformanceQueryParams:
        """Transform the query params."""
        return FMPHistoricalSectorPerformanceQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FMPHistoricalSectorPerformanceQueryParams,
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

        url = (
            "https://financialmodelingprep.com/stable/historical-sector-performance?"
            + "&".join(params)
        )
        return await get_data_urls([url], **kwargs)  # type: ignore

    @staticmethod
    def transform_data(
        query: FMPHistoricalSectorPerformanceQueryParams,
        data: list,
        **kwargs: Any,
    ) -> list[FMPHistoricalSectorPerformanceData]:
        """Return the transformed data."""
        if not data:
            raise EmptyDataError("No data was returned for the given sector.")
        normalized = []
        for item in sorted(data, key=lambda x: x.get("date") or datetime.min.date()):
            value = dict(item)
            if value.get("averageChange") is not None:
                value["averageChange"] = float(value["averageChange"]) / 100.0
            normalized.append(FMPHistoricalSectorPerformanceData.model_validate(value))
        return normalized
