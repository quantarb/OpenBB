"""Historical Sector Performance Standard Model."""

from datetime import date as dateType

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class HistoricalSectorPerformanceQueryParams(QueryParams):
    """Historical Sector Performance Query."""

    sector: str = Field(description="The name of the sector.")
    exchange: str = Field(description="The exchange where the data is from.")
    start_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("start_date", "")
    )
    end_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("end_date", "")
    )

    @field_validator("sector", mode="before", check_fields=False)
    @classmethod
    def strip_sector(cls, v: str) -> str:
        return str(v).strip()

    @field_validator("exchange", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str) -> str:
        return str(v).upper()


class HistoricalSectorPerformanceData(Data):
    """Historical Sector Performance Data."""

    date: dateType = Field(description=DATA_DESCRIPTIONS.get("date", ""))
    exchange: str | None = Field(
        default=None, description="The exchange where the data is from."
    )
    sector: str = Field(description="The name of the sector.")
    change_percent: float = Field(description="The change in percent from open.")

