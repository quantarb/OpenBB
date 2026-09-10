from datetime import date

import pytest
from openbb_fmp.models.income_statement import FMPIncomeStatementQueryParams
from openbb_fmp.models.balance_sheet import FMPBalanceSheetQueryParams
from openbb_fmp.models.cash_flow import FMPCashFlowStatementQueryParams
from openbb_fmp.models.historical_dividends import FMPHistoricalDividendsData


@pytest.mark.parametrize('query', [FMPIncomeStatementQueryParams, FMPBalanceSheetQueryParams, FMPCashFlowStatementQueryParams])
def test_statement_defaults_request_history_and_respect_explicit_limits(query):
    assert query(symbol='AAPL').limit == 1000
    assert query(symbol='AAPL', limit=5).limit == 5


def test_blank_optional_dividend_dates_preserve_the_observation():
    row = FMPHistoricalDividendsData.model_validate({'symbol':'DUK','date':'2024-03-01', 'dividend':1., 'adjDividend':1., 'recordDate':'', 'paymentDate':' ', 'declarationDate':None})
    assert row.ex_dividend_date == date(2024,3,1)
    assert row.record_date is None and row.payment_date is None
