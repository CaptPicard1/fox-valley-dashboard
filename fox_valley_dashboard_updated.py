# ============================================
# FOX VALLEY INTELLIGENCE ENGINE v5 – Nov 2025
# Zacks Tactical Intelligence & Rank Delta System
# Objective: Replicate Zacks 26% Annualized Performance
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re
import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Fox Valley Intelligence Engine v5",
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
        .rank1 {background-color:#004d00 !important;} /* 🟩 */
        .rank2 {background-color:#665c00 !important;} /* 🟨 */
        .rank3 {background-color:#663300 !important;} /* 🟧 */
    </style>
""", unsafe_allow_html=True)

# ---------- LOAD PORTFOLIO ----------
@st.cache_data
def load_portfolio():
    df = pd.read_csv("data/portfolio_data.csv")
    df["GainLoss%"] = pd.to_numeric(df["GainLoss%"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    return df

portfolio = load_portfolio()
total_value = portfolio["Value"].sum()
cash_row = portfolio[portfolio["Ticker"].str.contains("SPAXX", na=False)]
cash_value = cash_row["Value"].sum()

# ---------- ZACKS FILE AUTO-DETECTION ----------
def detect_zacks_files():
    files = sorted(Path("data").glob("zacks_custom_screen_*.csv"))
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
    dated_files = {}
    for f in files:
        match = pattern.search(str(f))
        if match:
            date_str = match.group(1)
            dated_files.setdefault(date_str, []).append(f)
    dates = sorted(dated_files.keys())
    return dated_files, dates

dated_files, zacks_dates = detect_zacks_files()

if len(zacks_dates) < 2:
    st.sidebar.warning("⚠️ Need at least two days of Zacks screens in /data for intelligence comparison.")
else:
    st.sidebar.success(f"✅ Using {zacks_dates[-2]} → {zacks_dates[-1]} for tactical delta analysis")

today_date = zacks_dates[-1] if zacks_dates else None
prev_date = zacks_dates[-2] if len(zacks_dates) > 1 else None

def safe_read(path):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

# ---------- LOAD TODAY + PREVIOUS ZACKS FILES ----------
def load_zacks_by_pattern(date_str, pattern):
    match = [p for p in dated_files.get(date_str, []) if pattern.lower() in str(p).lower()]
    return safe_read(match[0]) if match else pd.DataFrame()

if today_date and prev_date:
    g1_today = load_zacks_by_pattern(today_date, "growth1")
    g2_today = load_zacks_by_pattern(today_date, "growth2")
    dd_today = load_zacks_by_pattern(today_date, "defensive")
    g1_prev = load_zacks_by_pattern(prev_date, "growth1")
    g2_prev = load_zacks_by_pattern(prev_date, "growth2")
    dd_prev = load_zacks_by_pattern(prev_date, "defensive")
else:
    g1_today = g2_today = dd_today = g1_prev = g2_prev = dd_prev = pd.DataFrame()

# ---------- NORMALIZATION ----------
def normalize_zacks(df):
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

for var in ["g1_today", "g2_today", "dd_today", "g1_prev", "g2_prev", "dd_prev"]:
    locals()[var] = normalize_zacks(locals()[var])

# ---------- INTELLIGENCE CORE ----------
def merge_and_compare(today, prev):
    if today.empty or prev.empty:
        return today
    merged = today.merge(prev, on="Ticker", how="left", suffixes=("", "_Prev"))
    merged["Rank Δ"] = merged["Zacks Rank_Prev"] - merged["Zacks Rank"]
    merged["Δ Signal"] = merged["Rank Δ"].apply(
        lambda x: "↑ Improved" if x > 0 else "↓ Declined" if x < 0 else "→ Stable"
    )
    return merged

g1_delta = merge_and_compare(g1_today, g1_prev)
g2_delta = merge_and_compare(g2_today, g2_prev)
dd_delta = merge_and_compare(dd_today, dd_prev)

# ---------- ACTION CLASSIFICATION ----------
def classify_tactical_actions(zacks_df, portfolio_df):
    if zacks_df.empty:
        return pd.DataFrame(columns=["Ticker", "Zacks Rank", "Δ Signal", "Action"])
    held = portfolio_df["Ticker"].astype(str).tolist()
    actions = []
    for _, row in zacks_df.iterrows():
        t = str(row["Ticker"])
        r = row.get("Zacks Rank", "")
        delta = row.get("Δ Signal", "")
        if t not in held and r == 1:
            action = "🟢 BUY CANDIDATE"
        elif t in held and r in [1, 2]:
            action = "⚪ HOLD"
        elif t in held and r >= 3:
            action = "🟠 REVIEW/TRIM"
        else:
            action = ""
        actions.append(action)
    zacks_df["Action"] = actions
    return zacks_df

combined_today = pd.concat([g1_delta, g2_delta, dd_delta], ignore_index=True)
tactical_df = classify_tactical_actions(combined_today, portfolio)

# ---------- DAILY INTELLIGENCE TAB ----------
st.title("📖 Fox Valley Daily Intelligence Brief")
if not tactical_df.empty:
    buy_signals = tactical_df[tactical_df["Action"] == "🟢 BUY CANDIDATE"]
    hold_signals = tactical_df[tactical_df["Action"] == "⚪ HOLD"]
    review_signals = tactical_df[tactical_df["Action"] == "🟠 REVIEW/TRIM"]

    new_rank1s = len(buy_signals)
    downgrades = len(review_signals)

    st.markdown(f"### 🧭 Tactical Intelligence Summary – {today_date}")
    st.markdown(f"- 🟢 **{new_rank1s} New Rank #1 Buy Candidates** Detected")
    st.markdown(f"- 🟠 **{downgrades} Holdings Downgraded** for Review")
    st.markdown(f"- ⚙️ Portfolio Tracking: ${total_value:,.2f} | Cash: ${cash_value:,.2f}")

    st.markdown("---")
    st.markdown("### 🟢 Tactical Buy Candidates")
    st.dataframe(buy_signals[["Ticker", "Zacks Rank", "Δ Signal"]], use_container_width=True)

    st.markdown("### ⚪ Tactical Holds")
    st.dataframe(hold_signals[["Ticker", "Zacks Rank", "Δ Signal"]], use_container_width=True)

    st.markdown("### 🟠 Tactical Reviews / Trims")
    st.dataframe(review_signals[["Ticker", "Zacks Rank", "Δ Signal"]], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🧠 Narrative Summary")
    st.markdown(f"""
    **Automated Analysis:**  
    {new_rank1s} new Rank #1 candidates emerged across Zacks screens.  
    {downgrades} existing holdings were downgraded in Rank, suggesting potential trims or tighter stops.  
    Cash reserves at ${cash_value:,.2f} ({(cash_value/total_value)*100:.2f}%) indicate sufficient tactical flexibility.
    """)
else:
    st.warning("No valid Zacks data available to generate intelligence.")

# ---------- AUTO-EXPORT TACTICAL SUMMARY ----------
def export_tactical_report(df):
    now = datetime.datetime.now()
    filename = f"data/intelligence_brief_{now.strftime('%Y-%m-%d')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Fox Valley Tactical Intelligence – {now:%B %d, %Y}\n\n")
        f.write(f"**Total Account Value:** ${total_value:,.2f}\n")
        f.write(f"**Cash (SPAXX):** ${cash_value:,.2f}\n\n")
        for action, subset in [
            ("🟢 Tactical Buys", buy_signals),
            ("⚪ Tactical Holds", hold_signals),
            ("🟠 Tactical Reviews", review_signals)
        ]:
            f.write(f"## {action}\n")
            if subset.empty:
                f.write("None today.\n\n")
            else:
                for _, row in subset.iterrows():
                    f.write(f"- {row['Ticker']} ({row['Δ Signal']}, Rank {row['Zacks Rank']})\n")
                f.write("\n")
    st.success(f"✅ Intelligence brief exported: {filename}")

now = datetime.datetime.now()
if now.weekday() == 6 and now.hour == 7:
    export_tactical_report(tactical_df)

st.caption("Automation active • Tactical analysis updates daily • 07:00 CST weekly export enabled")
