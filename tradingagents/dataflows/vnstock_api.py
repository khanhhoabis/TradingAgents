from typing import Annotated
from datetime import datetime, timedelta
import pandas as pd

try:
    from vnstock import Vnstock
except ImportError:
    Vnstock = None

def get_vnstock_data_online(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Fetch historical OHLCV data using vnstock and return as CSV string."""
    if Vnstock is None:
        return "Error: vnstock library is not installed."
        
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
        
        client = Vnstock()
        stock = client.stock(symbol=symbol.upper(), source='VCI')
        
        data = stock.quote.history(start=start_date, end=end_date)
        
        if data is None or data.empty:
            return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"
            
        # Clean dataframe
        data = data.reset_index(drop=True)
        if 'time' in data.columns:
            data.set_index('time', inplace=True)
            
        # Round numerical values to 2 decimal places for cleaner display
        numeric_columns = ["open", "high", "low", "close", "volume"]
        for col in numeric_columns:
            if col in data.columns:
                data[col] = data[col].round(2)
                
        # Convert DataFrame to CSV string
        csv_string = data.to_csv()
        
        # Add header information
        header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
        header += f"# Total records: {len(data)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return header + csv_string
        
    except Exception as e:
        return f"Error retrieving data for {symbol}: {str(e)}"

def get_vnstock_fundamentals(
    ticker: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "current date (not used for vnstock)"] = None
) -> str:
    """Get company fundamentals overview from vnstock."""
    if Vnstock is None:
        return "Error: vnstock library is not installed."
        
    try:
        client = Vnstock()
        stock = client.stock(symbol=ticker.upper(), source='TCBS')
        
        data = stock.company.profile()
        
        if data is None or data.empty:
            return f"No fundamentals data found for symbol '{ticker}'"
            
        # Convert dataframe to a readable list of properties
        profile_dict = data.to_dict(orient='records')[0] if len(data) > 0 else {}
        
        lines = []
        for label, value in profile_dict.items():
            if value is not None and str(value).strip() != "":
                lines.append(f"{label.capitalize()}: {value}")
                
        header = f"# Company Profile for {ticker.upper()}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return header + "\n".join(lines)
        
    except Exception as e:
        return f"Error retrieving fundamentals for {ticker}: {str(e)}"
