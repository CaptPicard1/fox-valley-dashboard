# 🧭 Fox Valley Intelligence Engine — Enterprise Command Deck (v7.3R-4.1 | SPAXX-Calibrated Final Build – Nov 12, 2025)
# Streamlit app — deploy-ready final build (no hot-fixes). Designed for /data CSV inputs.
# Author: #1 for CaptPicard

import os
import io
import math
from datetime import datetime
from typing import List, Tuple

import numpy as np
import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fox Valley Intelligence Engine — Command Deck v7.3R-4.1 (SPAXX-Calibrated)",
    page_icon="🧭",
    layout="wide",
)

st.markdown(
    """
    <style>
      .metric-small .stMetric {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 12px;
      }
      .data-ok {color:#22c55e;font-weight:600}
      .data-warn {color:#f59e0b;font-weight:600}
      .data-err {color:#ef4444;font-weight:700}
      .section-card {background: rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);padding: 12px 16px;border-radius: 16px}
      .subtle {opacity:.85}
      div.block-container{padding-top:1.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────
DATA_DIR = "data"
PORTFOLIO_FILE = os.path.join(DATA_DIR, "Portfolio_Positions_Nov-12-2025.csv")
ZACKS_G1_FILE = os.path.join(DATA_DIR, "zacks_custom_screen_2025-11-12 Growth 1.csv")
ZACKS_G2_FILE = os.path.join(DATA_DIR, "zacks_custom_screen_2025-11-12 Growth 2.csv")
ZACKS_DD_FILE = os.path.join(DATA_DIR, "zacks_custom_screen_2025-11-12 Defensive Dividends.csv")

# ──────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_csv(path: str) -> Tuple[pd.DataFrame, List[str]]:
    msgs = []
    if not os.path.exists(path):
        return pd.DataFrame(), [f"Missing file: {path}"]
    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as e:
        return pd.DataFrame(), [f"Failed to read {path}: {e}"]

    df.columns = [str(c).strip() for c in df.columns]

    def clean_num_series(s: pd.Series) -> pd.Series:
        def _scrub(x):
            if pd.isna(x):
                return np.nan
            t = str(x).strip()
            neg = t.startswith("(") and t.endswith(")")
            t = t.replace("(", "").replace(")", "")
            t = t.replace("$", "").replace(",", "").replace("%", "")
            try:
                v = float(t)
            except:
                return np.nan
            return -v if neg else v
        return s.apply(_scrub)

    rename_map = {
        "Price": "Current Price",
        "Market Value": "Current Value",
        "Position Value": "Current Value",
        "Value": "Current Value",
    }
    for k, v in rename_map.items():
        if k in df.columns and v not in df.columns:
            df[v] = df[k]

    for col in ["Shares", "Current Price", "Current Value", "Cost Basis", "Average Cost", "Day Change %", "Gain/Loss %", "Zacks Rank", "Day Gain", "Gain $"]:
        if col in df.columns:
            df[col] = clean_num_series(df[col])

    if "Cost Basis" not in df.columns and "Average Cost" in df.columns:
        df["Cost Basis"] = df["Average Cost"]

    if "Current Value" not in df.columns and {"Shares", "Current Price"}.issubset(df.columns):
        df["Current Value"] = df["Shares"] * df["Current Price"]
        msgs.append("Computed 'Current Value' = Shares × Current Price")

    for zr in ["Zacks Rank", "ZacksRank", "Rank"]:
        if zr in df.columns:
            df["Zacks Rank"] = pd.to_numeric(df[zr], errors="coerce")
            break

    return df, msgs

def human_money(x: float) -> str:
    if pd.isna(x):
        return "—"
    return f"${x:,.2f}"

def infer_cash(df: pd.DataFrame) -> Tuple[float, List[str]]:
    if df.empty:
        return 0.0, []
    aliases = {"SPAXX", "FDRXX", "CASH", "MONEY MARKET", "CASH RESERVE"}
    tickers = []
    if "Ticker" in df.columns:
        cash_rows = df[df["Ticker"].astype(str).str.upper().isin(aliases)]
        tickers = cash_rows["Ticker"].astype(str).tolist()
    elif "Type" in df.columns:
        cash_rows = df[df["Type"].astype(str).str.contains("money market", case=False, na=False)]
        tickers = cash_rows["Type"].astype(str).tolist()
    else:
        return 0.0, []
    if cash_rows.empty:
        return 0.0, []
    value_col = next((c for c in ["Current Value", "Market Value", "Position Value", "Value"] if c in df.columns), None)
    if not value_col:
        return 0.0, tickers
    return float(pd.to_numeric(cash_rows[value_col], errors="coerce").sum()), tickers

# ──────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────────────────────
def load_data():
    portfolio_df, port_msgs = load_csv(PORTFOLIO_FILE)
    g1_df, g1_msgs = load_csv(ZACKS_G1_FILE)
    g2_df, g2_msgs = load_csv(ZACKS_G2_FILE)
    dd_df, dd_msgs = load_csv(ZACKS_DD_FILE)
    return portfolio_df, port_msgs, g1_df, g1_msgs, g2_df, g2_msgs, dd_df, dd_msgs

portfolio_df, port_msgs, g1_df, g1_msgs, g2_df, g2_msgs, dd_df, dd_msgs = load_data()

# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
st.title("🧭 Fox Valley Intelligence Engine – Enterprise Command Deck")
st.caption("v7.3R-4.1 | SPAXX-Calibrated Final Build – November 12, 2025")

st.subheader("📊 Portfolio Overview")

value_col = next((c for c in ["Current Value", "Market Value", "Position Value", "Value"] if c in portfolio_df.columns), None)
est_total = float(pd.to_numeric(portfolio_df[value_col], errors='coerce').sum()) if value_col else 0.0
est_cash, tickers = infer_cash(portfolio_df)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Estimated Total Value", human_money(est_total))
with m2:
    st.metric("Estimated Cash Value", human_money(est_cash))
with m3:
    if "Day Gain" in portfolio_df.columns:
        day_gain = pd.to_numeric(portfolio_df["Day Gain"], errors='coerce').sum()
    else:
        day_gain = np.nan
    st.metric("Day Gain (sum)", human_money(day_gain) if not math.isnan(day_gain) else "—")
with m4:
    if "Gain/Loss %" in portfolio_df.columns:
        avg_gl = pd.to_numeric(portfolio_df["Gain/Loss %"], errors='coerce').mean()
        st.metric("Avg Gain/Loss %", f"{avg_gl:.2f}%")
    else:
        st.metric("Avg Gain/Loss %", "—")

if tickers:
    st.info(f"Cash rows detected: {', '.join(tickers)}")
else:
    st.warning("No explicit SPAXX or Money Market rows detected; cash may be zero.")

if not portfolio_df.empty:
    st.dataframe(portfolio_df, use_container_width=True)
else:
    st.error("Portfolio file failed to load or contains no rows.")

st.markdown("---")
st.subheader("🔎 Zacks Unified Analyzer")

# combine
frames = []
for df, name in [(g1_df, "Growth 1"), (g2_df, "Growth 2"), (dd_df, "Defensive Dividends")]:
    if not df.empty:
        temp = df.copy()
        temp["Source"] = name
        frames.append(temp)

if frames:
    all_zacks = pd.concat(frames, ignore_index=True)
    all_zacks = all_zacks.drop_duplicates(subset=[c for c in ["Ticker", "Source"] if c in all_zacks.columns])
    st.dataframe(all_zacks.head(10), use_container_width=True)
else:
    st.warning("No Zacks data loaded.")

st.markdown("---")
st.caption("✅ Build v7.3R-4.1 Final | SPAXX calibrated | All totals auto-detected from /data")
