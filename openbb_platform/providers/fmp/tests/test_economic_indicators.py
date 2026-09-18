import asyncio
from datetime import date
from urllib.parse import parse_qs, urlparse
from openbb_fmp import fmp_provider
from openbb_fmp.models.economic_indicators import FMPEconomicIndicatorsFetcher


def test_economic_history_preserves_dates_values_and_registers_fmp(monkeypatch):
    query = FMPEconomicIndicatorsFetcher.transform_query({'symbol': 'GDP'})
    assert query.start_date == date(1900, 1, 1)
    async def fake_get_data(url, **kwargs):
        params = parse_qs(urlparse(url).query)
        assert params['name'] == ['GDP']
        assert params['from'] == ['1900-01-01']
        return [{'date': '1947-04-01', 'value': 250.}, {'date': '1947-01-01', 'value': None}]
    monkeypatch.setattr('openbb_fmp.models.economic_indicators.get_data', fake_get_data)
    raw = asyncio.run(FMPEconomicIndicatorsFetcher.aextract_data(query, {'fmp_api_key': 'test'}))
    rows = FMPEconomicIndicatorsFetcher.transform_data(query, raw)
    assert rows[0].date == date(1947, 1, 1)
    assert rows[0].value is None
    assert rows[1].value == 250.
    assert fmp_provider.fetcher_dict['EconomicIndicators'] is FMPEconomicIndicatorsFetcher
