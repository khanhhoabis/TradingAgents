import time

def fetch_mock_data(ticker: str, action: str):
    """Mock function to simulate fetching data from vnstock."""
    time.sleep(2) # Simulate network delay
    
    if action == "Historical Price (OHLCV)":
        return [
            {"date": "2026-05-10", "open": 100, "high": 105, "low": 98, "close": 102, "volume": 1500000},
            {"date": "2026-05-11", "open": 102, "high": 108, "low": 101, "close": 107, "volume": 2100000},
            {"date": "2026-05-12", "open": 106, "high": 109, "low": 105, "close": 106, "volume": 1800000},
        ]
    elif action == "Financial Reports":
        return [
            {"year": 2024, "revenue": 50000000000, "profit": 5000000000, "eps": 3500},
            {"year": 2025, "revenue": 62000000000, "profit": 7200000000, "eps": 4800},
        ]
    elif action == "Company Profile":
        return [
            {"field": "Name", "value": f"{ticker} Corporation"},
            {"field": "Industry", "value": "Technology"},
            {"field": "Listing Date", "value": "2010-01-01"},
            {"field": "Market Cap", "value": "120,000 Billion VND"},
        ]
    
    return []
