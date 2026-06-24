"""FMP Historical Industry Performance Model."""

# pylint: disable=unused-argument

from datetime import datetime
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.historical_industry_performance import (
    HistoricalIndustryPerformanceData,
    HistoricalIndustryPerformanceQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError


class FMPHistoricalIndustryPerformanceQueryParams(HistoricalIndustryPerformanceQueryParams):
    """FMP Historical Industry Performance Query."""


class FMPHistoricalIndustryPerformanceData(HistoricalIndustryPerformanceData):
    """FMP Historical Industry Performance Data."""

    __alias_dict__ = {
        "change_percent": "averageChange",
    }


class FMPHistoricalIndustryPerformanceFetcher(
    Fetcher[
        FMPHistoricalIndustryPerformanceQueryParams,
        list[FMPHistoricalIndustryPerformanceData],
    ]
):
    """FMP Historical Industry Performance Fetcher."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> FMPHistoricalIndustryPerformanceQueryParams:
        """Transform the query params."""
        return FMPHistoricalIndustryPerformanceQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FMPHistoricalIndustryPerformanceQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_fmp.utils.helpers import get_data_urls

        api_key = credentials.get("fmp_api_key") if credentials else ""
        params = [
            f"industry={query.industry}",
            f"exchange={query.exchange}",
            f"apikey={api_key}",
        ]
        if query.start_date is not None:
            params.append(f"from={query.start_date.isoformat()}")
        if query.end_date is not None:
            params.append(f"to={query.end_date.isoformat()}")

        url = (
            "https://financialmodelingprep.com/stable/historical-industry-performance?"
            + "&".join(params)
        )
        return await get_data_urls([url], **kwargs)  # type: ignore

    @staticmethod
    def transform_data(
        query: FMPHistoricalIndustryPerformanceQueryParams,
        data: list,
        **kwargs: Any,
    ) -> list[FMPHistoricalIndustryPerformanceData]:
        """Return the transformed data."""
        if not data:
            raise EmptyDataError("No data was returned for the given industry.")
        normalized = []
        for item in sorted(data, key=lambda x: x.get("date") or datetime.min.date()):
            value = dict(item)
            if value.get("averageChange") is not None:
                value["averageChange"] = float(value["averageChange"]) / 100.0
            normalized.append(FMPHistoricalIndustryPerformanceData.model_validate(value))
        return normalized

