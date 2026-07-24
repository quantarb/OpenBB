"""Historical company ratings standard model."""

from datetime import date as dateType

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import DATA_DESCRIPTIONS, QUERY_DESCRIPTIONS
from pydantic import Field, field_validator


class HistoricalRatingsQueryParams(QueryParams):
    """Historical company ratings query."""

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))
    limit: int | None = Field(default=None, description="Maximum number of records.")

    @field_validator("symbol", mode="before")
    @classmethod
    def to_upper(cls, value: str) -> str:
        return value.upper()


class HistoricalRatingsData(Data):
    """Dated company rating and component scores."""

    date: dateType = Field(description=DATA_DESCRIPTIONS.get("date", ""))
    symbol: str | None = Field(default=None, description=DATA_DESCRIPTIONS.get("symbol", ""))
    rating: str | None = None
    overall_score: float | None = None
    discounted_cash_flow_score: float | None = None
    return_on_equity_score: float | None = None
    return_on_assets_score: float | None = None
    debt_to_equity_score: float | None = None
    price_to_earnings_score: float | None = None
    price_to_book_score: float | None = None
