"""FMP Historical Ratings Model."""

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.historical_ratings import (
    HistoricalRatingsData,
    HistoricalRatingsQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError


class FMPHistoricalRatingsQueryParams(HistoricalRatingsQueryParams):
    """FMP historical company-ratings query."""

    __json_schema_extra__ = {"symbol": {"multiple_items_allowed": True}}


class FMPHistoricalRatingsData(HistoricalRatingsData):
    """A dated FMP company rating and its component scores."""

    __alias_dict__ = {
        "overall_score": "overallScore",
        "discounted_cash_flow_score": "discountedCashFlowScore",
        "return_on_equity_score": "returnOnEquityScore",
        "return_on_assets_score": "returnOnAssetsScore",
        "debt_to_equity_score": "debtToEquityScore",
        "price_to_earnings_score": "priceToEarningsScore",
        "price_to_book_score": "priceToBookScore",
    }


class FMPHistoricalRatingsFetcher(
    Fetcher[FMPHistoricalRatingsQueryParams, list[FMPHistoricalRatingsData]]
):
    """Fetch FMP's dated company ratings."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> FMPHistoricalRatingsQueryParams:
        return FMPHistoricalRatingsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FMPHistoricalRatingsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        import asyncio
        import warnings
        from openbb_core.provider.utils.helpers import amake_request
        from openbb_fmp.utils.helpers import response_callback

        api_key = credentials.get("fmp_api_key") if credentials else ""
        symbols = query.symbol.split(",")
        results: list[dict] = []

        async def get_one(symbol: str) -> None:
            limit = query.limit if query.limit is not None else 1000
            url = (
                "https://financialmodelingprep.com/stable/ratings-historical?"
                f"symbol={symbol}&limit={limit}&apikey={api_key}"
            )
            result = await amake_request(url, response_callback=response_callback, **kwargs)
            if not result:
                warnings.warn(f"No historical ratings found for {symbol}")
            else:
                results.extend(result)

        await asyncio.gather(*(get_one(symbol) for symbol in symbols))
        if not results:
            raise EmptyDataError("No historical ratings found for the given symbols.")
        return sorted(results, key=lambda row: (row.get("date", ""), row.get("symbol", "")))

    @staticmethod
    def transform_data(
        query: FMPHistoricalRatingsQueryParams, data: list[dict], **kwargs: Any
    ) -> list[FMPHistoricalRatingsData]:
        return [FMPHistoricalRatingsData.model_validate(row) for row in data]
