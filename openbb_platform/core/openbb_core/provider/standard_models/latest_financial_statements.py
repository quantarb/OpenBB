"""Statement-publication discovery, distinct from statement observation dates."""
from datetime import date as dateType,datetime
from pydantic import Field
from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams


class LatestFinancialStatementsQueryParams(QueryParams):
    """Fetch one explicit discovery page; the caller owns durable page progress."""
    page:int=Field(default=0,ge=0,le=100)
    limit:int=Field(default=250,gt=0,le=250)


class LatestFinancialStatementsData(Data):
    """Keep source reporting period separate from provider publication metadata."""
    symbol:str
    period:str
    date:dateType=Field(description='Source statement reporting date, unchanged.')
    date_added:datetime=Field(description='Provider dateAdded timestamp; no inferred timezone or filing lag.')
