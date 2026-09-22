"""Vietnam news vendor (HOSE) backed by vnstock.

Implements the two news methods the vendor-routing layer expects:

* ``get_news(ticker, curr_date, look_back_days=7, ...)`` -> ticker news text
* ``get_global_news(curr_date, ...)``                    -> macro news text

Schema verified live against vnstock 4.0.8:

* ``Company(symbol=...).news()`` returns a DataFrame with columns
  ``head, article_id, title, publish_time, url`` (``publish_time`` is an
  ISO timestamp string). This is company-specific disclosure/news.

vnstock exposes no reliable Vietnam *macro* news feed, so
:func:`get_global_news` returns a clear notice rather than fabricating
headlines; the routing layer's fallback chain then lets another vendor
serve macro news if configured.
"""

from __future__ import annotations

import io
import os
import contextlib
from datetime import datetime, timedelta
from typing import Annotated

import pandas as pd

from .utils import safe_ticker_component

os.environ.setdefault("VNSTOCK_TELEMETRY", "off")

_VN_SUFFIXES = (".HM", ".HN", ".UP", ".VN")


def _normalize_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    for suffix in _VN_SUFFIXES:
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break
    return safe_ticker_component(s)


def _quiet(fn):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn()


def get_news(
    ticker: Annotated[str, "ticker symbol (HOSE)"],
    curr_date: Annotated[str, "current date YYYY-MM-DD"] = None,
    look_back_days: Annotated[int, "lookback window in days"] = 7,
    max_articles: Annotated[int, "max articles to return"] = 20,
) -> str:
    """Return recent company news/disclosure as readable text.

    Filters to ``[curr_date - look_back_days, curr_date]`` when ``curr_date``
    is given, newest first, capped at ``max_articles``.
    """
    from vnstock import Company  # lazy import

    norm = _normalize_symbol(ticker)
    try:
        df = _quiet(lambda: Company(symbol=norm).news())
    except Exception as e:
        return f"Error retrieving VN news for {ticker}: {e}"

    if df is None or len(df) == 0 or "title" not in getattr(df, "columns", []):
        return f"No news found for symbol '{ticker}'"

    df = df.copy()
    if "publish_time" in df.columns:
        df["_ts"] = pd.to_datetime(df["publish_time"], errors="coerce")
        if curr_date:
            end = pd.Timestamp(curr_date) + pd.Timedelta(days=1)
            start = pd.Timestamp(curr_date) - pd.Timedelta(days=look_back_days)
            df = df[(df["_ts"] >= start) & (df["_ts"] < end)]
        df = df.sort_values("_ts", ascending=False)

    df = df.head(max_articles)
    if df.empty:
        return f"No news for '{ticker}' in the {look_back_days}-day window ending {curr_date}"

    lines = []
    for _, r in df.iterrows():
        ts = r.get("publish_time", "")
        title = str(r.get("title", "")).strip()
        url = str(r.get("url", "")).strip()
        lines.append(f"- [{ts}] {title}" + (f"  ({url})" if url else ""))

    header = f"# Company news for {norm} (HOSE)"
    if curr_date:
        header += f", up to {curr_date} (last {look_back_days} days)"
    header += f"\n# Source: vnstock; Retrieved {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + "\n".join(lines)


def get_global_news(
    curr_date: Annotated[str, "current date YYYY-MM-DD"] = None,
    *args,
    **kwargs,
) -> str:
    """VN macro news is not available via vnstock.

    Returns a clear notice instead of fabricating headlines. The vendor
    routing layer will fall through to another configured vendor for macro
    news if one is available; otherwise configure ``global_news_queries``
    (already localized to VN macro topics) with a web-search-backed vendor.
    """
    return (
        "# Vietnam macro news unavailable via the vnstock vendor.\n"
        "vnstock provides company-specific news only, not a macro feed. "
        "Configure a web-search-backed vendor for get_global_news, or rely on "
        "the localized global_news_queries (SBV rates, VN-Index, FDI, USD/VND) "
        "with another news vendor."
    )
