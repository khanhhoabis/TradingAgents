"""Vietnam market data vendor (HOSE) backed by the vnstock library.

Implements the two market-data methods the vendor-routing layer expects
(``get_stock_data`` -> :func:`get_stock`, ``get_indicators`` ->
:func:`get_indicator`), matching the signatures and string-return contract
of the existing yfinance / alpha_vantage vendors in ``interface.py``.

Schema verified live against vnstock 4.0.8 (see
``docs/vnstock_schema_xac_minh.md``):

* ``Quote(symbol=...).history(start, end, interval="1D")`` returns a
  DataFrame with lowercase columns ``time, open, high, low, close, volume``
  (``time`` is a ``datetime64[ns]``). We rename these to the
  ``Date/Open/High/Low/Close/Volume`` schema that ``stockstats`` and the
  repo's ``_clean_dataframe`` expect, so the whole technical-indicator path
  is reused unchanged.
* The VN-Index benchmark symbol is ``VNINDEX`` (no ``^`` prefix).

vnstock is a client-side connector, not a licensed data API; callers must
respect the upstream source's terms. Telemetry and the promotional stdout
banner are suppressed here so they never leak into the string returned to
the agents.
"""

from __future__ import annotations

import io
import os
import contextlib
from datetime import datetime
from typing import Annotated

import pandas as pd

from .stockstats_utils import _clean_dataframe
from .utils import safe_ticker_component

# Suppress vnstock's optional telemetry before the library is imported.
os.environ.setdefault("VNSTOCK_TELEMETRY", "off")


class VnRateLimitError(Exception):
    """Raised when the VN data source rate-limits us.

    Kept distinct so ``route_to_vendor`` can be extended to treat it as a
    fallback trigger (today only ``AlphaVantageRateLimitError`` triggers a
    vendor fallback).
    """


# Indicator descriptions reused verbatim from y_finance.get_stock_stats_indicators_window
# so the VN path produces the same agent-facing guidance text.
_IND_DESCRIPTIONS = {
    "close_50_sma": "50 SMA: A medium-term trend indicator for trend direction and dynamic support/resistance.",
    "close_200_sma": "200 SMA: A long-term trend benchmark; confirms overall trend and golden/death crosses.",
    "close_10_ema": "10 EMA: A responsive short-term average for quick momentum shifts.",
    "macd": "MACD: Momentum via EMA differences; watch crossovers and divergence.",
    "macds": "MACD Signal: EMA smoothing of MACD; crossovers trigger trades.",
    "macdh": "MACD Histogram: Gap between MACD and its signal; shows momentum strength.",
    "rsi": "RSI: Momentum, 70/30 overbought/oversold thresholds and divergence.",
    "boll": "Bollinger Middle: 20 SMA basis for Bollinger Bands.",
    "boll_ub": "Bollinger Upper Band: ~2 std above middle; overbought / breakout zones.",
    "boll_lb": "Bollinger Lower Band: ~2 std below middle; oversold conditions.",
    "atr": "ATR: Average true range for volatility-based stops and sizing.",
    "vwma": "VWMA: Volume-weighted moving average; confirms trend with volume.",
    "mfi": "MFI: Money Flow Index (price + volume), >80 overbought / <20 oversold.",
}

# HOSE and other VN exchange suffixes we strip before querying the source.
_VN_SUFFIXES = (".HM", ".HN", ".UP", ".VN")


def _normalize_symbol(symbol: str) -> str:
    """Strip any VN exchange suffix and upper-case the raw ticker.

    Agents may pass ``VNM``, ``VNM.HM`` (HOSE), ``VNINDEX`` etc. vnstock
    wants the bare code (``VNM``); index codes like ``VNINDEX`` are passed
    through unchanged.
    """
    s = symbol.strip().upper()
    for suffix in _VN_SUFFIXES:
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break
    # Validate it is safe to interpolate into a cache path downstream.
    return safe_ticker_component(s)


def _vnstock_history(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch raw OHLCV from vnstock and return it with repo-standard columns.

    Returns a DataFrame with ``Date, Open, High, Low, Close, Volume`` (the
    schema ``stockstats``/``_clean_dataframe`` expect), or raises.
    """
    # Imported lazily so the dependency is only required when the VN vendor
    # is actually selected.
    from vnstock import Quote  # type: ignore

    norm = _normalize_symbol(symbol)

    # Swallow vnstock's promotional banner / notices printed to stdout so
    # they never contaminate the returned string.
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            raw = Quote(symbol=norm).history(
                start=start_date, end=end_date, interval="1D"
            )
    except Exception as e:  # network / rate-limit / unknown symbol
        msg = str(e).lower()
        if "rate" in msg and "limit" in msg:
            raise VnRateLimitError(str(e)) from e
        raise

    if raw is None or len(raw) == 0:
        return pd.DataFrame()

    df = raw.rename(
        columns={
            "time": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    return df


def load_ohlcv_vn(symbol: str, curr_date: str) -> pd.DataFrame:
    """OHLCV loader for the indicator path, cleaned for stockstats.

    Fetches ~15y up to ``curr_date`` and filters out future rows to avoid
    look-ahead bias, mirroring ``stockstats_utils.load_ohlcv``.
    """
    curr_dt = pd.to_datetime(curr_date)
    start = (curr_dt - pd.DateOffset(years=15)).strftime("%Y-%m-%d")
    end = curr_dt.strftime("%Y-%m-%d")

    df = _vnstock_history(symbol, start, end)
    if df.empty:
        return df

    df = _clean_dataframe(df)
    # vnstock's ``time`` carries a time-of-day (07:00:00); normalize to the
    # calendar date so a curr_date at midnight does not filter out the same
    # day's (later-timestamped) trading row.
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    df = df[df["Date"] <= curr_dt.normalize()]
    return df


def get_stock(
    symbol: Annotated[str, "ticker symbol (HOSE), e.g. VNM or VNM.HM"],
    start_date: Annotated[str, "Start date yyyy-mm-dd"],
    end_date: Annotated[str, "End date yyyy-mm-dd"],
) -> str:
    """Return daily OHLCV as a CSV string with a ``#`` header block.

    Matches the return shape of ``y_finance.get_YFin_data_online`` /
    ``alpha_vantage_stock.get_stock``.
    """
    # Validate date formats up front (same contract as other vendors).
    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    try:
        df = _vnstock_history(symbol, start_date, end_date)
    except VnRateLimitError:
        raise
    except Exception as e:
        return f"Error retrieving VN stock data for {symbol}: {e}"

    if df.empty:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

    # Normalize Date to plain date string and round prices for display.
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"]).dt.strftime("%Y-%m-%d")
    for col in ("Open", "High", "Low", "Close"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(2)

    csv_string = out.to_csv(index=False)
    header = f"# Stock data for {_normalize_symbol(symbol)} (HOSE) from {start_date} to {end_date}\n"
    header += f"# Total records: {len(out)}\n"
    header += f"# Source: vnstock; Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + csv_string


def get_indicator(
    symbol: Annotated[str, "ticker symbol (HOSE)"],
    indicator: Annotated[str, "technical indicator key"],
    curr_date: Annotated[str, "current trading date, yyyy-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    """Compute a stockstats indicator over a lookback window from VN OHLCV.

    Reuses ``stockstats`` exactly like the yfinance path; only the data
    source differs.
    """
    from dateutil.relativedelta import relativedelta
    from stockstats import wrap

    if indicator not in _IND_DESCRIPTIONS:
        raise ValueError(
            f"Indicator {indicator} is not supported. Choose from: {list(_IND_DESCRIPTIONS.keys())}"
        )

    try:
        data = load_ohlcv_vn(symbol, curr_date)
    except VnRateLimitError:
        raise
    except Exception as e:
        return f"Error retrieving VN indicator data for {symbol}: {e}"

    if data.empty:
        return f"No data found for symbol '{symbol}' up to {curr_date}"

    df = wrap(data)
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    df[indicator]  # trigger stockstats to compute the column

    ind_map = {row["Date"]: row[indicator] for _, row in df.iterrows()}

    end_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    before = end_dt - relativedelta(days=look_back_days)

    lines = []
    cur = end_dt
    while cur >= before:
        ds = cur.strftime("%Y-%m-%d")
        val = ind_map.get(ds)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            lines.append(f"{ds}: N/A: Not a trading day (weekend or holiday)")
        else:
            lines.append(f"{ds}: {val}")
        cur = cur - relativedelta(days=1)

    return (
        f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {curr_date}:\n\n"
        + "\n".join(lines)
        + "\n\n"
        + _IND_DESCRIPTIONS.get(indicator, "No description available.")
    )
