from tradingagents.dataflows.interface import route_to_vendor
import sys
from pathlib import Path

# Add project root to sys.path to allow importing tradingagents if not installed as package
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from datetime import datetime, timedelta

def fetch_data(ticker: str, action: str, freq: str = "quarterly") -> str:
    """Fetch data through the TradingAgents Core Dataflows."""
    
    if action == "Historical Price (OHLCV)":
        try:
            from tradingagents.dataflows.vnstock_api import get_vnstock_data_online
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            return get_vnstock_data_online(symbol=ticker, start_date=start_date, end_date=end_date)
        except Exception as e:
            return f"Error: Failed to fetch historical data: {e}"
            
    elif action == "Company Profile":
        try:
            from tradingagents.dataflows.vnstock_api import get_vnstock_fundamentals
            return get_vnstock_fundamentals(ticker=ticker)
        except Exception as e:
            return f"Error: Failed to fetch profile data: {e}"
            
    elif action == "Balance Sheet":
        try:
            from tradingagents.dataflows.vnstock_api import get_vnstock_balance_sheet
            return get_vnstock_balance_sheet(ticker=ticker, freq=freq)
        except Exception as e:
            return f"Error: Failed to fetch balance sheet: {e}"
            
    elif action == "Income Statement":
        try:
            from tradingagents.dataflows.vnstock_api import get_vnstock_income_statement
            return get_vnstock_income_statement(ticker=ticker, freq=freq)
        except Exception as e:
            return f"Error: Failed to fetch income statement: {e}"
            
    elif action == "Cash Flow":
        try:
            from tradingagents.dataflows.vnstock_api import get_vnstock_cashflow
            return get_vnstock_cashflow(ticker=ticker, freq=freq)
        except Exception as e:
            return f"Error: Failed to fetch cash flow: {e}"
    
    return "Unknown action."
