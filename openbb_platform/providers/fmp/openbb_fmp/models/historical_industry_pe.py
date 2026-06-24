"""FMP Historical Industry P/E Model."""

# pylint: disable=unused-argument

from datetime import datetime
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.historical_industry_pe import (
    HistoricalIndustryPEData,
    HistoricalIndustryPEQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError


class FMPHistoricalIndustryPEQueryParams(HistoricalIndustryPEQueryParams):
    """FMP Historical Industry P/E Query."""


class FMPHistoricalIndustryPEData(HistoricalIndustryPEData):
    """FMP Historical Industry P/E Data."""


class FMPHistoricalIndustryPEFetcher(
    Fetcher[
        FMPHistoricalIndustryPEQueryParams,
        list[FMPHistoricalIndustryPEData],
    ]
):
    """FMP Historical Industry P/E Fetcher."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> FMPHistoricalIndustryPEQueryParams:
        """Transform the query params."""
        return FMPHistoricalIndustryPEQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FMPHistoricalIndustryPEQueryParams,
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

        url = "https://financialmodelingprep.com/stable/historical-industry-pe?" + "&".join(params)
        return await get_data_urls([url], **kwargs)  # type: ignore

    @staticmethod
    def transform_data(
        query: FMPHistoricalIndustryPEQueryParams,
        data: list,
        **kwargs: Any,
    ) -> list[FMPHistoricalIndustryPEData]:
        """Return the transformed data."""
        if not data:
            raise EmptyDataError("No data was returned for the given industry.")
        return [
            FMPHistoricalIndustryPEData.model_validate(item)
            for item in sorted(data, key=lambda x: x.get("date") or datetime.min.date())
        ]

