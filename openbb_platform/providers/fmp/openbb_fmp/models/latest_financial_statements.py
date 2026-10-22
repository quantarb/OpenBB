"""FMP latest-statement publication discovery; one bounded page per request.

Source: https://site.financialmodelingprep.com/developer/docs/stable/latest-financial-statements
No hidden full-universe crawl and no inferred change-data-capture guarantee.
"""
from typing import Any
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.latest_financial_statements import LatestFinancialStatementsData,LatestFinancialStatementsQueryParams


class FMPLatestFinancialStatementsQueryParams(LatestFinancialStatementsQueryParams):pass


class FMPLatestFinancialStatementsData(LatestFinancialStatementsData):
    __alias_dict__={'date_added':'dateAdded'}


class FMPLatestFinancialStatementsFetcher(Fetcher[FMPLatestFinancialStatementsQueryParams,list[FMPLatestFinancialStatementsData]]):
    @staticmethod
    def transform_query(params:dict[str,Any])->FMPLatestFinancialStatementsQueryParams:
        return FMPLatestFinancialStatementsQueryParams(**params)

    @staticmethod
    async def aextract_data(query:FMPLatestFinancialStatementsQueryParams,credentials:dict[str,str]|None,**kwargs:Any)->list[dict]:
        from openbb_fmp.utils.helpers import get_data
        api_key=credentials.get('fmp_api_key','') if credentials else ''
        payload=await get_data(f'https://financialmodelingprep.com/stable/latest-financial-statements?page={query.page}&limit={query.limit}&apikey={api_key}',**kwargs)
        if not isinstance(payload,list):raise ValueError('Statement discovery returned a non-list response')
        return payload

    @staticmethod
    def transform_data(query:FMPLatestFinancialStatementsQueryParams,data:list[dict],**kwargs:Any)->list[FMPLatestFinancialStatementsData]:
        # Empty page is an explicit observation, not a fabricated statement row.
        return [FMPLatestFinancialStatementsData.model_validate(row) for row in data]
