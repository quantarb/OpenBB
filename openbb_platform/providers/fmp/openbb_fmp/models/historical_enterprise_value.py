"""FMP Historical Enterprise Value Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.historical_enterprise_value import (
    HistoricalEnterpriseValueData,
    HistoricalEnterpriseValueQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError
from pydantic import ConfigDict, Field


class FMPHistoricalEnterpriseValueQueryParams(HistoricalEnterpriseValueQueryParams):
    """FMP Historical Enterprise Value Query.

    Source: https://site.financialmodelingprep.com/developer/docs/stable/enterprise-values
    """

    __json_schema_extra__ = {"symbol": {"multiple_items_allowed": True}}

    limit: int | None = Field(
        default=None,
        description="Number of records to return. Default is all available records.",
    )


class FMPHistoricalEnterpriseValueData(HistoricalEnterpriseValueData):
    """FMP Historical Enterprise Value Data."""

    model_config = ConfigDict(extra="ignore")

    __alias_dict__ = {
        "stock_price": "stockPrice",
        "number_of_shares": "numberOfShares",
        "market_capitalization": "marketCapitalization",
        "cash_and_cash_equivalents": "minusCashAndCashEquivalents",
        "total_debt": "addTotalDebt",
        "enterprise_value": "enterpriseValue",
    }


class FMPHistoricalEnterpriseValueFetcher(
    Fetcher[
        FMPHistoricalEnterpriseValueQueryParams,
        list[FMPHistoricalEnterpriseValueData],
    ]
):
    """FMP Historical Enterprise Value Fetcher."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> FMPHistoricalEnterpriseValueQueryParams:
        """Transform the query params."""
        return FMPHistoricalEnterpriseValueQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FMPHistoricalEnterpriseValueQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        import warnings  # noqa
        from openbb_fmp.utils.helpers import get_data_many

        api_key = credentials.get("fmp_api_key") if credentials else ""
        symbols = query.symbol.split(",")
        results: list[dict] = []
        limit = query.limit if query.limit is not None else 10000

        for symbol in symbols:
            url = (
                "https://financialmodelingprep.com/stable/enterprise-values"
                f"?symbol={symbol}&limit={limit}&apikey={api_key}"
            )
            data = await get_data_many(url, **kwargs)

            if not data:
                warnings.warn(f"No data found for symbol {symbol}")
                continue

            results.extend(data)

        return results

    @staticmethod
    def transform_data(
        query: FMPHistoricalEnterpriseValueQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[FMPHistoricalEnterpriseValueData]:
        """Return the transformed data."""
        if not data:
            raise EmptyDataError("No data was returned for the given symbols.")

        result: list[FMPHistoricalEnterpriseValueData] = []

        for item in data:
            dt = item.get("date")

            if not dt:
                continue

            if query.start_date and dt < query.start_date.isoformat():
                continue

            if query.end_date and dt > query.end_date.isoformat():
                continue

            result.append(FMPHistoricalEnterpriseValueData.model_validate(item))

        return sorted(result, key=lambda x: (x.symbol, x.date), reverse=True)
