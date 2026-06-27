"""FMP Equity Ownership Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.price_target import (
    PriceTargetData,
    PriceTargetQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError
from pydantic import ConfigDict, Field


class FMPPriceTargetQueryParams(PriceTargetQueryParams):
    """FMP Price Target Query.

    Source: https://site.financialmodelingprep.com/developer/docs#analyst
    """

    __json_schema_extra__ = {"symbol": {"multiple_items_allowed": True}}


class FMPPriceTargetData(PriceTargetData):
    """FMP Price Target Data."""

    model_config = ConfigDict(extra="ignore")

    __alias_dict__ = {
        "analyst_firm": "analystCompany",
        "rating_current": "newGrade",
        "rating_previous": "previousGrade",
        "news_title": "newsTitle",
        "news_url": "newsURL",
    }

    news_title: str | None = Field(
        default=None, description="News title of the price target."
    )
    news_url: str | None = Field(
        default=None, description="News URL of the price target."
    )


class FMPPriceTargetFetcher(
    Fetcher[
        FMPPriceTargetQueryParams,
        list[FMPPriceTargetData],
    ]
):
    """FMP Price Target Fetcher."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> FMPPriceTargetQueryParams:
        """Transform the query params."""
        return FMPPriceTargetQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FMPPriceTargetQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from warnings import warn
        from openbb_core.provider.utils.helpers import amake_request
        from openbb_fmp.utils.helpers import response_callback

        api_key = credentials.get("fmp_api_key") if credentials else ""
        base_url = "https://financialmodelingprep.com/stable/price-target-news?"
        symbols = query.symbol.split(",")  # type: ignore
        requested_limit = query.limit
        page_limit = min(requested_limit, 100) if requested_limit else 100
        results: list[dict] = []

        async def get_one(symbol):
            """Get data for one symbol."""
            page = 0
            symbol_results: list[dict] = []

            while True:
                url = (
                    f"{base_url}symbol={symbol}&page={page}"
                    f"&limit={page_limit}&apikey={api_key}"
                )
                page_results = await amake_request(
                    url, response_callback=response_callback, **kwargs
                )

                if not page_results:
                    break

                symbol_results.extend(page_results)

                if len(page_results) < page_limit:
                    break
                if requested_limit and len(symbol_results) >= requested_limit:
                    break
                page += 1

            if not symbol_results:
                warn(f"Symbol Error: No data found for {symbol}")

            if symbol_results:
                results.extend(
                    symbol_results[:requested_limit]
                    if requested_limit
                    else symbol_results
                )

        await asyncio.gather(*[get_one(symbol) for symbol in symbols])

        if not results:
            raise EmptyDataError("No data returned for the given symbols.")

        return sorted(
            results, key=lambda x: (x["publishedDate"], x["symbol"]), reverse=True
        )

    @staticmethod
    def transform_data(
        query: FMPPriceTargetQueryParams, data: list[dict], **kwargs: Any
    ) -> list[FMPPriceTargetData]:
        """Return the transformed data."""
        return [FMPPriceTargetData.model_validate(item) for item in data]
