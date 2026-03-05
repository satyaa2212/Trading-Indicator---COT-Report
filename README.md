# Campus COT Report — Trading Indicator

A **Commitments of Traders (COT) Report** indicator suite that visualises CFTC net positions across three trader categories in the same three-panel style shown on TradingView's Campus COT indicators.

---

## Overview

The CFTC publishes weekly COT reports showing how commercial hedgers, large speculators (fund managers), and small speculators (retail traders) are positioned across dozens of futures markets.  
This repository contains:

| File | Purpose |
|---|---|
| `COT_Report_Indicator.pine` | TradingView Pine Script v5 indicator |
| `python/cot_fetcher.py` | Python auto-fetch, analysis & interactive charting |
| `python/config.py` | Market codes, URLs, colour constants |
| `python/requirements.txt` | Python package dependencies |

---

## Three-Panel Layout

Each chart/indicator shows **three separate sub-panels** stacked vertically:

| Panel | Colour | Trader Category |
|---|---|---|
| Top | 🔴 Red | **Retail Traders** — Non-Reportable (small speculators) |
| Middle | 🟠 Orange | **Fund Managers** — Managed Money (large speculators) |
| Bottom | 🔵 Blue | **Producers & Users** — Commercials (hedgers) |

Each panel displays:
- Net position = **Long − Short contracts** over time
- A **zero reference line**
- Current value label / tooltip
- Optional **COT Index** (percentile ranking, 0–100)

---

## TradingView Pine Script (`COT_Report_Indicator.pine`)

### Features
- **Pine Script v5** — `indicator()` with `explicit_plot_display = true`
- Fetches data via TradingView's built-in `COT:` symbol feed (no external data source needed)
- Supports **21 markets**: Major FX pairs, Metals, Energy, Grains, Equity Indices, Rates
- Both **Disaggregated** (Fund Managers + Producers) and **Legacy** (Non-Commercial + Commercial) report formats
- **COT Index** calculation (rolling percentile over configurable 13–260 week lookback)
- **Extreme level highlighting** with dashed bands (default: 90% / 10%)
- **Signal markers** (▲▼) when COT Index crosses extreme thresholds
- **Alert conditions** for extreme readings
- **Data summary table** (top-right corner) showing net positions and COT Index for all three categories
- Per-panel visibility toggles, line width, and fill-area options

### Setup in TradingView

1. Open TradingView → Pine Script Editor (bottom panel)
2. Paste the entire contents of `COT_Report_Indicator.pine`
3. Click **Add to chart**
4. In **Settings → Inputs**, choose:
   - **Market** — e.g. `EUR/USD`, `Gold`, `S&P 500 E-mini`
   - **Report Type** — `Disaggregated` (recommended) or `Legacy`
   - **Show COT Index** — toggle between raw net positions and normalised index
5. The indicator will appear as three separate sub-panels below your price chart

> **Note:** TradingView COT data (`COT:` prefix symbols) requires a TradingView account. The data updates every Friday after the CFTC publishes the weekly report.

### Available Markets

| Category | Markets |
|---|---|
| Forex | EUR/USD, GBP/USD, JPY/USD, AUD/USD, CAD/USD, CHF/USD, NZD/USD |
| Metals | Gold, Silver, Copper |
| Energy | Crude Oil WTI, Natural Gas |
| Grains | Corn, Wheat, Soybeans |
| Indices | S&P 500 E-mini, Nasdaq 100 E-mini, Dow Jones E-mini |
| Rates | 10-Year T-Note, 30-Year T-Bond |

---

## Python Script (`python/cot_fetcher.py`)

Fetches COT data **directly from the CFTC website** — no TradingView account required.

### Installation

```bash
cd python
pip install -r requirements.txt
```

### Quick Start

```bash
# Plot EUR/USD (Disaggregated, 52-week COT Index) — opens in browser
python cot_fetcher.py --market "EUR/USD"

# Plot Gold with raw net positions (no index normalisation)
python cot_fetcher.py --market "Gold" --no-index

# Legacy report, 26-week lookback, save HTML
python cot_fetcher.py --market "S&P 500 E-mini" --report legacy --lookback 26 --save

# Save as HTML + PNG, limit date range
python cot_fetcher.py --market "Crude Oil WTI" --start 2018-01-01 --save --png

# List all available markets
python cot_fetcher.py --list-markets
```

### CLI Options

| Flag | Default | Description |
|---|---|---|
| `--market` / `-m` | `EUR/USD` | Market to analyse |
| `--report` / `-r` | `disaggregated` | `disaggregated` or `legacy` |
| `--no-index` | — | Plot raw net positions instead of COT Index |
| `--lookback` / `-l` | `52` | COT Index lookback in weeks |
| `--no-history` | — | Skip fetching bulk historical data (faster) |
| `--start YYYY-MM-DD` | — | Chart start date |
| `--end YYYY-MM-DD` | — | Chart end date |
| `--save` | — | Save chart as HTML in `output/` directory |
| `--png` | — | Also save as PNG (requires `kaleido`) |
| `--output-dir` | `output` | Directory for saved files |
| `--no-show` | — | Do not open browser |
| `--list-markets` | — | Print available markets and exit |

### Output

- **Interactive HTML** — hover tooltips, zoom, pan, download as PNG
- **Console summary** — net positions and COT Index for the latest week
- **PNG export** — static image (requires `kaleido`)

### Data Sources

| Report | URL |
|---|---|
| Disaggregated current | `https://www.cftc.gov/dea/newcot/fut_disagg_txt.zip` |
| Disaggregated history (2006–2016) | `https://www.cftc.gov/dea/newcot/fut_disagg_xls_hist_2006_2016.zip` |
| Disaggregated history (2017+) | `https://www.cftc.gov/dea/newcot/f_year/fut_disagg_txt_{year}.zip` (fetched year-by-year) |
| Legacy current | `https://www.cftc.gov/dea/newcot/deacom.zip` |
| Legacy history | `https://www.cftc.gov/dea/newcot/deahistfo.zip` |

> **Historical data note:** The CFTC provides a single bulk archive covering 2006–2016.
> Data from 2017 onward is fetched year-by-year automatically by the script.
> The current year's file is always fetched first so the latest weekly report is always included.

Data is updated every Friday following the market close and reflects positions as of the prior Tuesday.

---

## How to Interpret the COT Indicator

### Net Positions (Raw)
- **Positive** value → more longs than shorts (net bullish positioning)
- **Negative** value → more shorts than longs (net bearish positioning)
- Watch for **divergences** between Retail and Fund Managers — retail is often a contrary indicator

### COT Index (Percentile)
- **0%** = historically the most bearish positioning in the lookback window
- **100%** = historically the most bullish positioning in the lookback window
- **> 90%** (red dashed line) = extreme bullish zone → potential reversal risk
- **< 10%** (green dashed line) = extreme bearish zone → potential reversal opportunity

### Classic COT Trading Rules
1. **Commercials** (Producers & Users) are the "smart money" — they trade to hedge real business risk and are often right at major turning points
2. **Fund Managers** (Managed Money) tend to be trend-followers — extreme readings can signal crowded trades
3. **Retail** (Non-Reportable) are small speculators — extremes often coincide with market tops/bottoms

---

## Project Structure

```
Trading-Indicator---COT-Report/
├── README.md                     # This file
├── COT_Report_Indicator.pine     # TradingView Pine Script v5 indicator
└── python/
    ├── cot_fetcher.py            # Python auto-fetch + analysis + charting
    ├── requirements.txt          # Python dependencies
    └── config.py                 # Market codes, URLs, colour settings
```

---

## Requirements

### TradingView
- TradingView account (free or paid)
- Access to COT data symbols (available on most plan levels)

### Python
- Python 3.9+
- See `python/requirements.txt`:
  - `pandas >= 2.0`
  - `plotly >= 5.18`
  - `requests >= 2.31`
  - `kaleido >= 0.2` *(optional, for PNG export)*

---

## License

This project is provided for educational purposes. COT data is published by the U.S. Commodity Futures Trading Commission (CFTC) and is in the public domain.