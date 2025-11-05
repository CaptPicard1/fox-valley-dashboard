# ============================================
# FOX VALLEY INTELLIGENCE ENGINE v6.2R - FINAL STABLE BUILD (Fidelity Fix)
# Clean rebuild for Streamlit Cloud (Nov 05, 2025)
# ============================================

import os
import pandas as pd
import streamlit as st
import plotly.express as px
import datetime
from pathlib import Path
import re

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Fox Valley Intelligence Engine v6.2R",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- DARK MODE ----------
st.markdown("""
<style>
    body {background-color:#0e1117;color:#FAFAFA;}
    [data-testid="stHeader"] {background-color:#0e1117;}
    [data-testid="stSidebar"] {background-color:#111318;}
    table {color:#FAFAFA;}
    .rank1 {background-color:#004d00 !important;}
    .rank2 {background-color:#665c00 !important;}
    .rank3 {background-color:#663300 !important;}
</style>
""", unsafe_allow_html=True)

# ---------- LOAD PORTFOLIO ----------
@st.cache_data
def load_portfolio():
    # Always look inside the /data directory of this repository
    data_path = Path(__file__).parent / "data" / "Portfolio_Positions_Nov-05-2025.csv"

    if not data_path.exists():
        st.error(f"❌ Portfolio file not found: {data_path}")
        st.stop()

    # 🧭 Fidelity CSVs have several header lines before real data
    # Try skipping 10 first; if that fails, skip 11
    df = pd.read_csv(data_path, skiprows=10)
    # If we still don't see any plausible data columns, try 11
    if not any(col.strip().lower() in ["symbol", "security symbol", "quantity"] for col in df.columns):
        df = pd.read_csv(data_path, skiprows=11)

    # Clean column names
    df.columns = [c.strip() for c in df.columns]

    # 🧩 Detect any likely ticker column and rename it to Ticker
    possible_tickers = ["Symbol", "Security Symbol", "Fund Symbol", "Product Symbol"]
    for col in possible_tickers:
        if col in df.columns:
            df.rename(columns={col: "Ticker"}, inplace=True)
            break

    # Rename other Fidelity headers to internal names
    df.rename(columns={
        "Quantity": "Shares",
        "Last Price": "MarketPrice",
        "Cost Basis Total": "CostBasis",
        "Current Value": "MarketValue",
        "Total Gain/Loss Dollar": "GainLoss$",
        "Total Gain/Loss Percent": "GainLoss%"
    }, inplace=True)

    # Clean numeric columns
    money_cols = ["MarketPrice", "CostBasis", "MarketValue", "GainLoss$", "GainLoss%"]
    for col in money_cols:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace('[\$,()%+]', '', regex=True)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Ensure Shares is numeric
    if "Shares" in df.columns:
        df["Shares"] = pd.to_numeric(df["Shares"], errors="coerce")

    # Normalize tickers
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()
        df["Ticker"] = df["Ticker"].str.replace(r"[^A-Z]", "", regex=True)
    else:
        st.error("❌ No ticker column detected after cleaning. Check the Fidelity export format.")
        st.write("Columns detected:", list(df.columns))
        st.stop()

    return df

portfolio = load_portfolio()
total_value = portfolio["MarketValue"].sum() if "MarketValue" in portfolio.columns else 0.0

# ---------- AUTO-DETECT ZACKS FILES ----------
def get_latest(pattern):
    files = Path(__file__).parent.glob(f"data/{pattern}")
    date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
    dated = []
    for f in files:
        m = date_pattern.search(str(f))
        if m:
            dated.append((m.group(1), f))
    return str(max(dated)[1]) if dated else None

G1_PATH = get_latest("zacks_custom_screen_*Growth1*.csv")
G2_PATH = get_latest("zacks_custom_screen_*Growth2*.csv")
DD_PATH = get_latest("zacks_custom_screen_*Defensive*.csv")

def safe_read(p):
    if not p:
        return pd.DataFrame()
    try:
        return pd.read_csv(p)
    except Exception:
        return pd.DataFrame()

g1 = safe_read(G1_PATH)
g2 = safe_read(G2_PATH)
dd = safe_read(DD_PATH)

# ---------- NORMALIZE ZACKS FILES ----------
def normalize(df):
    if df.empty:
        return df
    tcols = [c for c in df.columns if "ticker" in c.lower() or "symbol" in c.lower()]
    if tcols:
        df.rename(columns={tcols[0]: "Ticker"}, inplace=True)
    if "Zacks Rank" not in df.columns:
        rcols = [c for c in df.columns if "rank" in c.lower()]
        if rcols:
            df.rename(columns={rcols[0]: "Zacks Rank"}, inplace=True)
    keep = [c for c in ["Ticker", "Zacks Rank"] if c in df.columns]
    return df[keep].copy()

g1, g2, dd = normalize(g1), normalize(g2), normalize(dd)

# ---------- CROSSMATCH ----------
def cross_match(zdf, pf):
    if zdf.empty or pf.empty or "Ticker" not in pf.columns or "Ticker" not in zdf.columns:
        return pd.DataFrame()
    zdf = zdf.copy()
    pf = pf.copy()
    zdf["Ticker"] = zdf["Ticker"].astype(str)
    pf["Ticker"] = pf["Ticker"].astype(str)
    merged = zdf.merge(pf[["Ticker"]], on="Ticker", how="left", indicator=True)
    merged["Held?"] = merged["_merge"].map({"both": "✔ Held", "left_only": "🟢 Candidate"})
    merged.drop(columns=["_merge"], inplace=True)
    return merged

# ---------- INTELLIGENCE OVERLAY ----------
def build_intel(pf, g1, g2, dd):
    if pf.empty or "Ticker" not in pf.columns:
        msg = [
            "Fox Valley Daily Tactical Overlay",
            "• Portfolio data unavailable or missing Ticker column."
        ]
        return {"narrative": "\n".join(msg), "new": pd.DataFrame(), "held": pd.DataFrame()}

    combined = pd.concat([g1, g2, dd], ignore_index=True).drop_duplicates(subset=["Ticker"]) if not (g1.empty and g2.empty and dd.empty) else pd.DataFrame()
    held = set(pf["Ticker"])
    if not combined.empty and "Zacks Rank" in combined.columns:
        rank1 = combined[combined["Zacks Rank"] == 1]
    else:
        rank1 = pd.DataFrame()

    new1 = rank1[~rank1["Ticker"].isin(held)] if not rank1.empty else pd.DataFrame()
    held1 = rank1[rank1["Ticker"].isin(held)] if not rank1.empty else pd.DataFrame()

    msg = [
        "Fox Valley Daily Tactical Overlay",
        f"• Portfolio Value: ${total_value:,.2f}",
        f"• Total #1 Symbols: {len(rank1)}",
        f"• New #1 Candidates: {len(new1)}",
        f"• Held #1 Positions: {len(held1)}"
    ]
    return {"narrative": "\n".join(msg), "new": new1, "held": held1}

intel = build_intel(portfolio, g1, g2, dd)

# ---------- DASHBOARD ----------
tabs = st.tabs([
    "💼 Portfolio Overview", "📊 Growth 1", "📊 Growth 2",
    "💰 Defensive Dividend", "🧩 Tactical Summary", "📖 Daily Intelligence Brief"
])

# --- Portfolio Overview ---
with tabs[0]:
    st.metric("Total Portfolio Value", f"${total_value:,.2f}")
    st.dataframe(portfolio, use_container_width=True)
    if not portfolio.empty and "MarketValue" in portfolio.columns and "Ticker" in portfolio.columns:
        fig = px.pie(portfolio, values="MarketValue", names="Ticker", hole=0.3,
                     title="Portfolio Allocation")
        st.plotly_chart(fig, use_container_width=True)

# --- Growth 1 ---
with tabs[1]:
    st.subheader("Zacks Growth 1 Cross-Match")
    g1m = cross_match(g1, portfolio)
    if not g1m.empty:
        st.dataframe(g1m, use_container_width=True)
    else:
        st.info("No Growth 1 data available or no matches found.")

# --- Growth 2 ---
with tabs[2]:
    st.subheader("Zacks Growth 2 Cross-Match")
    g2m = cross_match(g2, portfolio)
    if not g2m.empty:
        st.dataframe(g2m, use_container_width=True)
    else:
        st.info("No Growth 2 data available or no matches found.")

# --- Defensive Dividend ---
with tabs[3]:
    st.subheader("Zacks Defensive Dividend Cross-Match")
    ddm = cross_match(dd, portfolio)
    if not ddm.empty:
        st.dataframe(ddm, use_container_width=True)
    else:
        st.info("No Defensive Dividend data available or no matches found.")

# --- Tactical Summary ---
with tabs[4]:
    st.subheader("🧩 Weekly Tactical Summary")
    st.text(intel["narrative"])

# --- Daily Intelligence Brief ---
with tabs[5]:
    st.subheader("📖 Daily Intelligence Brief")
    st.markdown(f"```text\n{intel['narrative']}\n```")
    st.caption(f"Generated {datetime.datetime.now():%A, %B %d, %Y – %I:%M %p CST}")
    if not intel["new"].empty:
        st.markdown("### 🟢 New #1 Candidates")
        st.dataframe(intel["new"], use_container_width=True)
    if not intel["held"].empty:
        st.markdown("### ✔ Held #1 Positions")
        st.dataframe(intel["held"], use_container_width=True)
