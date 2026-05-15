import time
from datetime import datetime, timedelta

try:
    from vnstock import Vnstock
except ImportError:
    Vnstock = None

def fetch_data(ticker: str, action: str):
    """Fetch real data from vnstock API."""
    if Vnstock is None:
        # Fallback if vnstock is not installed
        return [{"error": "vnstock library is not installed. Please run 'pip install vnstock'"}]
        
    client = Vnstock()
    
    if action == "Historical Price (OHLCV)":
        try:
            # Fetch last 30 days of data
            stock = client.stock(symbol=ticker, source='VCI')
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            df = stock.quote.history(start=start_date, end=end_date)
            
            if df is None or df.empty:
                return [{"error": "No historical data found."}]
                
            # Convert timestamp to string if needed and drop index to make it clean
            df = df.reset_index(drop=True)
            # Convert date objects to string for JSON serialization
            if 'time' in df.columns:
                df['time'] = df['time'].astype(str)
                
            # Convert dataframe to list of dicts
            # Tail 10 to not spam the console
            return df.tail(10).to_dict(orient='records')
        except Exception as e:
            return [{"error": f"Failed to fetch historical data: {e}"}]
            
    elif action == "Company Profile":
        try:
            stock = client.stock(symbol=ticker, source='TCBS')
            df = stock.company.profile()
            
            if df is None or df.empty:
                return [{"error": "No profile data found."}]
                
            return df.to_dict(orient='records')
        except Exception as e:
            return [{"error": f"Failed to fetch profile data: {e}"}]
            
    elif action == "Financial Reports":
        # Kept mock for SCRUM-14
        return [
            {"year": 2024, "revenue": 50000000000, "profit": 5000000000, "eps": 3500},
            {"year": 2025, "revenue": 62000000000, "profit": 7200000000, "eps": 4800},
        ]
    
    return []
