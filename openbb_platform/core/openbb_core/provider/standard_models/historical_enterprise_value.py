"""Historical Enterprise Value Model."""

from datetime import date as dateType

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class HistoricalEnterpriseValueQueryParams(QueryParams):
    """Historical Enterprise Value Query."""

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))
    start_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("start_date", "")
    )
    end_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("end_date", "")
    )

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str) -> str:
        """Convert field to uppercase."""
        return v.upper()


class HistoricalEnterpriseValueData(Data):
    """Historical Enterprise Value Data."""

    date: dateType = Field(description=DATA_DESCRIPTIONS.get("date", ""))
    symbol: str = Field(description=DATA_DESCRIPTIONS.get("symbol", ""))
    stock_price: float | None = Field(
        default=None,
        description="Stock price used in the enterprise value calculation.",
        json_schema_extra={"x-unit_measurement": "currency"},
    )
    number_of_shares: int | float | None = Field(
        default=None,
        description="Number of shares used in the enterprise value calculation.",
    )
    market_capitalization: int | float | None = Field(
        default=None,
        description="Market capitalization used in the enterprise value calculation.",
        json_schema_extra={"x-unit_measurement": "currency"},
    )
    cash_and_cash_equivalents: int | float | None = Field(
        default=None,
        description="Cash and cash equivalents subtracted from market capitalization.",
        json_schema_extra={"x-unit_measurement": "currency"},
    )
    total_debt: int | float | None = Field(
        default=None,
        description="Total debt added to market capitalization.",
        json_schema_extra={"x-unit_measurement": "currency"},
    )
    enterprise_value: int | float = Field(
        description="Enterprise value.",
        json_schema_extra={"x-unit_measurement": "currency"},
    )
