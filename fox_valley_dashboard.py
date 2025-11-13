# ================================================================
# Fox Valley Intelligence Engine — Enterprise Command Deck v7.4R
# Full-System Integration Build (Part A of 2)
# Captain: Paste PART B immediately where indicated at the end.
# ================================================================

import os
import io
import math
from datetime import datetime
from typing import List, Tuple
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
import csv
import zipfile

# -----------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------
st.set_page_config(
    page_title="Fox Valley Intelligence Engine — Command Deck v7.4R",
    page_icon="🧭",
    layout="wide",
)

st.markdown(
    """
    <style>
    div.block-container{padding-top:1.4rem}
    .section-card{
        background:rgba(255,255,255,.03);
        border:1px solid rgba(255,255,255,.08);
        border-radius:16px;
        padding:1rem 1.25rem;
        margin-bottom:1rem
    }
    .data-ok{color:#22c55e;font-weight:600}
    .data-warn{color:#f59e0b;font-weight:600}
    .data-err{color:#ef4444;font-weight:700}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------
# DATA PATH
# -----------------------------------------------------------
DATA_PATH = "data"

PORTFOLIO_FILE = None
ZACKS_G1_FILE = None
ZACKS_G2_FILE = None
ZACKS_DD_FILE = None

# -----------------------------------------------------------
# HELPERS
# -----------------------------------------------------------
def money(x):
    if pd.isna(x): return "—"
    return f"${x:,.2f}"

def clean_numeric(s):
    if pd.isna(s): return np.nan
    t = str(s).replace("$","").replace(",","").replace("%","").strip()
    if t.startswith("(") and t.endswith(")"):
        try: return -float(t[1:-1])
        except: return np.nan
    try: return float(t)
    except: return np.nan

# -----------------------------------------------------------
# AUTO-DETECT LATEST DATA FILES
# -----------------------------------------------------------
def auto_detect_files():
    global PORTFOLIO_FILE, ZACKS_G1_FILE, ZACKS_G2_FILE, ZACKS_DD_FILE
    files = os.listdir(DATA_PATH)

    # Portfolio
    pf = [f for f in files if f.lower().startswith("portfolio_positions_")]
    if pf:
        PORTFOLIO_FILE = os.path.join(DATA_PATH, sorted(pf)[-1])

    # Zacks screens
    def find(prefix):
        cands = [f for f in files if f.lower().startswith(prefix)]
        return os.path.join(DATA_PATH, sorted(cands)[-1]) if cands else None

    ZACKS_G1_FILE = find("zacks_custom_screen_2025-11-13 growth 1")
    ZACKS_G2_FILE = find("zacks_custom_screen_2025-11-13 growth 2")
    ZACKS_DD_FILE = find("zacks_custom_screen_2025-11-13 defensive dividends")

auto_detect_files()

# -----------------------------------------------------------
# CSV LOADER
# -----------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_csv(path):
    if not path or not os.path.exists(path):
        return pd.DataFrame(), [f"Missing file: {path}"]

    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as e:
        return pd.DataFrame(), [f"Failed to read {path}: {e}"]

    df.columns = [str(c).strip() for c in df.columns]

    # Clean numeric columns
    for c in df.columns:
        if any(k in c.lower() for k in ["value","price","gain","loss","basis","shares","cost"]):
            df[c] = df[c].apply(clean_numeric)

    # Derived field
    if "Current Value" not in df.columns and {"Shares","Current Price"}.issubset(df.columns):
        df["Current Value"] = df["Shares"] * df["Current Price"]

    return df, []

# -----------------------------------------------------------
# LOAD ALL DATA
# -----------------------------------------------------------
portfolio_df, pmsg = load_csv(PORTFOLIO_FILE) if PORTFOLIO_FILE else (pd.DataFrame(), ["Portfolio not found"])
g1_df, g1msg = load_csv(ZACKS_G1_FILE) if ZACKS_G1_FILE else (pd.DataFrame(), ["G1 not found"])
g2_df, g2msg = load_csv(ZACKS_G2_FILE) if ZACKS_G2_FILE else (pd.DataFrame(), ["G2 not found"])
dd_df, ddmsg = load_csv(ZACKS_DD_FILE) if ZACKS_DD_FILE else (pd.DataFrame(), ["DD not found"])

# -----------------------------------------------------------
# NORMALIZE TICKERS
# -----------------------------------------------------------
def normalize_ticker(df):
    if df.empty: return df
    df = df.copy()

    if "Ticker" in df.columns:
        return df

    if "Symbol" in df.columns:
        df.rename(columns={"Symbol":"Ticker"}, inplace=True)
        return df

    if "Description" in df.columns:
        df["Ticker"] = df["Description"].astype(str).str.split().str[0]
        return df

    df["Ticker"] = [f"UNK{i+1}" for i in range(len(df))]
    return df

portfolio_df = normalize_ticker(portfolio_df)
g1_df = normalize_ticker(g1_df)
g2_df = normalize_ticker(g2_df)
dd_df = normalize_ticker(dd_df)

# -----------------------------------------------------------
# COMBINE ZACKS
# -----------------------------------------------------------
all_z = pd.concat([
    g1_df.assign(Source="Growth 1") if not g1_df.empty else None,
    g2_df.assign(Source="Growth 2") if not g2_df.empty else None,
    dd_df.assign(Source="Defensive Dividends") if not dd_df.empty else None
], ignore_index=True).dropna(how="all", axis=1) if any([
    not g1_df.empty, not g2_df.empty, not dd_df.empty
]) else pd.DataFrame()

# -----------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------
st.sidebar.title("🧭 Command Deck — v7.4R")
st.sidebar.caption("Enterprise Intelligence Engine")

manual_cash = st.sidebar.number_input(
    "💰 Cash Available to Trade ($)",
    min_value=0.0,
    step=100.0,
    value=0.0,
    format="%.2f",
)

def_trail = st.sidebar.slider("Default Trailing Stop %", 1, 50, 12)

# -----------------------------------------------------------
# MAIN TITLE
# -----------------------------------------------------------
st.title("🧭 Fox Valley Intelligence Engine – Enterprise Command Deck")
st.caption("v7.4R | Portfolio + Zacks + Tactical + Allocation + Evolution + Sector Intelligence Online")
st.markdown("---")

# -----------------------------------------------------------
# PORTFOLIO OVERVIEW
# -----------------------------------------------------------
st.subheader("📊 Portfolio Overview")

val_col = next((c for c in ["Current Value","Market Value","Value"] if c in portfolio_df.columns), None)

total_value = float(pd.to_numeric(portfolio_df[val_col], errors='coerce').sum()) if val_col else 0.0
cash_value  = manual_cash
day_gain    = pd.to_numeric(portfolio_df.get("Day Gain", pd.Series(dtype=float)), errors='coerce').sum()

gl = pd.to_numeric(portfolio_df.get("Gain/Loss %", pd.Series(dtype=float)), errors='coerce')
avg_gain = gl.mean() if not gl.empty else np.nan

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Estimated Total Value", money(total_value + cash_value))
with c2: st.metric("Cash Available to Trade", money(cash_value))
with c3: st.metric("Day Gain (sum)", money(day_gain))
with c4: st.metric("Avg Gain/Loss %", f"{avg_gain:.2f}%" if not pd.isna(avg_gain) else "—")

if manual_cash > 0:
    st.success(f"Manual cash override active: {money(cash_value)}")
else:
    st.warning("Manual cash is 0 — update sidebar for accuracy.")

if not portfolio_df.empty:
    st.dataframe(portfolio_df, use_container_width=True)
else:
    st.error("Portfolio file missing or empty.")

st.markdown("---")

# -----------------------------------------------------------
# ZACKS ANALYZER
# -----------------------------------------------------------
st.subheader("🔎 Zacks Unified Analyzer – Top Candidates")

if not all_z.empty:
    if "Zacks Rank" in all_z.columns:
        all_z["Zacks Rank"] = pd.to_numeric(all_z["Zacks Rank"], errors='coerce')

    sort_cols = [c for c in ["Zacks Rank","PEG","PE"] if c in all_z.columns]
    if sort_cols:
        all_z = all_z.sort_values(by=sort_cols, ascending=True)

    top_n = st.slider("Top-N Candidates", 4, 30, 8)
    st.dataframe(all_z.head(top_n), use_container_width=True)

    tickers = ", ".join(sorted(set(all_z.head(top_n)["Ticker"].astype(str))))
    st.code(tickers, language="text")
else:
    st.warning("No Zacks data available.")

st.markdown("---")

# ==== END OF PART A — INSERT PART B DIRECTLY BELOW THIS LINE ====
# ============================================================
# PART B — Tactical Engine, Allocation Engine, Heatmaps,
# Evolution Engine, Sector Intelligence, Export Engine
# ============================================================

# -----------------------------------------------------------
# Tactical Log (Mission B1)
# -----------------------------------------------------------
if "tactical_log" not in st.session_state:
    st.session_state.tactical_log = []

def log_tactical_action(action_type, ticker, quantity=None, percent=None, notes=""):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action_type,
        "ticker": ticker,
        "quantity": quantity,
        "percent": percent,
        "notes": notes,
    }
    st.session_state.tactical_log.append(entry)

def display_tactical_log():
    st.subheader("📘 Tactical Log — Session Actions")
    if not st.session_state.tactical_log:
        st.info("No tactical actions recorded.")
        return
    for e in st.session_state.tactical_log:
        st.markdown(f"**[{e['timestamp']}]** — `{e['action']}` **{e['ticker']}**")
        if e.get("quantity"): st.write(f"Shares: {e['quantity']}")
        if e.get("percent"): st.write(f"Trim %: {e['percent']}%")
        if e.get("notes"): st.write(f"Notes: {e['notes']}")
        st.markdown("---")

# -----------------------------------------------------------
# Tactical Intelligence Engine (Mission B4)
# -----------------------------------------------------------
def generate_tactical_insights(action_type, ticker, quantity=None, percent=None):
    intel = []

    # Portfolio alignment
    exists = portfolio_df[portfolio_df["Ticker"].astype(str).str.upper() == str(ticker).upper()]
    intel.append("Existing position detected." if not exists.empty else "New position.")

    # Zacks alignment
    if not all_z.empty:
        z = all_z[all_z["Ticker"].astype(str).str.upper() == str(ticker).upper()]
        if not z.empty:
            rank = z.get("Zacks Rank", pd.Series([None])).iloc[0]
            intel.append(f"Zacks Rank {rank} detected." if rank else "Present in Zacks screens.")
        else:
            intel.append("Ticker not present in Zacks screens.")

    # Action-specific
    if action_type == "BUY": intel.append("BUY action — confirm allocation alignment.")
    elif action_type == "SELL": intel.append("SELL action — validate exit rationale.")
    elif action_type == "HOLD": intel.append("HOLD logged — no change.")
    elif action_type == "TRIM": intel.append(f"TRIM at {percent}% — evaluate profit capture.")

    return intel

def display_insights(intel):
    st.markdown("### 🧠 Tactical Intelligence Insights")
    for item in intel:
        st.markdown(f"- {item}")
    st.markdown("---")

# -----------------------------------------------------------
# Tactical Console (Integrated B1–B4)
# -----------------------------------------------------------
def tactical_console():
    st.header("🎯 Tactical Operations Center — v7.4R")

    c1, c2, c3 = st.columns([2,2,3])
    with c1:
        action_type = st.selectbox("Action", ["BUY","SELL","HOLD","TRIM"], key="v74_action")
        ticker = st.text_input("Ticker", key="v74_ticker")
    with c2:
        qty = st.number_input("Shares (if applicable)", min_value=0, key="v74_qty")
        tpercent = st.slider("Trim %", 1, 50, 10, key="v74_trim")
    with c3:
        notes = st.text_area("Execution Notes", key="v74_notes")
        st.write("")
        if st.button("Log Action", use_container_width=True):
            intel = generate_tactical_insights(action_type, ticker, qty, tpercent if action_type=="TRIM" else None)
            display_insights(intel)
            log_tactical_action(action_type, ticker, qty if qty>0 else None,
                                tpercent if action_type=="TRIM" else None, notes)
            st.success(f"Logged {action_type} for {ticker}")

    st.markdown("---")
    display_tactical_log()

tactical_console()

# -----------------------------------------------------------
# Allocation Engine (Mission C)
# -----------------------------------------------------------
ALLOCATION_MAP = {
    "NVDA":"Growth","AMZN":"Growth","COMM":"Growth","RDDT":"Growth","NBIX":"Growth",
    "NEM":"Defensive","ALL":"Defensive","HSBC":"Defensive","PRK":"Defensive","NVT":"Defensive",
    "AU":"Core","IBKR":"Core","CNQ":"Core","TPC":"Core","NTB":"Core",
    "LCII":"Core","CUBI":"Core","CALX":"Core","KAR":"Core"
}

def apply_allocation_category(df):
    if df.empty: return df
    df = df.copy()
    df["Category"] = df["Ticker"].apply(lambda x: ALLOCATION_MAP.get(str(x).upper(), "Unassigned"))
    return df

def calculate_allocation(df):
    if df.empty or "Current Value" not in df.columns:
        return df, {}
    df = df.copy()
    total = df["Current Value"].sum()
    if total <= 0:
        return df, {}
    df["Allocation %"] = (df["Current Value"] / total) * 100
    cat_w = (df.groupby("Category")["Current Value"].sum() / total * 100).to_dict()
    return df, cat_w

def allocation_panel():
    st.header("📊 Allocation System — v7.4R")
    if portfolio_df.empty:
        st.warning("Portfolio not loaded — cannot compute allocation.")
        return
    df = apply_allocation_category(portfolio_df)
    df, cat_w = calculate_allocation(df)
    st.dataframe(df[[c for c in ["Ticker","Description","Current Value","Category","Allocation %"]
                     if c in df.columns]], use_container_width=True)
    st.subheader("📡 Category Exposure (%)")
    if not cat_w:
        st.info("No category exposure data available.")
    else:
        for k, v in cat_w.items():
            st.write(f"**{k}: {v:.2f}%**")

allocation_panel()

st.markdown("---")

# -----------------------------------------------------------
# Performance Heatmap (Mission D)
# -----------------------------------------------------------
def make_performance_heatmap(df):
    if df.empty or "Ticker" not in df.columns or "Gain/Loss %" not in df.columns:
        st.info("Insufficient data for heatmap.")
        return
    df = df.copy()
    df["Gain/Loss %"] = pd.to_numeric(df["Gain/Loss %"], errors="coerce")
    df = df[df["Gain/Loss %"].notna()]
    if df.empty:
        st.warning("No numerical gain/loss data available.")
        return

    chart = alt.Chart(df).mark_rect().encode(
        x=alt.X("Ticker:N", sort=None, title=""),
        y=alt.Y("Category:N", sort=None, title=""),
        color=alt.Color("Gain/Loss %:Q", scale=alt.Scale(scheme="redyellowgreen")),
        tooltip=["Ticker","Category","Gain/Loss %","Current Value"]
    ).properties(height=200)

    st.altair_chart(chart, use_container_width=True)

st.header("🔥 Performance Heatmap — v7.4R")
make_performance_heatmap(apply_allocation_category(portfolio_df))

st.markdown("---")

# -----------------------------------------------------------
# Zacks Evolution Engine (Mission E)
# -----------------------------------------------------------
def load_all_zacks_versions():
    return sorted([f for f in os.listdir(DATA_PATH) if f.lower().startswith("zacks_custom_screen_")])

def compare_zacks_versions(latest_file, prev_file):
    try:
        latest = pd.read_csv(os.path.join(DATA_PATH, latest_file))
        prev = pd.read_csv(os.path.join(DATA_PATH, prev_file))
    except:
        return [], []
    lset = set(latest["Ticker"].astype(str))
    pset = set(prev["Ticker"].astype(str))
    new = sorted(list(lset - pset))
    dropped = sorted(list(pset - lset))
    return new, dropped

st.header("📈 Zacks Evolution Engine — v7.4R")
all_versions = load_all_zacks_versions()

if len(all_versions) < 2:
    st.info("Not enough Zacks files for trend comparison.")
else:
    latest = all_versions[-1]
    prev = all_versions[-2]
    st.write(f"Comparing `{latest}` vs `{prev}`")
    new, dropped = compare_zacks_versions(latest, prev)
    st.subheader("🟢 New")
    st.write(new if new else "None")
    st.subheader("🔻 Dropped")
    st.write(dropped if dropped else "None")

st.markdown("---")

# -----------------------------------------------------------
# Sector Intelligence Engine v1.1 (Mission F)
# -----------------------------------------------------------
SECTOR_MAP = {
    "NVDA":"Technology","AMZN":"Consumer Discretionary","COMM":"Communication","RDDT":"Communication",
    "NBIX":"Healthcare","NEM":"Materials","ALL":"Financials","HSBC":"Financials","PRK":"Financials",
    "NVT":"Industrials","AU":"Materials","IBKR":"Financials","CNQ":"Energy","TPC":"Industrials",
    "NTB":"Financials","LCII":"Consumer Discretionary","CUBI":"Financials","CALX":"Technology","KAR":"Consumer Discretionary"
}

SECTOR_MAP_LOWER = {k.lower(): v for k, v in SECTOR_MAP.items()}

def resolve_sector(ticker: str):
    if not ticker:
        return "Unassigned"
    t = str(ticker).upper()
    tl = t.lower()

    if t in SECTOR_MAP:
        return SECTOR_MAP[t]
    if tl in SECTOR_MAP_LOWER:
        return SECTOR_MAP_LOWER[tl]

    base = t.replace(".","").replace("-","").split()[0]
    if base in SECTOR_MAP:
        return SECTOR_MAP[base]

    return "Unassigned"

def apply_sector(df):
    if df.empty: return df
    df = df.copy()
    df["Sector"] = df["Ticker"].apply(resolve_sector)
    return df

def render_sector_exposure(df):
    st.header("🏛 Sector Exposure Map — v7.4R")
    if df.empty:
        st.info("Portfolio not loaded.")
        return

    df = apply_sector(df)

    if "Current Value" not in df.columns:
        st.warning("Missing Current Value data.")
        return

    total = df["Current Value"].sum()
    sector_weights = (df.groupby("Sector")["Current Value"].sum() / total * 100).sort_values(ascending=False)

    st.subheader("📡 Sector Allocation (%)")
    for sec, pct in sector_weights.items():
        st.write(f"**{sec}: {pct:.2f}%**")

    bar = alt.Chart(df).mark_bar().encode(
        x=alt.X("Sector:N", sort=None),
        y=alt.Y("Current Value:Q"),
        tooltip=["Sector","Current Value","Ticker"]
    ).properties(height=300)
    st.altair_chart(bar, use_container_width=True)

    heat = alt.Chart(df).mark_rect().encode(
        x=alt.X("Ticker:N", sort=None),
        y=alt.Y("Sector:N", sort=None),
        color=alt.Color("Current Value:Q", scale=alt.Scale(scheme="blues")),
        tooltip=["Ticker","Sector","Current Value"]
    ).properties(height=220)
    st.altair_chart(heat, use_container_width=True)

render_sector_exposure(portfolio_df)

st.markdown("---")

# -----------------------------------------------------------
# Export System
# -----------------------------------------------------------
def export_bundle():
    st.header("📤 Export Unified Data Bundle (.zip)")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        if PORTFOLIO_FILE:
            z.write(PORTFOLIO_FILE, arcname=os.path.basename(PORTFOLIO_FILE))
        for f in [ZACKS_G1_FILE, ZACKS_G2_FILE, ZACKS_DD_FILE]:
            if f:
                z.write(f, arcname=os.path.basename(f))
        tbuf = io.StringIO()
        writer = csv.writer(tbuf)
        writer.writerow(["timestamp","action","ticker","quantity","percent","notes"])
        for e in st.session_state.tactical_log:
            writer.writerow([e["timestamp"], e["action"], e["ticker"], e["quantity"], e["percent"], e["notes"]])
        z.writestr("tactical_log.csv", tbuf.getvalue())

    st.download_button("Download Bundle", buf.getvalue(), "fvie_export_v74R.zip")

export_bundle()

# -----------------------------------------------------------
# Footer Diagnostics
# -----------------------------------------------------------
st.markdown("---")
st.caption(f"🧭 Command Deck v7.4R — Build Time: {datetime.now():%Y-%m-%d %H:%M:%S} | Enterprise Integration Complete")

# END OF FILE — v7.4R
