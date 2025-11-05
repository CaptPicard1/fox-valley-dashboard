# ============================================
# FOX VALLEY INTELLIGENCE ENGINE v6.2R - FINAL STABLE BUILD
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

    df = pd.read_csv(data_path)
    df.columns = [c.strip() for c in df.columns]

    df.rename(columns={
        "Symbol": "Ticker",
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

    if "Shares" in df.columns:
        df["Shares"] = pd.to_numeric(df["Shares"], errors="coerce")

    # Normalize tickers
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()
        df["Ticker"] = df["Ticker"].str.replace(r"[^A-Z]", "", regex=True)

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
    if not p: return pd.DataFrame()
    try: return pd.read_csv(p)
    except: return pd.DataFrame()

g1 = safe_read(G1_PATH)
g2 = safe_read(G2_PATH)
dd = safe_read(DD_PATH)

# ---------- NORMALIZE ZACKS FILES ----------
def normalize(df):
    if df.empty: return df
    tcols = [c for c in df.columns if "ticker" in c.lower() or "symbol" in c.lower()]
    if tcols: df.rename(columns={tcols[0]: "Ticker"}, inplace=True)
    if "Zacks Rank" not in df.columns:
        rcols = [c for c in df.columns if "rank" in c.lower()]
        if rcols: df.rename(columns={rcols[0]: "Zacks Rank"}, inplace=True)
    keep = [c for c in ["Ticker", "Zacks Rank"] if c in df.columns]
    return df[keep].copy()

g1, g2, dd = normalize(g1), normalize(g2), normalize(dd)

# ---------- CROSSMATCH ----------
def cross_match(zdf, pf):
    if zdf.empty or pf.empty: return pd.DataFrame()
    zdf["Ticker"] = zdf["Ticker"].astype(str)
    pf["Ticker"] = pf["Ticker"].astype(str)
    merged = zdf.merge(pf[["Ticker"]], on="Ticker", how="left", indicator=True)
    merged["Held?"] = merged["_merge"].map({"both": "✔ Held", "left_only": "🟢 Candidate"})
    merged.drop(columns=["_merge"], inplace=True)
    return merged

# ---------- INTELLIGENCE OVERLAY ----------
def build_intel(pf, g1, g2, dd):
    combined = pd.concat([g1, g2, dd], ignore_index=True).drop_duplicates(subset=["Ticker"])
    held = set(pf["Ticker"])
    rank1 = combined[combined["Zacks Rank"] == 1] if "Zacks Rank" in combined else pd.DataFrame()
    new1 = rank1[~rank1["Ticker"].isin(held)]
    held1 = rank1[rank1["Ticker"].isin(held)]
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

with tabs[0]:
    st.metric("Total Portfolio Value", f"${total_value:,.2f}")
    st.dataframe(portfolio, use_container_width=True)
    if not portfolio.empty and "MarketValue" in portfolio.columns:
        fig = px.pie(portfolio, values="MarketValue", names="Ticker", hole=0.3,
                     title="Portfolio Allocation")
        st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.subheader("Zacks Growth 1 Cross-Match")
    st.dataframe(cross_match(g1, portfolio), use_container_width=True)

with tabs[2]:
    st.subheader("Zacks Growth 2 Cross-Match")
    st.dataframe(cross_match(g2, portfolio), use_container_width=True)

with tabs[3]:
    st.subheader("Zacks Defensive Dividend Cross-Match")
    st.dataframe(cross_match(dd, portfolio), use_container_width=True)

with tabs[4]:
    st.subheader("🧩 Weekly Tactical Summary")
    st.text(intel["narrative"])

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
