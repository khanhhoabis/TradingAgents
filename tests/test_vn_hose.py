"""Tests for the Vietnam / HOSE customizations.

These are offline: they assert the static wiring (microstructure-rule
injection, VN-Index benchmark, vendor registration, symbol normalization)
without hitting the network, so they run in CI without vnstock connectivity.
"""

import pytest

from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    _is_hose,
    HOSE_MICROSTRUCTURE_RULES,
)
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows import interface
from tradingagents.dataflows import vn_market, vn_fundamentals, vn_news


class TestHoseDetection:
    @pytest.mark.parametrize("ticker,expected", [
        ("VNM.HM", True),
        ("vnm.hm", True),
        ("FPT.HM", True),
        ("AAPL", False),
        ("VNM", False),
        ("AAPL.TO", False),
        ("", False),
    ])
    def test_is_hose(self, ticker, expected):
        assert _is_hose(ticker) is expected


class TestInstrumentContext:
    def test_hose_ticker_gets_microstructure_rules(self):
        ctx = build_instrument_context("VNM.HM")
        assert "VNM.HM" in ctx
        assert HOSE_MICROSTRUCTURE_RULES in ctx
        # Key rules present
        assert "±7%" in ctx
        assert "T+2" in ctx
        assert "100 shares" in ctx

    def test_non_hose_ticker_has_no_hose_rules(self):
        ctx = build_instrument_context("AAPL")
        assert "AAPL" in ctx
        assert HOSE_MICROSTRUCTURE_RULES not in ctx
        assert "T+2" not in ctx


class TestBenchmarkMap:
    def test_hose_maps_to_vnindex(self):
        assert DEFAULT_CONFIG["benchmark_map"].get(".HM") == "VNINDEX"

    def test_us_default_preserved(self):
        assert DEFAULT_CONFIG["benchmark_map"].get("") == "SPY"


class TestVendorRegistration:
    def test_vn_in_vendor_list(self):
        assert "vn" in interface.VENDOR_LIST

    @pytest.mark.parametrize("method", [
        "get_stock_data", "get_indicators", "get_fundamentals",
        "get_balance_sheet", "get_cashflow", "get_income_statement",
        "get_news", "get_global_news",
    ])
    def test_vn_registered_for_method(self, method):
        assert "vn" in interface.VENDOR_METHODS[method]
        assert callable(interface.VENDOR_METHODS[method]["vn"])


class TestSymbolNormalization:
    @pytest.mark.parametrize("raw,norm", [
        ("VNM.HM", "VNM"),
        ("vnm", "VNM"),
        ("VNINDEX", "VNINDEX"),
        ("HPG.VN", "HPG"),
    ])
    def test_market_normalize(self, raw, norm):
        assert vn_market._normalize_symbol(raw) == norm

    def test_fundamentals_and_news_share_normalization(self):
        assert vn_fundamentals._normalize_symbol("FPT.HM") == "FPT"
        assert vn_news._normalize_symbol("FPT.HM") == "FPT"


class TestPeriodMapping:
    @pytest.mark.parametrize("freq,period", [
        ("quarterly", "quarter"),
        ("annual", "year"),
        ("yearly", "year"),
        (None, "quarter"),
    ])
    def test_period(self, freq, period):
        assert vn_fundamentals._period(freq) == period


class TestSentimentHoseAware:
    def test_hose_note_present_for_hm(self):
        from tradingagents.agents.analysts.sentiment_analyst import _build_system_message
        msg = _build_system_message(
            ticker="VNM.HM", start_date="2024-01-01", end_date="2024-01-08",
            news_block="n", stocktwits_block="s", reddit_block="r", is_hose=True,
        )
        assert "HOSE (Vietnam) ticker" in msg
        assert "Do NOT infer sentiment from them" in msg

    def test_no_hose_note_for_us(self):
        from tradingagents.agents.analysts.sentiment_analyst import _build_system_message
        msg = _build_system_message(
            ticker="AAPL", start_date="2024-01-01", end_date="2024-01-08",
            news_block="n", stocktwits_block="s", reddit_block="r", is_hose=False,
        )
        assert "HOSE (Vietnam) ticker" not in msg
