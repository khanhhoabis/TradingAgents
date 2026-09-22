from langchain_core.messages import HumanMessage, RemoveMessage

# Import tools from separate utility files
from tradingagents.agents.utils.core_stock_tools import (
    get_stock_data
)
from tradingagents.agents.utils.technical_indicators_tools import (
    get_indicators
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement
)
from tradingagents.agents.utils.news_data_tools import (
    get_news,
    get_insider_transactions,
    get_global_news
)


def get_language_instruction() -> str:
    """Return a prompt instruction for the configured output language.

    Returns empty string when English (default), so no extra tokens are used.
    Applied to every agent whose output reaches the saved report —
    analysts, researchers, debaters, research manager, trader, and
    portfolio manager — so a non-English run produces a fully localized
    report rather than a mix of languages.
    """
    from tradingagents.dataflows.config import get_config
    lang = get_config().get("output_language", "English")
    if lang.strip().lower() == "english":
        return ""
    return f" Write your entire response in {lang}."


def build_instrument_context(ticker: str) -> str:
    """Describe the exact instrument so agents preserve exchange-qualified tickers.

    For HOSE-listed tickers (``.HM`` suffix) the description is extended with
    the HOSE market-microstructure rules the trader and risk agents must
    respect (price band, settlement, board lot, session structure, foreign
    room, VND/VAS units).
    """
    base = (
        f"The instrument to analyze is `{ticker}`. "
        "Use this exact ticker in every tool call, report, and recommendation, "
        "preserving any exchange suffix (e.g. `.TO`, `.L`, `.HK`, `.T`, `.HM`)."
    )
    if _is_hose(ticker):
        return base + " " + HOSE_MICROSTRUCTURE_RULES
    return base


def _is_hose(ticker: str) -> bool:
    """True when ``ticker`` is a HOSE-listed symbol (``.HM`` suffix)."""
    return bool(ticker) and ticker.strip().upper().endswith(".HM")


# HOSE (Ho Chi Minh Stock Exchange) microstructure rules injected into the
# trader/risk prompt. Static domain knowledge — no data source needed.
HOSE_MICROSTRUCTURE_RULES = (
    "This is a HOSE (Ho Chi Minh Stock Exchange, Vietnam) listing, so apply "
    "these market rules when sizing trades and setting entries, stops and "
    "targets: (1) Daily price band is ±7% around the previous session's "
    "reference (ATC close); intraday targets/stops cannot exceed the ceiling/"
    "floor (newly listed first session is ±20%). (2) Settlement is T+2 — shares "
    "arrive on T+2 and can only be sold from then, so same-day round trips are "
    "not possible; any holding plan must span at least T+2. (3) Board lot is 100 "
    "shares for continuous matching; size positions in multiples of 100 (odd "
    "lots trade separately with poor liquidity). (4) Sessions: ATO opening "
    "auction (09:00-09:15), continuous matching (09:15-11:30, 13:00-14:30), ATC "
    "closing auction (14:30-14:45); ATO/ATC orders are priceless and risk "
    "slippage. (5) Tick size: <10,000 VND -> 10 VND; 10,000-49,950 -> 50 VND; "
    ">=50,000 -> 100 VND — entries/exits must land on a valid tick. (6) Foreign "
    "ownership room is capped (commonly 49%, banks 30%); a stock near its "
    "foreign-room limit is a meaningful supply/demand signal. (7) Prices are in "
    "VND and financial statements follow Vietnamese Accounting Standards (VAS)."
)

def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]

        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]

        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")

        return {"messages": removal_operations + [placeholder]}

    return delete_messages


        
