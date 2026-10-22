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
    statement_type: Literal["balance", "income", "cash", "full"] = Field(
        default="balance", description="Raw statement family; full returns the complete original filing."
    )
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
        route = {
            "balance": "balance-sheet-statement-as-reported",
            "income": "income-statement-as-reported",
            "cash": "cash-flow-statement-as-reported",
            "full": "financial-statement-full-as-reported",
        }[query.statement_type]
        url = (
            f"https://financialmodelingprep.com/stable/{route}"
            f"?symbol={query.symbol}&period={query.period}&limit={query.limit}&apikey={key}"
        )
        return await get_data_many(url, **kwargs)

    @staticmethod
    def transform_data(
        query: FMPReportedFinancialsQueryParams, data: list[dict], **kwargs: Any
    ) -> list[FMPReportedFinancialsData]:
        """Keep period dates exactly as returned; do not impose disclosure lags."""
        results = []
        for row in data:
            flat = {k: v for k, v in row.items() if k != "data"}
            nested = row.get("data")
            if nested is not None:
                if not isinstance(nested, dict):
                    raise ValueError("FMP raw financial data payload must be an object")
                for key, value in nested.items():
                    if key in flat and flat[key] != value:
                        raise ValueError("FMP raw financial field collides with source metadata")
                    flat[key] = value
            flat["raw_metadata"] = json.dumps(row, sort_keys=True)
            results.append(FMPReportedFinancialsData.model_validate(flat))
        return results
