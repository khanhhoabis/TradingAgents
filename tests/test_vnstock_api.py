import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from tradingagents.dataflows.vnstock_api import (
    get_vnstock_data_online,
    get_vnstock_fundamentals,
    get_vnstock_balance_sheet,
    vnstock_retry
)
from datetime import datetime

# Fixtures for mock data
@pytest.fixture
def mock_ohlcv_data():
    return pd.DataFrame({
        'time': ['2023-01-01', '2023-01-02'],
        'open': [10.0, 11.0],
        'high': [12.0, 13.0],
        'low': [9.0, 10.0],
        'close': [11.0, 12.0],
        'volume': [1000, 2000]
    })

@pytest.fixture
def mock_empty_data():
    return pd.DataFrame()

@pytest.fixture
def mock_fundamentals_data():
    return pd.DataFrame({
        'ticker': ['FPT'],
        'market_cap': [100000],
        'pe': [15.5]
    })

# Tests
@patch('tradingagents.dataflows.vnstock_api.Quote')
def test_get_vnstock_data_online_success(MockQuote, mock_ohlcv_data):
    # Setup mock
    mock_instance = MockQuote.return_value
    mock_instance.history.return_value = mock_ohlcv_data

    # Call
    result = get_vnstock_data_online('FPT', '2023-01-01', '2023-01-02')

    # Assert
    assert "Stock data for FPT" in result
    assert "Total records: 2" in result
    assert "2023-01-01" in result
    assert "10.0" in result # open price

@patch('tradingagents.dataflows.vnstock_api.Quote')
def test_get_vnstock_data_online_empty(MockQuote, mock_empty_data):
    mock_instance = MockQuote.return_value
    mock_instance.history.return_value = mock_empty_data

    result = get_vnstock_data_online('INVALID', '2023-01-01', '2023-01-02')
    assert "No data found for symbol 'INVALID'" in result

@patch('tradingagents.dataflows.vnstock_api.Company')
def test_get_vnstock_fundamentals_success(MockCompany, mock_fundamentals_data):
    mock_instance = MockCompany.return_value
    mock_instance.overview.return_value = mock_fundamentals_data

    result = get_vnstock_fundamentals('FPT')
    assert "Company Profile for FPT" in result
    assert "Ticker: FPT" in result
    assert "Market_cap: 100000" in result

@patch('tradingagents.dataflows.vnstock_api.Finance')
def test_get_vnstock_balance_sheet_success(MockFinance):
    mock_instance = MockFinance.return_value
    mock_df = pd.DataFrame({'year': [2023], 'assets': [50000]})
    mock_instance.balance_sheet.return_value = mock_df

    result = get_vnstock_balance_sheet('FPT', freq='annual')
    assert "Balance Sheet data for FPT (annual)" in result
    assert "assets" in result
    assert "50000" in result
    
# Testing retry decorator
def test_vnstock_retry_success_after_failure():
    # Setup a mock function that fails twice then succeeds
    call_count = 0
    
    @vnstock_retry(max_retries=2, base_delay=0.01)
    def flacky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Network down")
        return "Success"
        
    result = flacky_func()
    assert result == "Success"
    assert call_count == 3

def test_vnstock_retry_max_retries_exceeded():
    call_count = 0
    
    @vnstock_retry(max_retries=2, base_delay=0.01)
    def failing_func():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Network down")
        
    result = failing_func()
    # It should not raise an exception, but return the error string per our implementation
    assert "Error: Failed to fetch data after 2 retries" in result
    assert call_count == 3 # 1 initial + 2 retries

@patch('tradingagents.dataflows.vnstock_api.time.sleep') # Mock sleep to speed up test
@patch('tradingagents.dataflows.vnstock_api.Quote')
def test_api_call_with_retry(MockQuote, mock_sleep):
    mock_instance = MockQuote.return_value
    
    # Make history raise exception 3 times (fails all retries)
    mock_instance.history.side_effect = Exception("Rate Limited")
    
    result = get_vnstock_data_online('FPT', '2023-01-01', '2023-01-02')
    
    assert "Error: Failed to fetch data after 3 retries due to Rate Limited" in result
    assert mock_sleep.call_count == 3
