from typing import Annotated
from datetime import datetime, timedelta
import pandas as pd
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

try:
    from vnstock.api.quote import Quote
    from vnstock.api.company import Company
    from vnstock.api.financial import Finance
    VNSTOCK_AVAILABLE = True
except ImportError:
    VNSTOCK_AVAILABLE = False

def vnstock_retry(max_retries=3, base_delay=2.0):
    """Decorator to retry vnstock API calls on failure with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"vnstock API call failed ({e}), retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        logger.error(f"vnstock API call completely failed after {max_retries} retries: {e}")
                        # Depending on the function signature we want to return a string or raise. 
                        # Since all vnstock_api functions return strings for the LLM, we return the error string.
                        return f"Error: Failed to fetch data after {max_retries} retries due to {e}"
        return wrapper
    return decorator

@vnstock_retry()
def get_vnstock_data_online(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Fetch historical OHLCV data using vnstock and return as CSV string."""
    if not VNSTOCK_AVAILABLE:
        return "Error: vnstock library is not installed."
        
    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")
    
    q = Quote(symbol=symbol.upper(), source='VCI')
    data = q.history(start=start_date, end=end_date)
    
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

@vnstock_retry()
def get_vnstock_fundamentals(
    ticker: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "current date (not used for vnstock)"] = None
) -> str:
    """Get company fundamentals overview from vnstock."""
    if not VNSTOCK_AVAILABLE:
        return "Error: vnstock library is not installed."
        
    c = Company(symbol=ticker.upper(), source='VCI')
    data = c.overview()
    
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

def _format_financials_to_csv(data: pd.DataFrame, ticker: str, report_type: str, freq: str) -> str:
    """Helper method to format vnstock financial dataframe to CSV string"""
    if data is None or data.empty:
        return f"No {report_type} data found for symbol '{ticker}'"
        
    # Convert dataframe to CSV string
    csv_string = data.to_csv(index=False)
    
    header = f"# {report_type} data for {ticker.upper()} ({freq})\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    return header + csv_string

@vnstock_retry()
def get_vnstock_balance_sheet(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format (not used)"] = None
) -> str:
    """Get balance sheet data from vnstock."""
    if not VNSTOCK_AVAILABLE:
        return "Error: vnstock library is not installed."
        
    f = Finance(symbol=ticker.upper(), source='VCI')
    period = "year" if freq.lower() == "annual" else "quarter"
    
    data = f.balance_sheet(period=period, lang='vi')
    return _format_financials_to_csv(data, ticker, "Balance Sheet", freq)

@vnstock_retry()
def get_vnstock_income_statement(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format (not used)"] = None
) -> str:
    """Get income statement data from vnstock."""
    if not VNSTOCK_AVAILABLE:
        return "Error: vnstock library is not installed."
        
    f = Finance(symbol=ticker.upper(), source='VCI')
    period = "year" if freq.lower() == "annual" else "quarter"
    
    data = f.income_statement(period=period, lang='vi')
    return _format_financials_to_csv(data, ticker, "Income Statement", freq)

@vnstock_retry()
def get_vnstock_cashflow(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format (not used)"] = None
) -> str:
    """Get cash flow data from vnstock."""
    if not VNSTOCK_AVAILABLE:
        return "Error: vnstock library is not installed."
        
    f = Finance(symbol=ticker.upper(), source='VCI')
    period = "year" if freq.lower() == "annual" else "quarter"
    
    data = f.cash_flow(period=period, lang='vi')
    return _format_financials_to_csv(data, ticker, "Cash Flow", freq)
