"""FMP full as-reported financial statements; preserve source XBRL fields and zeros."""

import json
from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.reported_financials import (
    ReportedFinancialsData,
    ReportedFinancialsQueryParams,
)
from pydantic import Field, model_validator


class FMPReportedFinancialsQueryParams(ReportedFinancialsQueryParams):
    """Full raw filings from the documented stable FMP endpoint.

    Source: https://site.financialmodelingprep.com/developer/docs/stable/as-reported-financial-statements
    """

    period: Literal["annual", "quarter"] = Field(default="annual")
    statement_type: Literal["full"] = Field(default="full", description="Complete raw filing across statement families.")
    limit: int = Field(default=1000, ge=1, le=1000)


class FMPReportedFinancialsData(ReportedFinancialsData):
    """Source metadata plus original raw fields; zero is a real reported value."""

    __alias_dict__ = {"period_ending": "date", "fiscal_period": "period", "fiscal_year": "calendarYear"}
    raw_metadata: str = Field(description="Unmodified provider record for provenance.")

    @model_validator(mode="before")
    @classmethod
    def replace_zero(cls, values):
        """Preserve reported zero amounts rather than converting them to missing values."""
        return values


class FMPReportedFinancialsFetcher(Fetcher[FMPReportedFinancialsQueryParams, list[FMPReportedFinancialsData]]):
    """Fetch the vendor's complete raw filing through the standard OpenBB adapter."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> FMPReportedFinancialsQueryParams:
        """Validate explicit annual/quarter/full scope."""
        return FMPReportedFinancialsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FMPReportedFinancialsQueryParams, credentials: dict[str, str] | None, **kwargs: Any
    ) -> list[dict]:
        """Request bounded rows; provider helpers retain normal request admission and errors."""
        from openbb_fmp.utils.helpers import get_data_many  # pylint: disable=import-outside-toplevel

        key = credentials.get("fmp_api_key", "") if credentials else ""
        url = (
            "https://financialmodelingprep.com/stable/financial-statement-full-as-reported"
            f"?symbol={query.symbol}&period={query.period}&limit={query.limit}&apikey={key}"
        )
        return await get_data_many(url, **kwargs)

    @staticmethod
    def transform_data(
        query: FMPReportedFinancialsQueryParams, data: list[dict], **kwargs: Any
    ) -> list[FMPReportedFinancialsData]:
        """Keep period dates exactly as returned; do not impose disclosure lags."""
        return [
            FMPReportedFinancialsData.model_validate({**row, "raw_metadata": json.dumps(row, sort_keys=True)})
            for row in data
        ]
