"""FMP historical economic indicator series."""
from datetime import date
from typing import Any
from urllib.parse import urlencode
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.economic_indicators import EconomicIndicatorsData, EconomicIndicatorsQueryParams
from openbb_core.provider.utils.errors import EmptyDataError
from openbb_fmp.utils.helpers import get_data


class FMPEconomicIndicatorsQueryParams(EconomicIndicatorsQueryParams):
    """Request complete recorded FMP history by default."""
    start_date: date | None = None


class FMPEconomicIndicatorsData(EconomicIndicatorsData):
    """Preserve FMP observation dates and values."""


class FMPEconomicIndicatorsFetcher(Fetcher[FMPEconomicIndicatorsQueryParams, list[FMPEconomicIndicatorsData]]):
    @staticmethod
    def transform_query(params: dict[str, Any]) -> FMPEconomicIndicatorsQueryParams:
        return FMPEconomicIndicatorsQueryParams(**{**params, "start_date": params.get("start_date") or date(1900, 1, 1)})

    @staticmethod
    async def aextract_data(query: FMPEconomicIndicatorsQueryParams, credentials: dict[str, str] | None, **kwargs: Any) -> list[dict]:
        params = {'name': query.symbol, 'apikey': (credentials or {}).get('fmp_api_key', '')}
        if query.start_date:
            params['from'] = query.start_date.isoformat()
        if query.end_date:
            params['to'] = query.end_date.isoformat()
        result = await get_data('https://financialmodelingprep.com/stable/economic-indicators?' + urlencode(params), **kwargs)
        if not result:
            raise EmptyDataError('No economic indicator observations returned.')
        return result

    @staticmethod
    def transform_data(query: FMPEconomicIndicatorsQueryParams, data: list[dict], **kwargs: Any) -> list[FMPEconomicIndicatorsData]:
        return [FMPEconomicIndicatorsData.model_validate({**row, 'symbol': query.symbol}) for row in sorted(data, key=lambda row: row['date'])]
