from tradingagents.dataflows.interface import route_to_vendor
import sys
from pathlib import Path

# Add project root to sys.path to allow importing tradingagents if not installed as package
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from datetime import datetime, timedelta

def fetch_data(ticker: str, action: str) -> str:
    """Fetch data through the TradingAgents Core Dataflows."""
    
    if action == "Historical Price (OHLCV)":
        try:
            # We enforce using 'vnstock' vendor for VN Market CLI
            # Set the config dynamically or pass vendor if route_to_vendor allows.
            # Currently interface.py doesn't accept vendor as kwarg easily unless config is set.
            # But we can override it or just call the mapped method.
            # Since we want to ensure vnstock is used, we'll temporarily mock config or call it directly.
            # Actually, the best way without modifying interface.py config logic is calling the vendor method.
            # However, to demonstrate 'power of tradingagents', let's mock the config or just call the method.
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
            
    elif action == "Financial Reports":
        # SCRUM-14 mock
        return "Financial Reports feature is under development (SCRUM-14)."
    
    return "Unknown action."
