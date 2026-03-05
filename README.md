# COT Report Indicator for TradingView

A **Pine Script v6** indicator that displays **Commitment of Traders (COT) report data** for Forex, Commodities, and Indices markets directly inside TradingView. It visualises raw positioning data (no buy/sell signals) sourced from the CFTC via TradingView's built-in CFTC data feeds.

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Settings Explained](#settings-explained)
4. [How to Interpret COT Data](#how-to-interpret-cot-data)
5. [Supported Markets](#supported-markets)
6. [Screenshots](#screenshots)
7. [Technical Details](#technical-details)
8. [License](#license)

---

## Features

- 📊 **19 markets** across Forex, Commodities, and Indices
- 📈 **Net Positions** view – Commercials, Large Specs, and Small Specs net longs vs shorts
- 🔢 **COT Index** view – normalized 0–100 score over a configurable lookback period
- 📉 **Open Interest** optional overlay
- 🎨 **Full colour customisation** per trader category
- 🔍 **Info table** showing current values for the selected market
- ⚡ Works on **all chart timeframes** (weekly COT data is forward-filled automatically)
- 🪟 Renders in a **separate pane** – does not overlap the price chart

---

## Installation

1. Open **TradingView** and navigate to any chart.
2. Click the **Pine Script Editor** tab at the bottom of the screen (or press `Alt + E`).
3. Delete any existing code in the editor.
4. Open [`COT_Report_Indicator.pine`](./COT_Report_Indicator.pine) from this repository and **copy its entire contents**.
5. Paste the copied code into the Pine Script Editor.
6. Click **"Add to chart"** (the rocket icon or `Ctrl + Enter`).
7. The indicator will appear as a new panel below your price chart.

> **Tip:** Save the script to your Personal Library via *File → Save As…* so you can reuse it across charts.

---

## Settings Explained

### Market Selection

| Setting | Description |
|---|---|
| **Market** | Dropdown to choose the futures contract whose COT data is displayed. |

### Display Settings

| Setting | Description | Default |
|---|---|---|
| **Display Mode** | `Net Positions` – raw long minus short values. `COT Index` – normalized 0–100 value. | Net Positions |
| **COT Index Lookback (weeks)** | Number of weekly bars used to calculate the COT Index min/max range. | 26 |

### Show / Hide

| Setting | Description | Default |
|---|---|---|
| **Show Commercials (Hedgers)** | Toggle the Commercials net-position or index line. | On |
| **Show Large Speculators (Non-Comm.)** | Toggle the Large Speculators line. | On |
| **Show Small Speculators (Non-Rep.)** | Toggle the Small Speculators line. | On |
| **Show Open Interest** | Toggle the total open interest line. | Off |
| **Show Zero Line** | Toggle the dashed zero reference line (Net Positions mode only). | On |

### Colors

Each trader category has an independently configurable color:

| Category | Default Color |
|---|---|
| Commercials | 🟢 Green |
| Large Speculators | 🔵 Blue |
| Small Speculators | 🔴 Red |
| Open Interest | ⚫ Gray |

---

## How to Interpret COT Data

The Commitment of Traders report is published **every Friday** by the CFTC and covers positions as of the **previous Tuesday**. Understanding who holds what positions is the core of COT analysis.

### Trader Categories

| Category | Who they are | Typical behaviour |
|---|---|---|
| **Commercials (Hedgers)** | Producers, exporters, importers, financial institutions that use futures to hedge real-world exposure. | Often contrarian – they sell when prices are high and buy when prices are low. Considered "smart money". |
| **Large Speculators (Non-Commercial)** | Hedge funds, commodity trading advisors (CTAs), and large managed-money accounts. | Trend-following. They go long in up-trends and short in down-trends. |
| **Small Speculators (Non-Reportable)** | Retail traders and small speculators whose positions do not meet the reportable threshold. | Often the "dumb money" – frequently wrong at extremes. |

### Net Positions Mode

- **Positive value** = more longs than shorts for that category.
- **Negative value** = more shorts than longs.
- Watch for **divergence** between Commercials and Large Specs – extremes often precede reversals.

### COT Index Mode

The COT Index normalises the net position relative to the range seen over the lookback period:

```
COT Index = ((Current Net Position - Lowest) / (Highest - Lowest)) × 100
```

| Index Range | Interpretation |
|---|---|
| **75 – 100** | Extremely net-long (potential overbought for specs; bullish signal for commercials) |
| **25 – 75** | Neutral range |
| **0 – 25** | Extremely net-short (potential oversold for specs; bearish signal for commercials) |

> **Classic setup:** Commercials COT Index near 100 (heavy hedging/short) + Large Spec COT Index near 100 (crowded long) → watch for a potential top.

---

## Supported Markets

### Forex

| Market | CFTC Code |
|---|---|
| EUR (Euro FX) | 099741 |
| GBP (British Pound) | 096742 |
| JPY (Japanese Yen) | 097741 |
| AUD (Australian Dollar) | 232741 |
| CAD (Canadian Dollar) | 090741 |
| CHF (Swiss Franc) | 092741 |
| NZD (New Zealand Dollar) | 112741 |

### Commodities

| Market | CFTC Code |
|---|---|
| Gold | 088691 |
| Silver | 084691 |
| Crude Oil (WTI) | 067651 |
| Natural Gas | 023651 |
| Copper | 085692 |
| Corn | 002602 |
| Soybeans | 005602 |
| Wheat | 001602 |

### Indices

| Market | CFTC Code |
|---|---|
| S&P 500 (E-mini) | 13874A |
| Nasdaq 100 (E-mini) | 209742 |
| Dow Jones (E-mini) | 124603 |
| Russell 2000 (E-mini) | 239742 |

---

## Screenshots

> _Screenshots below are placeholders. After installing the indicator on TradingView, replace the image paths with your own captures._

### Net Positions View
<!-- Replace the path below with an actual screenshot once available -->
<!-- ![Net Positions View](screenshots/net_positions.png) -->

### COT Index View
<!-- Replace the path below with an actual screenshot once available -->
<!-- ![COT Index View](screenshots/cot_index.png) -->

---

## Technical Details

- **Language:** Pine Script v6
- **Pane type:** Separate pane (`overlay=false`)
- **Data source:** CFTC Legacy COT reports via TradingView (`CFTC:` prefix tickers)
- **Data frequency:** Weekly (published every Friday; forward-filled on all timeframes)
- **Data fetch method:** `request.security()` using the `"W"` timeframe with `barmerge.gaps_off`
- **COT ticker format:** `CFTC:<CODE>_F_L_ALL` (futures-only, legacy, all traders)

### CFTC Ticker Field Names Used

| Field | Description |
|---|---|
| `Comm_Positions_Long_All` | Commercial long contracts |
| `Comm_Positions_Short_All` | Commercial short contracts |
| `NonComm_Positions_Long_All` | Non-commercial (Large Spec) long contracts |
| `NonComm_Positions_Short_All` | Non-commercial (Large Spec) short contracts |
| `NonRept_Positions_Long_All` | Non-reportable (Small Spec) long contracts |
| `NonRept_Positions_Short_All` | Non-reportable (Small Spec) short contracts |
| `Open_Interest_All` | Total open interest |

---

## License

This project is released under the [Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/).
