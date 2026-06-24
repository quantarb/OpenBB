"""Historical Industry Performance Standard Model."""

from datetime import date as dateType

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class HistoricalIndustryPerformanceQueryParams(QueryParams):
    """Historical Industry Performance Query."""

    industry: str = Field(description="The name of the industry.")
    exchange: str = Field(description="The exchange where the data is from.")
    start_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("start_date", "")
    )
    end_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("end_date", "")
    )

    @field_validator("industry", mode="before", check_fields=False)
    @classmethod
    def strip_industry(cls, v: str) -> str:
        return str(v).strip()

    @field_validator("exchange", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str) -> str:
        return str(v).upper()


class HistoricalIndustryPerformanceData(Data):
    """Historical Industry Performance Data."""

    date: dateType = Field(description=DATA_DESCRIPTIONS.get("date", ""))
    exchange: str | None = Field(
        default=None, description="The exchange where the data is from."
    )
    industry: str = Field(description="The name of the industry.")
    change_percent: float = Field(description="The change in percent from open.")

