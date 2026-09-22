"""Vietnam fundamentals vendor (HOSE) backed by vnstock.

Implements the four fundamental-data methods the vendor-routing layer
expects, matching the signatures / string-return contract of the yfinance
and alpha_vantage vendors:

* ``get_fundamentals(ticker, curr_date=None)``      -> company overview text
* ``get_balance_sheet(ticker, freq, curr_date)``    -> CSV with ``#`` header
* ``get_cashflow(ticker, freq, curr_date)``         -> CSV with ``#`` header
* ``get_income_statement(ticker, freq, curr_date)`` -> CSV with ``#`` header

Schema verified live against vnstock 4.0.8 (see
``docs/vnstock_schema_xac_minh.md``):

* ``Finance(source, symbol, period).{balance_sheet,cash_flow,income_statement}()``
  return a LONG DataFrame: ``item`` (Vietnamese label), ``item_en`` (English
  label), ``item_id`` (machine key), then one float column per fiscal period
  named ``YYYY-QN`` (quarterly) or ``YYYY`` (annual). Values are in absolute
  VND under Vietnamese Accounting Standards (VAS). The community edition caps
  results at 4 periods.
* ``Company(symbol).overview()`` returns a single-row wide DataFrame with
  fields such as ``exchange`` (e.g. ``HOSE``), ``founded_date``,
  ``charter_capital``, ``outstanding_shares``, ``free_float_percentage``,
  ``ceo_name``, ``website``.

The ``item_en`` column means agents get English labels for free — no
Vietnamese-label mapping is needed. Prices/values are left in native VND.
"""

from __future__ import annotations

import io
import os
import contextlib
from datetime import datetime
from typing import Annotated

import pandas as pd

from .utils import safe_ticker_component

os.environ.setdefault("VNSTOCK_TELEMETRY", "off")

# Default source for fundamentals. VCI (Vietcap) returns the full VAS
# statement structure with English labels in testing.
_FUND_SOURCE = "VCI"

_VN_SUFFIXES = (".HM", ".HN", ".UP", ".VN")


def _normalize_symbol(symbol: str) -> str:
    """Strip a VN exchange suffix and upper-case; validate as path-safe."""
    s = symbol.strip().upper()
    for suffix in _VN_SUFFIXES:
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break
    return safe_ticker_component(s)


def _period(freq: str | None) -> str:
    """Map the repo's ``freq`` ('quarterly'/'annual') to vnstock ``period``."""
    if freq and freq.lower().startswith("year") or (freq and freq.lower() == "annual"):
        return "year"
    return "quarter"


def _quiet(fn):
    """Run ``fn`` swallowing vnstock's promotional stdout banner/notices."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn()


def _statement_csv(kind: str, ticker: str, freq: str, curr_date: str | None) -> str:
    """Fetch one financial statement and render it as a ``#``-header CSV.

    ``kind`` is the Finance method name: balance_sheet / cash_flow /
    income_statement. Periods (columns) after ``curr_date`` are dropped to
    avoid look-ahead bias, mirroring ``filter_financials_by_date``.
    """
    from vnstock import Finance  # lazy import

    norm = _normalize_symbol(ticker)
    period = _period(freq)

    try:
        fin = Finance(source=_FUND_SOURCE, symbol=norm, period=period)
        df = _quiet(lambda: getattr(fin, kind)())
    except Exception as e:
        return f"Error retrieving {kind} for {ticker}: {e}"

    if df is None or len(df) == 0:
        return f"No {kind} data found for symbol '{ticker}'"

    # Period columns are everything except the three label columns.
    label_cols = [c for c in ("item", "item_en", "item_id") if c in df.columns]
    period_cols = [c for c in df.columns if c not in label_cols]

    # Drop future periods relative to curr_date (look-ahead guard). Period
    # labels look like 'YYYY-QN' or 'YYYY'; compare on the year (and quarter
    # end) parsed loosely — anything unparseable is kept.
    if curr_date:
        cutoff = pd.Timestamp(curr_date)
        keep = []
        for c in period_cols:
            end = _period_end(str(c))
            if end is None or end <= cutoff:
                keep.append(c)
        period_cols = keep

    out = df[label_cols + period_cols]
    csv_string = out.to_csv(index=False)
    header = f"# {kind.replace('_', ' ').title()} for {norm} (HOSE, {period}, VND/VAS)\n"
    header += f"# Source: vnstock; Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + csv_string


def _period_end(label: str) -> pd.Timestamp | None:
    """Best-effort fiscal-period-end timestamp from a 'YYYY-QN' / 'YYYY' label."""
    label = label.strip()
    try:
        if "-Q" in label:
            year, q = label.split("-Q")
            month = int(q) * 3
            return pd.Timestamp(int(year), month, 1) + pd.offsets.MonthEnd(0)
        if label.isdigit() and len(label) == 4:
            return pd.Timestamp(int(label), 12, 31)
    except Exception:
        return None
    return None


def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol (HOSE)"],
    freq: Annotated[str, "'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date YYYY-MM-DD"] = None,
) -> str:
    return _statement_csv("balance_sheet", ticker, freq, curr_date)


def get_cashflow(
    ticker: Annotated[str, "ticker symbol (HOSE)"],
    freq: Annotated[str, "'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date YYYY-MM-DD"] = None,
) -> str:
    return _statement_csv("cash_flow", ticker, freq, curr_date)


def get_income_statement(
    ticker: Annotated[str, "ticker symbol (HOSE)"],
    freq: Annotated[str, "'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date YYYY-MM-DD"] = None,
) -> str:
    return _statement_csv("income_statement", ticker, freq, curr_date)


def get_fundamentals(
    ticker: Annotated[str, "ticker symbol (HOSE)"],
    curr_date: Annotated[str, "current date (unused)"] = None,
) -> str:
    """Return a company overview as readable text (name, exchange, capital, etc.)."""
    from vnstock import Company  # lazy import

    norm = _normalize_symbol(ticker)
    try:
        df = _quiet(lambda: Company(symbol=norm).overview())
    except Exception as e:
        return f"Error retrieving fundamentals for {ticker}: {e}"

    if df is None or len(df) == 0:
        return f"No fundamentals data found for symbol '{ticker}'"

    row = df.iloc[0].to_dict()

    # A curated, agent-friendly subset (skip the very long free-text blobs).
    # NOTE: vnstock's overview mislabels some numeric fields (charter_capital,
    # free_float_percentage, free_float, par_value are cross-wired in 4.0.8),
    # so we only surface fields verified to carry correct values, plus
    # outstanding_shares which is reliable. Capital/free-float are omitted
    # rather than shown wrong.
    fields = [
        ("Symbol", "symbol"),
        ("Exchange", "exchange"),
        ("Company Type", "company_type"),
        ("Founded", "founded_date"),
        ("Listing Date", "listing_date"),
        ("Outstanding Shares", "outstanding_shares"),
        ("Employees", "number_of_employees"),
        ("CEO", "ceo_name"),
        ("Auditor", "auditor"),
        ("Website", "website"),
        ("As Of", "as_of_date"),
    ]
    lines = []
    for label, key in fields:
        val = row.get(key)
        if val is not None and str(val).strip() and str(val) != "nan":
            lines.append(f"{label}: {val}")

    header = f"# Company Fundamentals for {norm} (HOSE)\n"
    header += f"# Source: vnstock; Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + "\n".join(lines)
