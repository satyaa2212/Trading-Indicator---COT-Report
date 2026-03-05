"""
config.py — Configuration for the COT Report fetcher.

Contains:
  • CFTC data source URLs
  • Market / contract code mappings (Legacy and Disaggregated reports)
  • Column name constants for both report formats
  • Chart styling constants
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CFTC DATA URLS
# ─────────────────────────────────────────────────────────────────────────────

CFTC_URLS = {
    # Current-year Disaggregated Futures-Only (updated weekly)
    "disaggregated_current": "https://www.cftc.gov/dea/newcot/fut_disagg_xls.zip",
    # Historical Disaggregated Futures-Only (2006–2016 bulk ZIP; data from 2017
    # onward must be fetched year-by-year or via the current-year file)
    "disaggregated_history": "https://www.cftc.gov/dea/newcot/fut_disagg_xls_hist_2006_2016.zip",
    # Year-by-year historical disaggregated ZIPs (2017+); append year to use.
    # e.g. "https://www.cftc.gov/dea/newcot/f_year/fut_disagg_txt_{YEAR}.zip"
    "disaggregated_history_url_template": "https://www.cftc.gov/dea/newcot/f_year/fut_disagg_txt_{year}.zip",
    # Current-year Legacy Futures-Only
    "legacy_current": "https://www.cftc.gov/dea/newcot/deacom.zip",
    # Historical Legacy (ZIP containing CSV for all years)
    "legacy_history": "https://www.cftc.gov/dea/newcot/deahistfo.zip",
    # CFTC historical index page (for reference)
    "history_index": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm",
    # Alternative disaggregated current (txt, no zip)
    "disaggregated_current_txt": "https://www.cftc.gov/dea/newcot/fut_disagg_txt.zip",
    # Alternative legacy txt
    "legacy_current_txt": "https://www.cftc.gov/dea/newcot/deacom.txt",
}

# ─────────────────────────────────────────────────────────────────────────────
#  MARKET / CONTRACT CODE MAPPINGS
#
#  Each entry:
#    key        : human-readable name shown in CLI / charts
#    "code"     : CFTC "Market and Exchange Names" identifier used in
#                 the data files (partial match is supported)
#    "category" : asset class for grouping
# ─────────────────────────────────────────────────────────────────────────────

MARKETS = {
    # ── Forex ────────────────────────────────────────────────────────────────
    "EUR/USD": {
        "code": "EURO FX",
        "category": "Forex",
        "cftc_code": "099741",
    },
    "GBP/USD": {
        "code": "BRITISH POUND STERLING",
        "category": "Forex",
        "cftc_code": "096742",
    },
    "JPY/USD": {
        "code": "JAPANESE YEN",
        "category": "Forex",
        "cftc_code": "097741",
    },
    "AUD/USD": {
        "code": "AUSTRALIAN DOLLAR",
        "category": "Forex",
        "cftc_code": "232741",
    },
    "CAD/USD": {
        "code": "CANADIAN DOLLAR",
        "category": "Forex",
        "cftc_code": "090741",
    },
    "CHF/USD": {
        "code": "SWISS FRANC",
        "category": "Forex",
        "cftc_code": "092741",
    },
    "NZD/USD": {
        "code": "NEW ZEALAND DOLLAR",
        "category": "Forex",
        "cftc_code": "112741",
    },
    # ── Metals ───────────────────────────────────────────────────────────────
    "Gold": {
        "code": "GOLD",
        "category": "Metals",
        "cftc_code": "088691",
    },
    "Silver": {
        "code": "SILVER",
        "category": "Metals",
        "cftc_code": "084691",
    },
    "Copper": {
        "code": "COPPER",
        "category": "Metals",
        "cftc_code": "085692",
    },
    # ── Energy ───────────────────────────────────────────────────────────────
    "Crude Oil WTI": {
        "code": "CRUDE OIL, LIGHT SWEET",
        "category": "Energy",
        "cftc_code": "067651",
    },
    "Natural Gas": {
        "code": "NATURAL GAS",
        "category": "Energy",
        "cftc_code": "023651",
    },
    # ── Grains ───────────────────────────────────────────────────────────────
    "Corn": {
        "code": "CORN",
        "category": "Grains",
        "cftc_code": "002602",
    },
    "Wheat": {
        "code": "WHEAT",
        "category": "Grains",
        "cftc_code": "001602",
    },
    "Soybeans": {
        "code": "SOYBEANS",
        "category": "Grains",
        "cftc_code": "005602",
    },
    # ── Indices ──────────────────────────────────────────────────────────────
    "S&P 500 E-mini": {
        "code": "E-MINI S&P 500",
        "category": "Indices",
        "cftc_code": "13874A",
    },
    "Nasdaq 100 E-mini": {
        "code": "NASDAQ-100 MINI",
        "category": "Indices",
        "cftc_code": "209742",
    },
    "Dow Jones E-mini": {
        "code": "DJIA X $5",
        "category": "Indices",
        "cftc_code": "12460P",
    },
    # ── Rates ────────────────────────────────────────────────────────────────
    "10-Year T-Note": {
        "code": "10-YEAR U.S. TREASURY NOTES",
        "category": "Rates",
        "cftc_code": "043602",
    },
    "30-Year T-Bond": {
        "code": "U.S. TREASURY BONDS",
        "category": "Rates",
        "cftc_code": "020601",
    },
}

# Convenience list of all market names
MARKET_NAMES = list(MARKETS.keys())

# ─────────────────────────────────────────────────────────────────────────────
#  COLUMN NAMES — DISAGGREGATED REPORT
#  (Source: CFTC fut_disagg_txt.zip / fut_disagg_xls.zip)
# ─────────────────────────────────────────────────────────────────────────────

DISAGG_COLS = {
    "market_name": "Market and Exchange Names",
    "date":        "As of Date in Form YYYY-MM-DD",
    "cftc_code":   "CFTC Commodity Code",
    "open_interest": "Open Interest (All)",
    # Managed Money (Fund Managers)
    "mm_long":     "M Money Positions-Long (All)",
    "mm_short":    "M Money Positions-Short (All)",
    "mm_spread":   "M Money Positions-Spreading (All)",
    # Producer / Merchant / Processor / User (Commercials)
    "pm_long":     "Prod Merc Positions-Long (All)",
    "pm_short":    "Prod Merc Positions-Short (All)",
    # Swap Dealers
    "swap_long":   "Swap Positions-Long (All)",
    "swap_short":  "Swap Positions-Short (All)",
    "swap_spread": "Swap Positions-Spreading (All)",
    # Non-Reportable (Retail / Small Speculators)
    "nr_long":     "NonRept Positions-Long (All)",
    "nr_short":    "NonRept Positions-Short (All)",
    # Other Reportable
    "other_long":  "Other Rept Positions-Long (All)",
    "other_short": "Other Rept Positions-Short (All)",
}

# ─────────────────────────────────────────────────────────────────────────────
#  COLUMN NAMES — LEGACY REPORT
#  (Source: CFTC deacom.txt / deahistfo.txt)
# ─────────────────────────────────────────────────────────────────────────────

LEGACY_COLS = {
    "market_name":   "Market and Exchange Names",
    "date":          "As of Date in Form YYYY-MM-DD",
    "cftc_code":     "CFTC Commodity Code",
    "open_interest": "Open Interest (All)",
    # Non-Commercial (Large Speculators)
    "nc_long":       "NonComm Positions-Long (All)",
    "nc_short":      "NonComm Positions-Short (All)",
    "nc_spread":     "NonComm Positions-Spreading (All)",
    # Commercial (Hedgers)
    "com_long":      "Comm Positions-Long (All)",
    "com_short":     "Comm Positions-Short (All)",
    # Non-Reportable (Retail / Small Speculators)
    "nr_long":       "NonRept Positions-Long (All)",
    "nr_short":      "NonRept Positions-Short (All)",
}

# ─────────────────────────────────────────────────────────────────────────────
#  CHART / VISUAL SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

CHART_COLORS = {
    "retail":    "#FF2D55",   # Red
    "funds":     "#FF8C00",   # Orange
    "producers": "#2979FF",   # Blue
    "zero_line": "#808080",   # Gray
    "bg":        "#131722",   # Dark background (TradingView style)
    "grid":      "#2A2E39",   # Grid lines
    "text":      "#D9D9D9",   # Axis labels / text
}

CHART_PANEL_TITLES = {
    "retail":    "Campus COT – Retail Traders (Non-Reportable)",
    "funds":     "Campus COT – Fund Managers (Managed Money)",
    "producers": "Campus COT – Producers & Users (Commercials)",
}

# Default COT Index lookback in weeks
DEFAULT_LOOKBACK = 52

# Extreme level thresholds (percentile) for signals
EXTREME_HIGH = 90
EXTREME_LOW  = 10

# Output directory for saved charts
OUTPUT_DIR = "output"

# Requests timeout in seconds
REQUEST_TIMEOUT = 30
