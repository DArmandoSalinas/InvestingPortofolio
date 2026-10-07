import pandas as pd

from app.market_data import closes_from_frame
from app.universe import (
    apply_ipc_adjustments,
    compact_bmv,
    gics_code,
    listing_from_bmv,
    parse_ipc_html,
    parse_sp500_html,
)


IPC_PAGE = """
<h2 id="Components">Components</h2>
<table>
<tr><td>Becle</td><td>CUERVO</td><td>Consumer Staples</td></tr>
<tr><td>Televisa</td><td>TLEVISA CPO</td><td>Consumer Discretionary</td></tr>
<tr><td>Walmart de México</td><td>WALMEX</td><td>Consumer Staples</td></tr>
<tr><td>Banorte</td><td>GFNORTE O</td><td>Financial</td></tr>
<tr><td>Volaris</td><td>VOLAR A</td><td>Industrials</td></tr>
</table>
<h2 id="Annual_Returns">Annual Returns</h2>
<table><tr><td>2020</td><td>1%</td><td>ignore</td></tr></table>
"""

SP_PAGE = """
<table>
<tr><th>Symbol</th><th>Security</th><th>GICS Sector</th></tr>
<tr><td>AAPL</td><td>Apple</td><td>Information Technology</td></tr>
<tr><td>BRK.B</td><td>Berkshire Hathaway</td><td>Financials</td></tr>
</table>
"""


def test_bmv_symbols_drop_spaces_and_map_sectors():
    assert compact_bmv("LIVEPOL C-1") == "LIVEPOLC-1"
    listing = listing_from_bmv("Banorte", "GFNORTE O", "Financial")
    assert listing.symbol == "GFNORTEO"
    assert listing.yahoo_symbol == "GFNORTEO.MX"
    assert listing.sector == "financials"
    assert gics_code("Telecommunication Services") == "communication_services"
    assert gics_code("Technology") == "information_technology"


def test_ipc_adjustments_drop_2026_names_and_add_alpek_once():
    listings = apply_ipc_adjustments(parse_ipc_html(IPC_PAGE))
    symbols = [item.symbol for item in listings]
    assert "CUERVO" not in symbols
    assert "TLEVISACPO" not in symbols
    assert symbols.count("ALPEKA") == 1
    assert "WALMEX" in symbols
    assert "VOLARA" in symbols
    again = apply_ipc_adjustments(listings)
    assert [item.symbol for item in again].count("ALPEKA") == 1


def test_daily_bars_keep_open_high_low_close_together():
    from app.market_data import bars_from_frame

    index = pd.to_datetime(["2026-10-01", "2026-10-02"])
    frame = pd.DataFrame(
        {
            ("SMCI", "Open"): [10.0, 11.0],
            ("SMCI", "High"): [12.0, 13.0],
            ("SMCI", "Low"): [9.0, 10.5],
            ("SMCI", "Close"): [11.0, 12.5],
        },
        index=index,
    )
    frame.columns = pd.MultiIndex.from_tuples(frame.columns, names=["Ticker", "Price"])
    bars = bars_from_frame(frame, "SMCI")
    assert bars[0]["time"] == "2026-10-01"
    assert bars[1]["close"] == 12.5
    assert bars[1]["low"] == 10.5


def test_adjusted_closes_come_out_of_a_grouped_download():
    frame = pd.DataFrame(
        {("MMM", "Close"): [10.0, 12.0], ("AOS", "Close"): [None, 4.0]}
    )
    frame.columns = pd.MultiIndex.from_tuples(frame.columns, names=["Ticker", "Price"])
    assert closes_from_frame(frame, "MMM") == [10.0, 12.0]
    assert closes_from_frame(frame, "AOS") == [4.0]


def test_sp500_parser_keeps_the_share_class_dot_out_of_yahoo():
    listings = parse_sp500_html(SP_PAGE)
    by_symbol = {item.symbol: item for item in listings}
    assert by_symbol["AAPL"].yahoo_symbol == "AAPL"
    assert by_symbol["AAPL"].sector == "information_technology"
    assert by_symbol["BRK.B"].yahoo_symbol == "BRK-B"
    assert by_symbol["BRK.B"].market == "us"
