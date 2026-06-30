"""Unit tests for FMP provider modules."""

import re
from datetime import date

import pytest
from openbb_core.app.service.user_service import UserService
from openbb_fmp.models.analyst_estimates import FMPAnalystEstimatesFetcher
from openbb_fmp.models.available_indices import FMPAvailableIndicesFetcher
from openbb_fmp.models.balance_sheet import FMPBalanceSheetFetcher
from openbb_fmp.models.balance_sheet_growth import FMPBalanceSheetGrowthFetcher
from openbb_fmp.models.calendar_dividend import FMPCalendarDividendFetcher
from openbb_fmp.models.calendar_earnings import FMPCalendarEarningsFetcher
from openbb_fmp.models.calendar_events import FMPCalendarEventsFetcher
from openbb_fmp.models.calendar_ipo import FMPCalendarIpoFetcher
from openbb_fmp.models.calendar_splits import FMPCalendarSplitsFetcher
from openbb_fmp.models.cash_flow import FMPCashFlowStatementFetcher
from openbb_fmp.models.cash_flow_growth import FMPCashFlowStatementGrowthFetcher
from openbb_fmp.models.company_filings import FMPCompanyFilingsFetcher
from openbb_fmp.models.company_news import FMPCompanyNewsFetcher
from openbb_fmp.models.crypto_historical import FMPCryptoHistoricalFetcher
from openbb_fmp.models.crypto_search import FMPCryptoSearchFetcher
from openbb_fmp.models.currency_historical import FMPCurrencyHistoricalFetcher
from openbb_fmp.models.currency_pairs import FMPCurrencyPairsFetcher
from openbb_fmp.models.currency_snapshots import FMPCurrencySnapshotsFetcher
from openbb_fmp.models.discovery_filings import FMPDiscoveryFilingsFetcher
from openbb_fmp.models.earnings_call_transcript import FMPEarningsCallTranscriptFetcher
from openbb_fmp.models.economic_calendar import FMPEconomicCalendarFetcher
from openbb_fmp.models.equity_gainers import FMPGainersFetcher
from openbb_fmp.models.equity_historical import FMPEquityHistoricalFetcher
from openbb_fmp.models.equity_losers import FMPLosersFetcher
from openbb_fmp.models.equity_most_active import FMPEquityActiveFetcher
from openbb_fmp.models.equity_ownership import FMPEquityOwnershipFetcher
from openbb_fmp.models.equity_peers import FMPEquityPeersFetcher
from openbb_fmp.models.equity_profile import FMPEquityProfileFetcher
from openbb_fmp.models.equity_quote import FMPEquityQuoteFetcher
from openbb_fmp.models.equity_screener import FMPEquityScreenerFetcher
from openbb_fmp.models.esg_score import FMPEsgScoreFetcher
from openbb_fmp.models.etf_countries import FMPEtfCountriesFetcher
from openbb_fmp.models.etf_equity_exposure import FMPEtfEquityExposureFetcher
from openbb_fmp.models.etf_holdings import FMPEtfHoldingsFetcher
from openbb_fmp.models.etf_info import FMPEtfInfoFetcher
from openbb_fmp.models.etf_search import FMPEtfSearchFetcher
from openbb_fmp.models.etf_sectors import FMPEtfSectorsFetcher
from openbb_fmp.models.executive_compensation import FMPExecutiveCompensationFetcher
from openbb_fmp.models.financial_ratios import FMPFinancialRatiosFetcher
from openbb_fmp.models.forward_ebitda_estimates import FMPForwardEbitdaEstimatesFetcher
from openbb_fmp.models.forward_eps_estimates import FMPForwardEpsEstimatesFetcher
from openbb_fmp.models.government_trades import FMPGovernmentTradesFetcher
from openbb_fmp.models.historical_dividends import FMPHistoricalDividendsFetcher
from openbb_fmp.models.historical_employees import FMPHistoricalEmployeesFetcher
from openbb_fmp.models.historical_enterprise_value import (
    FMPHistoricalEnterpriseValueFetcher,
)
from openbb_fmp.models.historical_eps import FMPHistoricalEpsFetcher
from openbb_fmp.models.historical_industry_pe import FMPHistoricalIndustryPEFetcher
from openbb_fmp.models.historical_industry_performance import FMPHistoricalIndustryPerformanceFetcher
from openbb_fmp.models.historical_market_cap import FmpHistoricalMarketCapFetcher
from openbb_fmp.models.historical_sector_pe import FMPHistoricalSectorPEFetcher
from openbb_fmp.models.historical_sector_performance import FMPHistoricalSectorPerformanceFetcher
from openbb_fmp.models.historical_splits import FMPHistoricalSplitsFetcher
from openbb_fmp.models.income_statement import FMPIncomeStatementFetcher
from openbb_fmp.models.income_statement_growth import FMPIncomeStatementGrowthFetcher
from openbb_fmp.models.index_constituents import (
    FMPIndexConstituentsFetcher,
)
from openbb_fmp.models.index_historical import FMPIndexHistoricalFetcher
from openbb_fmp.models.insider_trading import FMPInsiderTradingFetcher
from openbb_fmp.models.institutional_ownership import FMPInstitutionalOwnershipFetcher
from openbb_fmp.models.key_executives import FMPKeyExecutivesFetcher
from openbb_fmp.models.key_metrics import FMPKeyMetricsFetcher
from openbb_fmp.models.market_snapshots import FMPMarketSnapshotsFetcher
from openbb_fmp.models.nport_disclosure import FMPNportDisclosureFetcher
from openbb_fmp.models.price_performance import FMPPricePerformanceFetcher
from openbb_fmp.models.price_target import FMPPriceTargetFetcher
from openbb_fmp.models.price_target_consensus import FMPPriceTargetConsensusFetcher
from openbb_fmp.models.revenue_business_line import FMPRevenueBusinessLineFetcher
from openbb_fmp.models.revenue_geographic import FMPRevenueGeographicFetcher
from openbb_fmp.models.risk_premium import FMPRiskPremiumFetcher
from openbb_fmp.models.share_statistics import FMPShareStatisticsFetcher
from openbb_fmp.models.treasury_rates import FMPTreasuryRatesFetcher
from openbb_fmp.models.world_news import FMPWorldNewsFetcher
from openbb_fmp.models.yield_curve import FMPYieldCurveFetcher

test_credentials = UserService().default_user_settings.credentials.model_dump(
    mode="json"
)


def response_filter(response):
    """Filter the response."""
    if "Location" in response["headers"]:
        response["headers"]["Location"] = [
            re.sub(r"apikey=[^&]+", "apikey=MOCK_API_KEY", x)
            for x in response["headers"]["Location"]
        ]
    return response


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "filter_headers": [("User-Agent", None)],
        "filter_query_parameters": [
            ("apikey", "MOCK_API_KEY"),
        ],
        "before_record_response": response_filter,
    }


@pytest.mark.record_http
def test_fmp_company_filings_fetcher(credentials=test_credentials):
    """Test FMP company filings fetcher."""
    params = {
        "symbol": "AAPL",
        "form_type": "10-K",
        "limit": 2,
        "start_date": date(2024, 9, 20),
        "end_date": date(2024, 10, 20),
    }

    fetcher = FMPCompanyFilingsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_crypto_historical_fetcher(credentials=test_credentials):
    """Test FMP crypto historical fetcher."""
    params = {
        "symbol": "BTCUSD",
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 1, 10),
    }

    fetcher = FMPCryptoHistoricalFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_currency_historical_fetcher(credentials=test_credentials):
    """Test FMP currency historical fetcher."""
    params = {
        "symbol": "EURUSD",
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 1, 10),
    }

    fetcher = FMPCurrencyHistoricalFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_index_historical_fetcher(credentials=test_credentials):
    """Test FMP index historical fetcher."""
    params = {
        "symbol": "^DJI",
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 1, 10),
    }

    fetcher = FMPIndexHistoricalFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


def test_fmp_historical_sector_performance_transform():
    fetcher = FMPHistoricalSectorPerformanceFetcher()
    data = fetcher.transform_data(
        fetcher.transform_query(
            {
                "sector": "Technology",
                "exchange": "NASDAQ",
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            }
        ),
        [
            {"date": "2024-01-02", "sector": "Technology", "exchange": "NASDAQ", "averageChange": 1.5},
            {"date": "2024-01-01", "sector": "Technology", "exchange": "NASDAQ", "averageChange": 1.0},
        ],
    )
    assert [row.date.isoformat() for row in data] == ["2024-01-01", "2024-01-02"]
    assert data[0].change_percent == 0.01


def test_fmp_historical_industry_performance_transform():
    fetcher = FMPHistoricalIndustryPerformanceFetcher()
    data = fetcher.transform_data(
        fetcher.transform_query(
            {
                "industry": "Software",
                "exchange": "NASDAQ",
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            }
        ),
        [{"date": "2024-01-02", "industry": "Software", "exchange": "NASDAQ", "averageChange": 2.5}],
    )
    assert data[0].change_percent == 0.025


def test_fmp_historical_sector_pe_transform():
    fetcher = FMPHistoricalSectorPEFetcher()
    data = fetcher.transform_data(
        fetcher.transform_query(
            {
                "sector": "Technology",
                "exchange": "NASDAQ",
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            }
        ),
        [{"date": "2024-01-02", "sector": "Technology", "exchange": "NASDAQ", "pe": 25.5}],
    )
    assert data[0].pe == 25.5


def test_fmp_historical_industry_pe_transform():
    fetcher = FMPHistoricalIndustryPEFetcher()
    data = fetcher.transform_data(
        fetcher.transform_query(
            {
                "industry": "Software",
                "exchange": "NASDAQ",
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            }
        ),
        [{"date": "2024-01-02", "industry": "Software", "exchange": "NASDAQ", "pe": 34.2}],
    )
    assert data[0].pe == 34.2


@pytest.mark.record_http
def test_fmp_equity_historical_fetcher(credentials=test_credentials):
    """Test FMP equity historical fetcher."""
    params = {
        "symbol": "AAPL",
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 1, 10),
        "interval": "1d",
    }

    fetcher = FMPEquityHistoricalFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_company_news_fetcher(credentials=test_credentials):
    """Test FMP company news fetcher."""
    params = {"symbol": "AAPL,MSFT", "limit": 1}

    fetcher = FMPCompanyNewsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_balance_sheet_fetcher(credentials=test_credentials):
    """Test FMP balance sheet fetcher."""
    params = {"symbol": "AAPL", "limit": 1}

    fetcher = FMPBalanceSheetFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_cash_flow_statement_fetcher(credentials=test_credentials):
    """Test FMP cash flow statement fetcher."""
    params = {"symbol": "AAPL", "limit": 1}

    fetcher = FMPCashFlowStatementFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_income_statement_fetcher(credentials=test_credentials):
    """Test FMP income statement fetcher."""
    params = {"symbol": "AAPL", "limit": 1}

    fetcher = FMPIncomeStatementFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_available_indices_fetcher(credentials=test_credentials):
    """Test FMP available indices fetcher."""
    params = {}

    fetcher = FMPAvailableIndicesFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_key_executives_fetcher(credentials=test_credentials):
    """Test FMP key executives fetcher."""
    params = {"symbol": "AAPL"}

    fetcher = FMPKeyExecutivesFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_world_news_fetcher(credentials=test_credentials):
    """Test FMP world news fetcher."""
    params = {"limit": 1}

    fetcher = FMPWorldNewsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_income_statement_growth_fetcher(credentials=test_credentials):
    """Test FMP income statement growth fetcher."""
    params = {"symbol": "AAPL", "limit": 1}

    fetcher = FMPIncomeStatementGrowthFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_balance_sheet_growth_fetcher(credentials=test_credentials):
    """Test FMP balance sheet growth fetcher."""
    params = {"symbol": "AAPL", "limit": 1, "period": "annual"}

    fetcher = FMPBalanceSheetGrowthFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_cash_flow_statement_growth_fetcher(credentials=test_credentials):
    """Test FMP cash flow statement growth fetcher."""
    params = {"symbol": "AAPL", "limit": 1, "period": "annual"}

    fetcher = FMPCashFlowStatementGrowthFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_share_statistics_fetcher(credentials=test_credentials):
    """Test FMP share statistics fetcher."""
    params = {"symbol": "AAPL,MSFT"}

    fetcher = FMPShareStatisticsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_revenue_geographic_fetcher(credentials=test_credentials):
    """Test FMP revenue geographic fetcher."""
    params = {"symbol": "AAPL", "period": "annual"}

    fetcher = FMPRevenueGeographicFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_revenue_business_line_fetcher(credentials=test_credentials):
    """Test FMP revenue business line fetcher."""
    params = {"symbol": "AAPL", "period": "annual"}

    fetcher = FMPRevenueBusinessLineFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_institutional_ownership_fetcher(credentials=test_credentials):
    """Test FMP institutional ownership fetcher."""
    params = {"symbol": "AAPL,MSFT", "year": 2025, "quarter": 2}

    fetcher = FMPInstitutionalOwnershipFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


def test_fmp_institutional_ownership_fetcher_fetches_date_window(monkeypatch):
    """Test FMP institutional ownership fetches each quarter in a date window."""
    import asyncio
    from urllib.parse import parse_qs, urlparse

    requested_urls = []

    async def mock_amake_request(url, **kwargs):
        requested_urls.append(url)
        query = parse_qs(urlparse(url).query)
        year = int(query["year"][0])
        quarter = int(query["quarter"][0])
        return [
            {
                "symbol": "AAPL",
                "date": f"{year}-{quarter * 3:02d}-30",
                "investorsHolding": 100 + quarter,
                "lastInvestorsHolding": 100,
                "investorsHoldingChange": quarter,
                "totalInvested": 1000,
                "lastTotalInvested": 900,
                "totalInvestedChange": 100,
                "ownershipPercent": 50,
                "lastOwnershipPercent": 49,
                "changeInOwnershipPercentage": 1,
                "newPositions": 1,
                "lastNewPositions": 0,
                "newPositionsChange": 1,
                "increasedPositions": 2,
                "lastIncreasedPositions": 1,
                "increasedPositionsChange": 1,
                "closedPositions": 0,
                "lastClosedPositions": 1,
                "closedPositionsChange": -1,
                "reducedPositions": 1,
                "lastReducedPositions": 2,
                "reducedPositionsChange": -1,
                "totalCalls": 0,
                "lastTotalCalls": 0,
                "totalCallsChange": 0,
                "totalPuts": 0,
                "lastTotalPuts": 0,
                "totalPutsChange": 0,
                "putCallRatio": 0,
                "lastPutCallRatio": 0,
                "putCallRatioChange": 0,
            }
        ]

    monkeypatch.setattr(
        "openbb_core.provider.utils.helpers.amake_request",
        mock_amake_request,
    )

    query = FMPInstitutionalOwnershipFetcher.transform_query(
        {"symbol": "AAPL", "start_date": "2025-01-01", "end_date": "2025-06-30"}
    )
    data = asyncio.run(
        FMPInstitutionalOwnershipFetcher.aextract_data(
            query, {"fmp_api_key": "MOCK_API_KEY"}
        )
    )

    assert len(data) >= 2
    assert any("year=2025&quarter=1" in url for url in requested_urls)
    assert any("year=2025&quarter=2" in url for url in requested_urls)


@pytest.mark.record_http
def test_fmp_insider_trading_fetcher(credentials=test_credentials):
    """Test FMP insider trading fetcher."""
    params = {"symbol": "AAPL", "limit": 1, "transaction_type": "purchase"}

    fetcher = FMPInsiderTradingFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


def test_fmp_insider_trading_fetcher_paginates_full_symbol_history(monkeypatch):
    """Test FMP insider trading fetches all symbol pages when no limit is set."""
    import asyncio
    from urllib.parse import parse_qs, urlparse

    requested_urls = []

    async def mock_amake_request(url, **kwargs):
        requested_urls.append(url)
        query = parse_qs(urlparse(url).query)
        page = int(query["page"][0])

        if page in {0, 1}:
            return [
                {
                    "symbol": "AAPL",
                    "filingDate": f"2024-01-{page + 1:02d}",
                    "transactionDate": f"2024-01-{page + 1:02d}",
                    "reportingName": f"Insider {page}-{i}",
                    "transactionType": "P-Purchase",
                }
                for i in range(1000)
            ]
        if page == 2:
            return [
                {
                    "symbol": "AAPL",
                    "filingDate": "2024-01-03",
                    "transactionDate": "2024-01-03",
                    "reportingName": "Insider 2-0",
                    "transactionType": "S-Sale",
                }
            ]
        return []

    monkeypatch.setattr(
        "openbb_core.provider.utils.helpers.amake_request",
        mock_amake_request,
    )

    query = FMPInsiderTradingFetcher.transform_query({"symbol": "AAPL"})
    data = asyncio.run(
        FMPInsiderTradingFetcher.aextract_data(
            query, {"fmp_api_key": "MOCK_API_KEY"}
        )
    )

    assert len(data) == 2001
    assert any("page=2" in url for url in requested_urls)
    assert all("limit=1000" in url for url in requested_urls)


@pytest.mark.record_http
def test_fmp_equity_ownership_fetcher(credentials=test_credentials):
    """Test FMP equity ownership fetcher."""
    params = {"symbol": "AAPL", "year": 2025, "quarter": 2, "limit": 1}

    fetcher = FMPEquityOwnershipFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_price_target_consensus_fetcher(credentials=test_credentials):
    """Test FMP price target consensus fetcher."""
    params = {"symbol": "AAPL,MSFT"}

    fetcher = FMPPriceTargetConsensusFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_price_target_fetcher(credentials=test_credentials):
    """Test FMP price target fetcher."""
    params = {"symbol": "AAPL", "limit": 1}

    fetcher = FMPPriceTargetFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


def test_fmp_price_target_fetcher_paginates_full_symbol_history(monkeypatch):
    """Test FMP price target fetches all symbol pages when no limit is set."""
    import asyncio
    from urllib.parse import parse_qs, urlparse

    requested_urls = []

    async def mock_amake_request(url, **kwargs):
        requested_urls.append(url)
        query = parse_qs(urlparse(url).query)
        page = int(query["page"][0])

        if page in {0, 1}:
            return [
                {
                    "symbol": "AAPL",
                    "publishedDate": f"2024-01-{page + 1:02d}",
                    "newsTitle": f"Price Target {page}-{i}",
                    "analystCompany": "Test Firm",
                    "priceTarget": 200 + page,
                }
                for i in range(100)
            ]
        if page == 2:
            return [
                {
                    "symbol": "AAPL",
                    "publishedDate": "2024-01-03",
                    "newsTitle": "Price Target 2-0",
                    "analystCompany": "Test Firm",
                    "priceTarget": 205,
                }
            ]
        return []

    monkeypatch.setattr(
        "openbb_core.provider.utils.helpers.amake_request",
        mock_amake_request,
    )

    query = FMPPriceTargetFetcher.transform_query({"symbol": "AAPL"})
    data = asyncio.run(
        FMPPriceTargetFetcher.aextract_data(query, {"fmp_api_key": "MOCK_API_KEY"})
    )

    assert len(data) == 201
    assert any("page=2" in url for url in requested_urls)
    assert all("limit=100" in url for url in requested_urls)


@pytest.mark.record_http
def test_fmp_analyst_estimates_fetcher(credentials=test_credentials):
    """Test FMP analyst estimates fetcher."""
    params = {"symbol": "AAPL,MSFT", "limit": 1}

    fetcher = FMPAnalystEstimatesFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_historical_eps_fetcher(credentials=test_credentials):
    """Test FMP historical EPS fetcher."""
    params = {"symbol": "AAPL,MSFT", "limit": 1}

    fetcher = FMPHistoricalEpsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_earnings_call_transcript_fetcher(credentials=test_credentials):
    """Test FMP earnings call transcript fetcher."""
    params = {"symbol": "AAPL", "year": 2025, "quarter": 3}

    fetcher = FMPEarningsCallTranscriptFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_historical_splits_fetcher(credentials=test_credentials):
    """Test FMP historical splits fetcher."""
    params = {"symbol": "AAPL"}

    fetcher = FMPHistoricalSplitsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_calendar_splits_fetcher(credentials=test_credentials):
    """Test FMP calendar splits fetcher."""
    params = {"start_date": date(2023, 1, 1), "end_date": date(2023, 1, 10)}

    fetcher = FMPCalendarSplitsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_historical_dividends_fetcher(credentials=test_credentials):
    """Test FMP historical dividends fetcher."""
    params = {"symbol": "AAPL", "limit": 1}

    fetcher = FMPHistoricalDividendsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_key_metrics_fetcher(credentials=test_credentials):
    """Test FMP key metrics fetcher."""
    params = {"symbol": "AAPL"}

    fetcher = FMPKeyMetricsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_treasury_rates_fetcher(credentials=test_credentials):
    """Test FMP treasury rates fetcher."""
    params = {"start_date": date(2023, 1, 1), "end_date": date(2023, 1, 10)}

    fetcher = FMPTreasuryRatesFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_executive_compensation_fetcher(credentials=test_credentials):
    """Test FMP executive compensation fetcher."""
    params = {"symbol": "AAPL", "year": 2024}

    fetcher = FMPExecutiveCompensationFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_currency_pairs_fetcher(credentials=test_credentials):
    """Test FMP currency pairs fetcher."""
    params = {}

    fetcher = FMPCurrencyPairsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_equity_peers_fetcher(credentials=test_credentials):
    """Test FMP equity peers fetcher."""
    params = {"symbol": "AAPL"}

    fetcher = FMPEquityPeersFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_historical_employees_fetcher(credentials=test_credentials):
    """Test FMP historical employees fetcher."""
    params = {"symbol": "AAPL", "limit": 1}

    fetcher = FMPHistoricalEmployeesFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_risk_premium_fetcher(credentials=test_credentials):
    """Test FMP risk premium fetcher."""
    params = {}

    fetcher = FMPRiskPremiumFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_index_constituents_fetcher(credentials=test_credentials):
    """Test FMP index constituents fetcher."""
    params = {"symbol": "dowjones", "historical": False}

    fetcher = FMPIndexConstituentsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_calendar_dividend_fetcher(credentials=test_credentials):
    """Test FMP calendar dividend fetcher."""
    params = {"start_date": date(2023, 11, 6), "end_date": date(2023, 11, 10)}

    fetcher = FMPCalendarDividendFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_equity_quote_fetcher(credentials=test_credentials):
    """Test FMP equity quote fetcher."""
    params = {"symbol": "AAPL"}

    fetcher = FMPEquityQuoteFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_equity_screener_fetcher(credentials=test_credentials):
    """Test FMP equity screener fetcher."""
    params = {
        "industry": "oil_gas_midstream",
        "sector": "energy",
        "beta_max": 0.5,
        "limit": 2,
    }

    fetcher = FMPEquityScreenerFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_financial_ratios_fetcher(credentials=test_credentials):
    """Test FMP financial ratios fetcher."""
    params = {"symbol": "AAPL"}

    fetcher = FMPFinancialRatiosFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_economic_calendar_fetcher(credentials=test_credentials):
    """Test FMP economic calendar fetcher."""
    params = {"start_date": date(2024, 1, 1), "end_date": date(2024, 3, 30)}

    fetcher = FMPEconomicCalendarFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_market_snapshots_fetcher(credentials=test_credentials):
    """Test FMP market snapshots fetcher."""
    params = {"market": "neo"}

    fetcher = FMPMarketSnapshotsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_etf_search_fetcher(credentials=test_credentials):
    """Test FMP ETF search fetcher."""
    params = {"query": "India", "exchange": "tsx"}

    fetcher = FMPEtfSearchFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_etf_info_fetcher(credentials=test_credentials):
    """Test FMP ETF info fetcher."""
    params = {"symbol": "IOO"}

    fetcher = FMPEtfInfoFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_etf_sectors_fetcher(credentials=test_credentials):
    """Test FMP ETF sectors fetcher."""
    params = {"symbol": "IOO"}

    fetcher = FMPEtfSectorsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_etf_holdings_fetcher(credentials=test_credentials):
    """Test FMP ETF holdings fetcher."""
    params = {"symbol": "DIA"}

    fetcher = FMPEtfHoldingsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_etf_nport_disclosure_fetcher(credentials=test_credentials):
    """Test FMP ETF N-PORT disclosure fetcher."""
    params = {"symbol": "DIA", "year": 2025, "quarter": 1}

    fetcher = FMPNportDisclosureFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_price_performance_fetcher(credentials=test_credentials):
    """Test FMP price performance fetcher."""
    params = {"symbol": "AAPL,SPY,BTCUSD"}

    fetcher = FMPPricePerformanceFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_etf_countries_fetcher(credentials=test_credentials):
    """Test FMP ETF countries fetcher."""
    params = {"symbol": "VTI,QQQ,VOO,IWM"}

    fetcher = FMPEtfCountriesFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_discovery_filings_fetcher(credentials=test_credentials):
    """Test FMP discovery filings fetcher."""
    params = {
        "start_date": date(2025, 9, 20),
        "end_date": date(2025, 9, 22),
        "form_type": None,
        "limit": 2,
    }

    fetcher = FMPDiscoveryFilingsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_crypto_search_fetcher(credentials=test_credentials):
    """Test FMP crypto search fetcher."""
    params = {"query": "asd"}

    fetcher = FMPCryptoSearchFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_calendar_earnings_fetcher(credentials=test_credentials):
    """Test FMP calendar earnings fetcher."""
    params = {"symbol": "AAPL"}

    params = {
        "start_date": date(2023, 11, 6),
        "end_date": date(2023, 11, 10),
    }
    fetcher = FMPCalendarEarningsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_equity_profile_fetcher(credentials=test_credentials):
    """Test FMP equity profile fetcher."""
    params = {"symbol": "AAPL"}

    fetcher = FMPEquityProfileFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_etf_equity_exposure_fetcher(credentials=test_credentials):
    """Test FMP ETF equity exposure fetcher."""
    params = {"symbol": "CNST"}

    fetcher = FMPEtfEquityExposureFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_currency_snapshots_fetcher(credentials=test_credentials):
    """Test FMP currency snapshots fetcher."""
    params = {
        "base": "XAU",
        "quote_type": "indirect",
        "counter_currencies": "USD,EUR,GBP,JPY,HKD,AUD,CAD,CHF,SEK,NZD,SGD",
    }

    fetcher = FMPCurrencySnapshotsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_equity_forward_eps_fetcher(credentials=test_credentials):
    """Test FMP forward EPS estimates fetcher."""
    params = {
        "symbol": "MSFT,AAPL",
        "fiscal_period": "annual",
        "include_historical": False,
        "limit": None,
    }

    fetcher = FMPForwardEpsEstimatesFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_equity_forward_ebitda_fetcher(credentials=test_credentials):
    """Test FMP forward EBITDA estimates fetcher."""
    params = {
        "symbol": "MSFT,AAPL",
        "fiscal_period": "annual",
        "include_historical": False,
        "limit": None,
    }

    fetcher = FMPForwardEbitdaEstimatesFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_yield_curve_fetcher(credentials=test_credentials):
    """Test FMP Yield Curve Fetcher."""
    params = {"date": "2024-05-14,2023-05-14"}

    fetcher = FMPYieldCurveFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_historical_market_cap_fetcher(credentials=test_credentials):
    """Test FMP Historical Market Cap Fetcher."""
    params = {
        "symbol": "AAPL",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 1, 31),
    }

    fetcher = FmpHistoricalMarketCapFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_historical_enterprise_value_fetcher(credentials=test_credentials):
    """Test FMP Historical Enterprise Value Fetcher."""
    params = {
        "symbol": "AAPL",
        "start_date": date(2024, 1, 1),
        "end_date": date(2025, 12, 31),
        "limit": 10,
    }

    fetcher = FMPHistoricalEnterpriseValueFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_government_trades_fetcher(credentials=test_credentials):
    """Test FMP government trades fetcher.
    params limit only functions when there is no parameter symbol.
    """
    params = {
        "chamber": "senate",
        "limit": 1,
    }
    fetcher = FMPGovernmentTradesFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


def test_fmp_government_trades_fetcher_paginates_symbol(monkeypatch):
    """Test FMP government trades fetches all symbol pages."""
    import asyncio
    from urllib.parse import parse_qs, urlparse

    requested_urls = []

    async def mock_amake_request(url, **kwargs):
        requested_urls.append(url)
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        page = int(query["page"][0])
        endpoint = parsed.path.rsplit("/", 1)[-1]

        if endpoint == "house-trades" and page == 0:
            return [
                {
                    "ticker": "AAPL",
                    "disclosureDate": "2024-01-01",
                    "transactionDate": "2023-12-29",
                    "office": f"House Member {i}",
                    "type": "Purchase",
                }
                for i in range(100)
            ]
        if endpoint == "house-trades" and page == 1:
            return [
                {
                    "ticker": "AAPL",
                    "disclosureDate": "2024-01-02",
                    "transactionDate": "2023-12-30",
                    "office": "House Member 100",
                    "type": "Sale",
                }
            ]
        if endpoint == "senate-trades" and page == 0:
            return [
                {
                    "ticker": "AAPL",
                    "disclosureDate": "2024-01-03",
                    "transactionDate": "2023-12-31",
                    "office": "Senate Member",
                    "type": "Purchase",
                }
            ]
        return []

    monkeypatch.setattr(
        "openbb_core.provider.utils.helpers.amake_request",
        mock_amake_request,
    )

    query = FMPGovernmentTradesFetcher.transform_query(
        {"symbol": "AAPL", "chamber": "all"}
    )
    data = asyncio.run(
        FMPGovernmentTradesFetcher.aextract_data(
            query, {"fmp_api_key": "MOCK_API_KEY"}
        )
    )

    assert len(data) == 102
    assert any("house-trades?symbol=AAPL&page=1" in url for url in requested_urls)
    assert all("limit=100" in url for url in requested_urls)
    assert {entry["chamber"] for entry in data} == {"House", "Senate"}


@pytest.mark.record_http
def test_fmp_calendar_events_fetcher(credentials=test_credentials):
    """Test FMP calendar events fetcher."""
    params = {
        "start_date": date(2025, 1, 7),
        "end_date": date(2025, 1, 10),
    }
    fetcher = FMPCalendarEventsFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_equity_gainers_fetcher(credentials=test_credentials):
    """Test FMP equity gainers fetcher."""
    params = {}
    fetcher = FMPGainersFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_equity_losers_fetcher(credentials=test_credentials):
    """Test FMP equity losers fetcher."""
    params = {}
    fetcher = FMPLosersFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_esg_score(credentials=test_credentials):
    """Test FMP ESG score fetcher."""
    params = {"symbol": "AAPL"}
    fetcher = FMPEsgScoreFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_calendar_ipo_fetcher(credentials=test_credentials):
    """Test FMP calendar IPO fetcher."""
    params = {"start_date": date(2024, 9, 20), "end_date": date(2024, 10, 20)}
    fetcher = FMPCalendarIpoFetcher()
    result = fetcher.test(params, credentials)
    assert result is None


@pytest.mark.record_http
def test_fmp_equity_active_fetcher(credentials=test_credentials):
    """Test FMP equity active fetcher."""
    params = {}
    fetcher = FMPEquityActiveFetcher()
    result = fetcher.test(params, credentials)
    assert result is None
