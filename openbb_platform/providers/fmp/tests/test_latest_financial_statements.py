import asyncio
import pytest
from pydantic import ValidationError
from openbb_fmp.models.latest_financial_statements import FMPLatestFinancialStatementsFetcher as Fetcher


def test_explicit_page_zero_validates_and_publication_date_stays_distinct():
    query=Fetcher.transform_query({'page':0,'limit':250})
    rows=Fetcher.transform_data(query,[{'symbol':'MSFT','period':'Q2','date':'2026-06-30','dateAdded':'2026-07-30 13:17:26'}])
    assert rows[0].date.isoformat()=='2026-06-30'
    assert rows[0].date_added.isoformat()=='2026-07-30T13:17:26'
    assert rows[0].date_added.tzinfo is None
    with pytest.raises(ValidationError):Fetcher.transform_query({'page':101})
    with pytest.raises(ValidationError):Fetcher.transform_query({'limit':251})


def test_exactly_one_sdk_request_and_empty_page_is_explicit(monkeypatch):
    urls=[]
    async def fake(url,**kwargs):urls.append(url);return []
    monkeypatch.setattr('openbb_fmp.utils.helpers.get_data',fake)
    query=Fetcher.transform_query({'page':4,'limit':250})
    data=asyncio.run(Fetcher.aextract_data(query,{'fmp_api_key':'fixture'}))
    assert len(urls)==1 and 'page=4&limit=250' in urls[0]
    assert Fetcher.transform_data(query,data)==[]


def test_filings_explicit_first_page_is_valid():
    from openbb_fmp.models.company_filings import FMPCompanyFilingsQueryParams
    assert FMPCompanyFilingsQueryParams(symbol='MSFT',page=0).page==0
    with pytest.raises(ValidationError):FMPCompanyFilingsQueryParams(symbol='MSFT',page=-1)
