from vnstock import Vnstock

def run_trial(symbol='FPT'):
    print(f"=== Trial: Fetching data for {symbol} using vnstock v4.0 ===")
    
    # Initialize vnstock client
    client = Vnstock()
    stock = client.stock(symbol=symbol, source='VCI') # VCI is a common free source

    # 1. Company Overview
    print("\n[1] Company Overview:")
    try:
        overview = stock.company.overview()
        print(overview)
    except Exception as e:
        print(f"Error: {e}")

    # 2. Historical Data
    print("\n[2] Historical Data (Last 5 records):")
    try:
        # Note: end_date is usually current date if not specified
        df = stock.quote.history(start='2026-05-01', end='2026-05-15')
        print(df.tail())
    except Exception as e:
        print(f"Error: {e}")

    # 3. Recent News
    print("\n[3] Recent News:")
    try:
        news = stock.company.news()
        print(news.head(3))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_trial('FPT')
