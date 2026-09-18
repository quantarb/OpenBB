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

@pytest.mark.parametrize('model,field,value', [
    ('income_statement', 'revenue', 123.456),
    ('balance_sheet', 'accumulated_other_comprehensive_income', -19999.99999999602),
    ('cash_flow', 'net_cash_from_operating_activities', -21800000.00000001),
])
def test_statement_amounts_preserve_fractional_provider_values(model, field, value):
    from importlib import import_module
    classes = {'income_statement': 'FMPIncomeStatementData', 'balance_sheet': 'FMPBalanceSheetData', 'cash_flow': 'FMPCashFlowStatementData'}
    data_model = getattr(import_module(f'openbb_fmp.models.{model}'), classes[model])
    record = data_model.model_validate({'date': '2024-03-31', 'symbol': 'TEST', field: value})
    assert getattr(record, field) == value
