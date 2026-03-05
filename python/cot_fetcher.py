"""
cot_fetcher.py — Auto-fetch, parse, analyse, and chart CFTC COT data.

Usage examples
--------------
# Fetch and plot EUR/USD (Disaggregated report, 52-week COT Index):
    python cot_fetcher.py --market "EUR/USD"

# Fetch and plot Gold with raw net positions:
    python cot_fetcher.py --market "Gold" --no-index

# Use Legacy report for S&P 500, 26-week lookback:
    python cot_fetcher.py --market "S&P 500 E-mini" --report legacy --lookback 26

# Save chart as HTML (default) and PNG:
    python cot_fetcher.py --market "Crude Oil WTI" --save --png

# List available markets:
    python cot_fetcher.py --list-markets

Data sources
------------
Primary  : CFTC Disaggregated Futures-Only  (fut_disagg_txt.zip)
Secondary: CFTC Legacy Futures-Only         (deacom.zip / deahistfo.zip)
Website  : https://www.cftc.gov/MarketReports/CommitmentsofTraders/
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import zipfile
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import requests
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Local config — fall back gracefully if run from outside the package dir
# ---------------------------------------------------------------------------
try:
    from config import (
        CFTC_URLS,
        CHART_COLORS,
        CHART_PANEL_TITLES,
        DEFAULT_LOOKBACK,
        DISAGG_COLS,
        EXTREME_HIGH,
        EXTREME_LOW,
        LEGACY_COLS,
        MARKETS,
        OUTPUT_DIR,
        REQUEST_TIMEOUT,
    )
except ModuleNotFoundError:
    # Allow running as a standalone script from any directory
    sys.path.insert(0, str(Path(__file__).parent))
    from config import (  # type: ignore
        CFTC_URLS,
        CHART_COLORS,
        CHART_PANEL_TITLES,
        DEFAULT_LOOKBACK,
        DISAGG_COLS,
        EXTREME_HIGH,
        EXTREME_LOW,
        LEGACY_COLS,
        MARKETS,
        OUTPUT_DIR,
        REQUEST_TIMEOUT,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  DOWNLOAD HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _download_zip(url: str, timeout: int = REQUEST_TIMEOUT) -> bytes:
    """Download a ZIP file from *url* and return its raw bytes."""
    print(f"  Downloading: {url}")
    resp = requests.get(url, timeout=timeout, stream=True)
    resp.raise_for_status()
    return resp.content


def _read_csv_from_zip(zip_bytes: bytes, encoding: str = "latin-1") -> pd.DataFrame:
    """
    Open an in-memory ZIP archive and read the first CSV/TXT file found.
    Returns a raw DataFrame (all columns as strings for robustness).
    """
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith((".csv", ".txt"))]
        if not csv_names:
            raise ValueError("No CSV/TXT file found inside the ZIP archive.")
        # Prefer files without 'readme' in the name
        data_files = [n for n in csv_names if "readme" not in n.lower()]
        target = data_files[0] if data_files else csv_names[0]
        print(f"  Reading file from ZIP: {target}")
        with zf.open(target) as fh:
            return pd.read_csv(fh, encoding=encoding, low_memory=False, dtype=str)


def _read_txt_url(url: str, timeout: int = REQUEST_TIMEOUT) -> pd.DataFrame:
    """Download a plain-text CSV (not zipped) and return a raw DataFrame."""
    print(f"  Downloading plain text: {url}")
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return pd.read_csv(io.StringIO(resp.text), dtype=str, low_memory=False)


# ─────────────────────────────────────────────────────────────────────────────
#  FETCH  (Disaggregated & Legacy)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_disaggregated(include_history: bool = True) -> pd.DataFrame:
    """
    Fetch the CFTC Disaggregated Futures-Only report.

    Tries the current-year ZIP first.  When *include_history* is True, also
    appends:
      • The 2006–2016 bulk historical ZIP.
      • Individual year ZIPs for 2017 through the prior calendar year.

    Returns a combined, date-sorted DataFrame with standardised column names.

    Note: The CFTC bulk archive only covers 2006–2016. Data from 2017 onward
    is fetched year-by-year from ``fut_disagg_txt_{year}.zip``.
    """
    import datetime

    frames: list[pd.DataFrame] = []

    # Current year
    try:
        raw = _download_zip(CFTC_URLS["disaggregated_current_txt"])
        frames.append(_read_csv_from_zip(raw))
    except Exception as exc:
        print(f"  Warning: could not fetch current disaggregated data — {exc}")

    if include_history:
        # 2006–2016 bulk ZIP
        try:
            raw = _download_zip(CFTC_URLS["disaggregated_history"])
            frames.append(_read_csv_from_zip(raw))
        except Exception as exc:
            print(f"  Warning: could not fetch 2006–2016 disaggregated data — {exc}")

        # 2017 through last complete year (year-by-year)
        current_year = datetime.date.today().year
        url_tpl = CFTC_URLS.get("disaggregated_history_url_template", "")
        if url_tpl:
            for yr in range(2017, current_year):
                try:
                    raw = _download_zip(url_tpl.format(year=yr))
                    frames.append(_read_csv_from_zip(raw))
                except Exception as exc:
                    print(f"  Warning: could not fetch {yr} disaggregated data — {exc}")

    if not frames:
        raise RuntimeError("Failed to fetch any disaggregated COT data.")

    df = pd.concat(frames, ignore_index=True)
    return _clean_disaggregated(df)


def fetch_legacy(include_history: bool = True) -> pd.DataFrame:
    """
    Fetch the CFTC Legacy Futures-Only report.

    Returns a combined, date-sorted DataFrame with standardised column names.
    """
    frames: list[pd.DataFrame] = []

    # Current year
    try:
        raw = _download_zip(CFTC_URLS["legacy_current"])
        frames.append(_read_csv_from_zip(raw))
    except Exception as exc:
        print(f"  Warning: could not fetch current legacy data — {exc}")
        # Fallback: plain-text version
        try:
            frames.append(_read_txt_url(CFTC_URLS["legacy_current_txt"]))
        except Exception as exc2:
            print(f"  Warning: plain-text fallback also failed — {exc2}")

    if include_history:
        try:
            raw = _download_zip(CFTC_URLS["legacy_history"])
            frames.append(_read_csv_from_zip(raw))
        except Exception as exc:
            print(f"  Warning: could not fetch historical legacy data — {exc}")

    if not frames:
        raise RuntimeError("Failed to fetch any legacy COT data.")

    df = pd.concat(frames, ignore_index=True)
    return _clean_legacy(df)


# ─────────────────────────────────────────────────────────────────────────────
#  CLEANING & NORMALISATION
# ─────────────────────────────────────────────────────────────────────────────

def _numeric_col(df: pd.DataFrame, col: str) -> pd.Series:
    """Convert a string column to numeric, coercing errors to NaN."""
    if col not in df.columns:
        return pd.Series(0, index=df.index)
    return pd.to_numeric(df[col].str.replace(",", ""), errors="coerce").fillna(0)


def _clean_disaggregated(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise a raw disaggregated DataFrame into a standard schema:
      date, market_name, cftc_code, open_interest,
      mm_long, mm_short, pm_long, pm_short,
      nr_long, nr_short, swap_long, swap_short
    """
    c = DISAGG_COLS
    # Flexible column matching (strip whitespace, case-insensitive)
    df.columns = df.columns.str.strip()

    result = pd.DataFrame()
    result["date"]          = pd.to_datetime(df[c["date"]].str.strip(), errors="coerce")
    result["market_name"]   = df[c["market_name"]].str.strip()
    result["cftc_code"]     = df[c["cftc_code"]].str.strip()
    result["open_interest"] = _numeric_col(df, c["open_interest"])
    result["mm_long"]       = _numeric_col(df, c["mm_long"])
    result["mm_short"]      = _numeric_col(df, c["mm_short"])
    result["pm_long"]       = _numeric_col(df, c["pm_long"])
    result["pm_short"]      = _numeric_col(df, c["pm_short"])
    result["nr_long"]       = _numeric_col(df, c["nr_long"])
    result["nr_short"]      = _numeric_col(df, c["nr_short"])
    result["swap_long"]     = _numeric_col(df, c["swap_long"])
    result["swap_short"]    = _numeric_col(df, c["swap_short"])

    result = result.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return result


def _clean_legacy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise a raw legacy DataFrame into a standard schema:
      date, market_name, cftc_code, open_interest,
      nc_long, nc_short, com_long, com_short,
      nr_long, nr_short
    """
    c = LEGACY_COLS
    df.columns = df.columns.str.strip()

    result = pd.DataFrame()
    result["date"]          = pd.to_datetime(df[c["date"]].str.strip(), errors="coerce")
    result["market_name"]   = df[c["market_name"]].str.strip()
    result["cftc_code"]     = df[c["cftc_code"]].str.strip()
    result["open_interest"] = _numeric_col(df, c["open_interest"])
    result["nc_long"]       = _numeric_col(df, c["nc_long"])
    result["nc_short"]      = _numeric_col(df, c["nc_short"])
    result["com_long"]      = _numeric_col(df, c["com_long"])
    result["com_short"]     = _numeric_col(df, c["com_short"])
    result["nr_long"]       = _numeric_col(df, c["nr_long"])
    result["nr_short"]      = _numeric_col(df, c["nr_short"])

    result = result.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  MARKET FILTER
# ─────────────────────────────────────────────────────────────────────────────

def filter_market(df: pd.DataFrame, market: str) -> pd.DataFrame:
    """
    Filter *df* to rows matching *market*.

    Matching strategy (in order):
      1. Exact CFTC code match (most reliable).
      2. Case-insensitive substring match on market_name.
    """
    if market not in MARKETS:
        raise ValueError(
            f"Unknown market '{market}'. "
            f"Available: {', '.join(MARKETS.keys())}"
        )

    info = MARKETS[market]
    cftc_code = info["cftc_code"]
    keyword   = info["code"].upper()

    # 1. Try CFTC code
    mask = df["cftc_code"].str.strip() == cftc_code
    subset = df[mask].copy()

    # 2. Fallback: name substring
    if subset.empty:
        mask = df["market_name"].str.upper().str.contains(keyword, na=False)
        subset = df[mask].copy()

    if subset.empty:
        raise ValueError(
            f"No data found for market '{market}' "
            f"(CFTC code: {cftc_code}, keyword: '{keyword}')."
        )

    # De-duplicate by date (keep last record per date)
    subset = subset.drop_duplicates(subset="date", keep="last")
    return subset.sort_values("date").reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
#  NET POSITION & COT INDEX CALCULATION
# ─────────────────────────────────────────────────────────────────────────────

def compute_net_positions(df: pd.DataFrame, report_type: str = "disaggregated") -> pd.DataFrame:
    """
    Calculate net positions (Long − Short) for each trader category.

    Disaggregated report produces:
      net_funds, net_producers, net_retail, net_swap

    Legacy report produces:
      net_funds (= Non-Commercial), net_producers (= Commercial), net_retail
    """
    out = df[["date", "market_name", "cftc_code", "open_interest"]].copy()

    if report_type == "disaggregated":
        out["net_funds"]     = df["mm_long"]  - df["mm_short"]
        out["net_producers"] = df["pm_long"]  - df["pm_short"]
        out["net_retail"]    = df["nr_long"]  - df["nr_short"]
        out["net_swap"]      = df.get("swap_long", 0) - df.get("swap_short", 0)
    else:  # legacy
        out["net_funds"]     = df["nc_long"]  - df["nc_short"]
        out["net_producers"] = df["com_long"] - df["com_short"]
        out["net_retail"]    = df["nr_long"]  - df["nr_short"]
        out["net_swap"]      = 0

    # Week-over-week changes
    for col in ["net_funds", "net_producers", "net_retail"]:
        out[f"{col}_chg"] = out[col].diff()

    return out


def compute_cot_index(series: pd.Series, lookback: int = DEFAULT_LOOKBACK) -> pd.Series:
    """
    Calculate the COT Index as a percentile ranking.

    For each row:  index = (value − min_N) / (max_N − min_N) × 100

    where max_N and min_N are the rolling highest/lowest over the last
    *lookback* weeks (inclusive of the current row).

    Returns values in [0, 100]; NaN for the first (lookback − 1) rows.
    """
    rolling_max = series.rolling(window=lookback, min_periods=lookback).max()
    rolling_min = series.rolling(window=lookback, min_periods=lookback).min()
    rng = rolling_max - rolling_min
    idx = (series - rolling_min) / rng * 100
    idx[rng == 0] = 50.0  # flat range → neutral
    return idx


def add_cot_index(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK) -> pd.DataFrame:
    """Append COT Index columns to a net-positions DataFrame."""
    out = df.copy()
    for col in ["net_funds", "net_producers", "net_retail"]:
        out[f"{col}_idx"] = compute_cot_index(out[col], lookback)
    return out


# ─────────────────────────────────────────────────────────────────────────────
#  CHARTING
# ─────────────────────────────────────────────────────────────────────────────

def _format_value(val: float) -> str:
    """Format a net-position value with thousands separator."""
    return f"{val:,.0f}"


def build_chart(
    df: pd.DataFrame,
    market: str,
    report_type: str = "disaggregated",
    use_index: bool = False,
    lookback: int = DEFAULT_LOOKBACK,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> go.Figure:
    """
    Build a three-panel interactive Plotly chart matching the reference image:
      • Top panel    (Red)    — Retail Traders / Non-Reportable
      • Middle panel (Orange) — Fund Managers  / Managed Money
      • Bottom panel (Blue)   — Producers & Users / Commercials

    Parameters
    ----------
    df          : Processed DataFrame (output of add_cot_index).
    market      : Human-readable market name (for the chart title).
    report_type : 'disaggregated' or 'legacy'.
    use_index   : If True, plot the COT Index (0–100) instead of raw net.
    lookback    : Lookback for COT Index (shown in subtitle).
    start_date  : Optional ISO date string to filter the x-axis start.
    end_date    : Optional ISO date string to filter the x-axis end.
    """
    # Optional date filter
    plot_df = df.copy()
    if start_date:
        plot_df = plot_df[plot_df["date"] >= pd.Timestamp(start_date)]
    if end_date:
        plot_df = plot_df[plot_df["date"] <= pd.Timestamp(end_date)]

    if plot_df.empty:
        raise ValueError("No data in the specified date range.")

    # Column selection
    if use_index:
        col_retail    = "net_retail_idx"
        col_funds     = "net_funds_idx"
        col_producers = "net_producers_idx"
        y_suffix      = " COT Index (%)"
    else:
        col_retail    = "net_retail"
        col_funds     = "net_funds"
        col_producers = "net_producers"
        y_suffix      = " Net Contracts"

    dates     = plot_df["date"]
    retail    = plot_df[col_retail]
    funds     = plot_df[col_funds]
    producers = plot_df[col_producers]

    # Current (last) values
    cur_retail    = retail.iloc[-1]    if not retail.isna().all()    else float("nan")
    cur_funds     = funds.iloc[-1]     if not funds.isna().all()     else float("nan")
    cur_producers = producers.iloc[-1] if not producers.isna().all() else float("nan")

    # Week-over-week changes
    chg_retail    = plot_df["net_retail_chg"].iloc[-1]
    chg_funds     = plot_df["net_funds_chg"].iloc[-1]
    chg_producers = plot_df["net_producers_chg"].iloc[-1]

    # Colours
    C = CHART_COLORS
    bg  = C["bg"]
    grd = C["grid"]
    txt = C["text"]

    # ── Create figure with 3 vertically stacked subplots ─────────────────────
    titles = [
        CHART_PANEL_TITLES["retail"]    + f"  ▸ {_format_value(cur_retail)}" + (f"  ({chg_retail:+,.0f})" if not pd.isna(chg_retail) else ""),
        CHART_PANEL_TITLES["funds"]     + f"  ▸ {_format_value(cur_funds)}"  + (f"  ({chg_funds:+,.0f})"  if not pd.isna(chg_funds)  else ""),
        CHART_PANEL_TITLES["producers"] + f"  ▸ {_format_value(cur_producers)}" + (f"  ({chg_producers:+,.0f})" if not pd.isna(chg_producers) else ""),
    ]

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=titles,
        row_heights=[1, 1, 1],
    )

    # ── Helper: add zero reference line ──────────────────────────────────────
    def _add_zero_line(row: int) -> None:
        fig.add_hline(
            y=0,
            line_color=C["zero_line"],
            line_width=1,
            line_dash="dot",
            row=row,
            col=1,
        )

    # ── Helper: add extreme bands (COT Index mode) ────────────────────────────
    def _add_extreme_bands(row: int) -> None:
        for level, fill_col in [
            (EXTREME_HIGH, "rgba(255,0,0,0.08)"),
            (EXTREME_LOW,  "rgba(0,200,0,0.08)"),
        ]:
            fig.add_hline(
                y=level,
                line_color=fill_col,
                line_width=1,
                line_dash="dash",
                row=row,
                col=1,
            )

    # ── Panel 1: Retail (Red) ─────────────────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=retail,
            mode="lines",
            name="Retail Traders",
            line=dict(color=C["retail"], width=2),
            fill="tozeroy",
            fillcolor=f"rgba(255,45,85,0.08)",
            hovertemplate="<b>Retail</b><br>Date: %{x|%Y-%m-%d}<br>Net: %{y:,.0f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    _add_zero_line(1)
    if use_index:
        _add_extreme_bands(1)

    # ── Panel 2: Fund Managers (Orange) ───────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=funds,
            mode="lines",
            name="Fund Managers",
            line=dict(color=C["funds"], width=2),
            fill="tozeroy",
            fillcolor=f"rgba(255,140,0,0.08)",
            hovertemplate="<b>Fund Managers</b><br>Date: %{x|%Y-%m-%d}<br>Net: %{y:,.0f}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    _add_zero_line(2)
    if use_index:
        _add_extreme_bands(2)

    # ── Panel 3: Producers (Blue) ─────────────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=producers,
            mode="lines",
            name="Producers & Users",
            line=dict(color=C["producers"], width=2),
            fill="tozeroy",
            fillcolor=f"rgba(41,121,255,0.08)",
            hovertemplate="<b>Producers</b><br>Date: %{x|%Y-%m-%d}<br>Net: %{y:,.0f}<extra></extra>",
        ),
        row=3,
        col=1,
    )
    _add_zero_line(3)
    if use_index:
        _add_extreme_bands(3)

    # ── Layout ────────────────────────────────────────────────────────────────
    idx_info = f" — COT Index ({lookback}w)" if use_index else ""
    report_label = "Disaggregated" if report_type == "disaggregated" else "Legacy"

    fig.update_layout(
        title=dict(
            text=f"<b>Campus COT Report — {market}</b><br>"
                 f"<span style='font-size:11px;color:{txt}'>"
                 f"{report_label} Report{idx_info} · Source: CFTC</span>",
            font=dict(color=txt, size=16),
            x=0.01,
        ),
        paper_bgcolor=bg,
        plot_bgcolor=bg,
        font=dict(color=txt, size=11),
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0,
            y=-0.04,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=txt),
        ),
        height=900,
        margin=dict(l=60, r=80, t=100, b=60),
    )

    # Apply dark-theme axes to all panels
    for i in range(1, 4):
        yaxis_key = "yaxis" if i == 1 else f"yaxis{i}"
        xaxis_key = "xaxis" if i == 1 else f"xaxis{i}"
        y_title   = "COT Index (%)" if use_index else "Net Contracts"

        fig.update_layout({
            yaxis_key: dict(
                title=y_title,
                gridcolor=grd,
                zeroline=False,
                showgrid=True,
                tickfont=dict(color=txt),
                title_font=dict(color=txt, size=10),
                side="right",
            ),
            xaxis_key: dict(
                gridcolor=grd,
                showgrid=True,
                tickfont=dict(color=txt),
                zeroline=False,
            ),
        })

    # Style subplot title annotations
    for ann in fig.layout.annotations:
        ann.font = dict(color=txt, size=11)

    return fig


# ─────────────────────────────────────────────────────────────────────────────
#  SAVE / DISPLAY
# ─────────────────────────────────────────────────────────────────────────────

def save_chart(fig: go.Figure, market: str, output_dir: str = OUTPUT_DIR, as_png: bool = False) -> str:
    """
    Save *fig* as an interactive HTML file (and optionally a PNG).

    Returns the path to the saved HTML file.
    """
    os.makedirs(output_dir, exist_ok=True)
    safe_name = market.replace("/", "_").replace(" ", "_").replace("&", "and")
    html_path = os.path.join(output_dir, f"COT_{safe_name}.html")
    fig.write_html(html_path, include_plotlyjs="cdn")
    print(f"  Chart saved: {html_path}")

    if as_png:
        png_path = os.path.join(output_dir, f"COT_{safe_name}.png")
        try:
            fig.write_image(png_path, width=1600, height=900)
            print(f"  PNG saved:   {png_path}")
        except Exception as exc:
            print(f"  Warning: could not save PNG — {exc}")
            print("  (Install kaleido: pip install kaleido)")

    return html_path


# ─────────────────────────────────────────────────────────────────────────────
#  PRINT SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(df: pd.DataFrame, market: str) -> None:
    """Print a text summary of the latest COT data to the console."""
    latest = df.iloc[-1]
    prev   = df.iloc[-2] if len(df) > 1 else latest

    def _chg(col: str) -> str:
        v = latest[col] - prev[col]
        return f"{v:+,.0f}"

    print()
    print("=" * 60)
    print(f"  COT REPORT SUMMARY — {market}")
    print(f"  Date: {latest['date'].date()}")
    print("=" * 60)
    print(f"  {'Category':<25} {'Net Position':>14}  {'WoW Change':>12}")
    print(f"  {'-'*53}")
    print(f"  {'Retail (Non-Reportable)':<25} {latest['net_retail']:>14,.0f}  {_chg('net_retail'):>12}")
    print(f"  {'Fund Managers':<25} {latest['net_funds']:>14,.0f}  {_chg('net_funds'):>12}")
    print(f"  {'Producers & Users':<25} {latest['net_producers']:>14,.0f}  {_chg('net_producers'):>12}")
    if "net_retail_idx" in df.columns:
        print()
        print(f"  {'Category':<25} {'COT Index (%)':>14}")
        print(f"  {'-'*41}")
        print(f"  {'Retail':<25} {latest['net_retail_idx']:>13.1f}%")
        print(f"  {'Fund Managers':<25} {latest['net_funds_idx']:>13.1f}%")
        print(f"  {'Producers':<25} {latest['net_producers_idx']:>13.1f}%")
    print("=" * 60)
    print()


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run(
    market: str = "EUR/USD",
    report_type: str = "disaggregated",
    use_index: bool = True,
    lookback: int = DEFAULT_LOOKBACK,
    include_history: bool = True,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    save: bool = False,
    as_png: bool = False,
    output_dir: str = OUTPUT_DIR,
    show: bool = True,
) -> go.Figure:
    """
    End-to-end pipeline: fetch → parse → compute → chart.

    Returns the Plotly Figure object.
    """
    print(f"\n[COT Fetcher] Market: {market}  |  Report: {report_type}  |  COT Index: {use_index}")

    # 1. Fetch
    print("[1/4] Fetching data from CFTC...")
    if report_type == "disaggregated":
        raw = fetch_disaggregated(include_history=include_history)
    else:
        raw = fetch_legacy(include_history=include_history)

    # 2. Filter to market
    print(f"[2/4] Filtering for '{market}'...")
    market_df = filter_market(raw, market)
    print(f"      {len(market_df)} weekly records found.")

    # 3. Compute net positions & COT Index
    print("[3/4] Computing net positions and COT Index...")
    net_df  = compute_net_positions(market_df, report_type=report_type)
    full_df = add_cot_index(net_df, lookback=lookback)

    print_summary(full_df, market)

    # 4. Build chart
    print("[4/4] Building chart...")
    fig = build_chart(
        full_df,
        market=market,
        report_type=report_type,
        use_index=use_index,
        lookback=lookback,
        start_date=start_date,
        end_date=end_date,
    )

    if save:
        save_chart(fig, market, output_dir=output_dir, as_png=as_png)

    if show:
        fig.show()

    return fig


# ─────────────────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cot_fetcher",
        description="Fetch and visualise CFTC COT data as 3-panel charts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--market", "-m",
        default="EUR/USD",
        help="Market to analyse (default: %(default)s). Use --list-markets for options.",
    )
    parser.add_argument(
        "--report", "-r",
        choices=["disaggregated", "legacy"],
        default="disaggregated",
        help="CFTC report type (default: %(default)s).",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Plot raw net positions instead of the COT Index.",
    )
    parser.add_argument(
        "--lookback", "-l",
        type=int,
        default=DEFAULT_LOOKBACK,
        help="COT Index lookback in weeks (default: %(default)s).",
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Skip fetching the historical bulk data (faster, current year only).",
    )
    parser.add_argument(
        "--start",
        metavar="YYYY-MM-DD",
        default=None,
        help="Chart start date (ISO format).",
    )
    parser.add_argument(
        "--end",
        metavar="YYYY-MM-DD",
        default=None,
        help="Chart end date (ISO format).",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the chart as an HTML file in the output directory.",
    )
    parser.add_argument(
        "--png",
        action="store_true",
        help="Also save the chart as a PNG (requires kaleido).",
    )
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        help="Directory for saved charts (default: %(default)s).",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open the chart in the browser.",
    )
    parser.add_argument(
        "--list-markets",
        action="store_true",
        help="Print all available markets and exit.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()

    if args.list_markets:
        from config import MARKETS  # type: ignore[import]
        print("\nAvailable markets:\n")
        categories: dict[str, list[str]] = {}
        for name, info in MARKETS.items():
            cat = info["category"]
            categories.setdefault(cat, []).append(name)
        for cat, names in sorted(categories.items()):
            print(f"  {cat}:")
            for n in names:
                print(f"    • {n}")
        print()
        sys.exit(0)

    run(
        market          = args.market,
        report_type     = args.report,
        use_index       = not args.no_index,
        lookback        = args.lookback,
        include_history = not args.no_history,
        start_date      = args.start,
        end_date        = args.end,
        save            = args.save,
        as_png          = args.png,
        output_dir      = args.output_dir,
        show            = not args.no_show,
    )


if __name__ == "__main__":
    main()
