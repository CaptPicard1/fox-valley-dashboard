# ============================================
# FOX VALLEY TACTICAL DASHBOARD v4.1 – Nov 2025
# Daily Tactical Intelligence + Auto Zacks Loader + Narrative Overlay (Dark Mode)
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re
import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Fox Valley Tactical Dashboard v4.1 – Daily Intelligence",
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
    df = pd.read_csv("data/portfolio_data.csv")
    df["GainLoss%"] = pd.to_numeric(df["GainLoss%"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    return df

portfolio = load_portfolio()
total_value = portfolio["Value"].sum()
cash_row = portfolio[portfolio["Ticker"].str.contains("SPAXX", na=False)]
cash_value = cash_row["Value"].sum()

# ---------- AUTO-DETECT LATEST ZACKS FILES ----------
def get_latest_zacks_file(pattern: str):
    files = Path("data").glob(pattern)
    date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
    dated_files = []
    for f in files:
        match = date_pattern.search(str(f))
        if match:
            dated_files.append((match.group(1), f))
    if dated_files:
        latest = max(dated_files)[1]
        return str(latest)
    return None

G1_PATH = get_latest_zacks_file("zacks_custom_screen_*_Growth1.csv")
G2_PATH = get_latest_zacks_file("zacks_custom_screen_*_Growth2.csv")
DD_PATH = get_latest_zacks_file("zacks_custom_screen_*_DefensiveDividend.csv")

def safe_read(path: str | None):
    if path is None:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

g1_raw = safe_read(G1_PATH)
g2_raw = safe_read(G2_PATH)
dd_raw = safe_read(DD_PATH)

# ---------- SIDEBAR ----------
if not g1_raw.empty or not g2_raw.empty or not dd_raw.empty:
    st.sidebar.success("✅ Latest Zacks files auto-detected from /data")
else:
    st.sidebar.error("⚠️ No valid Zacks CSVs found in /data folder. Upload Nov 3 screens tomorrow.")

# ---------- NORMALIZE + CROSSMATCH ----------
def normalize_zacks(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    ticker_cols = [c for c in df.columns if "ticker" in c.lower() or "symbol" in c.lower()]
    if ticker_cols:
        df = df.rename(columns={ticker_cols[0]: "Ticker"})
    if "Zacks Rank" not in df.columns:
        rank_cols = [c for c in df.columns if "rank" in c.lower()]
        if rank_cols:
            df = df.rename(columns={rank_cols[0]: "Zacks Rank"})
    keep = [c for c in ["Ticker", "Zacks Rank"] if c in df.columns]
    return df[keep].copy()

def cross_match(zdf: pd.DataFrame, pf: pd.DataFrame) -> pd.DataFrame:
    if zdf.empty:
        return pd.DataFrame()
    pf_tickers = pf[["Ticker"]].astype(str)
    zdf["Ticker"] = zdf["Ticker"].astype(str)
    merged = zdf.merge(pf_tickers, on="Ticker", how="left", indicator=True)
    merged["Held?"] = merged["_merge"].map({"both": "✔ Held", "left_only": "🟢 Candidate"})
    merged.drop(columns=["_merge"], inplace=True)
    return merged

g1 = normalize_zacks(g1_raw)
g2 = normalize_zacks(g2_raw)
dd = normalize_zacks(dd_raw)

# ---------- INTELLIGENCE ENGINE ----------
def build_intel_overlay(portfolio_df: pd.DataFrame,
                        g1_df: pd.DataFrame,
                        g2_df: pd.DataFrame,
                        dd_df: pd.DataFrame,
                        cash_val: float,
                        total_val: float) -> dict:
    """Build AI tactical narrative and cross-summary."""
    combined = pd.concat([g1_df, g2_df, dd_df], axis=0, ignore_index=True)
    if not combined.empty:
        combined = combined.drop_duplicates(subset=["Ticker"])
    held_tickers = set(portfolio_df["Ticker"].astype(str).tolist())
    rank1 = combined[combined["Zacks Rank"] == 1] if "Zacks Rank" in combined.columns else pd.DataFrame()
    new_rank1 = rank1[~rank1["Ticker"].isin(held_tickers)] if not rank1.empty else pd.DataFrame()
    held_rank1 = rank1[rank1["Ticker"].isin(held_tickers)] if not rank1.empty else pd.DataFrame()

    cash_pct = (cash_val / total_val) * 100 if total_val > 0 else 0

    pieces = []
    pieces.append("Fox Valley Tactical Intelligence – Daily Overlay")
    pieces.append(f"- Portfolio value: ${total_val:,.2f}")
    pieces.append(f"- Cash on hand (SPAXX): ${cash_val:,.2f} ({cash_pct:.2f}%)")

    if not rank1.empty:
        pieces.append(f"- Zacks Rank #1 symbols detected today: {len(rank1)}")
    else:
        pieces.append("- No Zacks Rank #1 symbols detected in today’s screens.")

    if not new_rank1.empty:
        pieces.append(f"- New #1 candidates NOT YET HELD: {len(new_rank1)} → PRIORITY SCAN")
    else:
        pieces.append("- No new #1s outside current holdings.")

    if not held_rank1.empty:
        pieces.append(f"- Held positions still at #1: {len(held_rank1)} → MAINTAIN / MONITOR")
    else:
        pieces.append("- None of the current holdings are at Zacks #1 today.")

    if cash_pct < 5:
        pieces.append("⚠️ Cash is tight — avoid overcommitting unless signal is very strong.")
    elif cash_pct > 25:
        pieces.append("🟡 Cash elevated — consider deploying into top new #1s or defensive dividends.")
    else:
        pieces.append("🟢 Cash in tactical range — standard buy/trims can be executed.")

    narrative = "\n".join(pieces)

    return {
        "narrative": narrative,
        "combined": combined,
        "new_rank1": new_rank1,
        "held_rank1": held_rank1,
        "cash_pct": cash_pct
    }

intel = build_intel_overlay(portfolio, g1, g2, dd, cash_value, total_value)

# ---------- MAIN TABS ----------
tabs = st.tabs([
    "💼 Portfolio Overview",
    "📊 Growth 1",
    "📊 Growth 2",
    "💰 Defensive Dividend",
    "🧩 Tactical Summary",
    "📖 Daily Intelligence Brief"
])

# --- Portfolio Overview ---
with tabs[0]:
    st.subheader("Qualified Plan Holdings")
    st.dataframe(portfolio, use_container_width=True)

    if not portfolio.empty:
        fig = px.pie(
            portfolio,
            values="Value",
            names="Ticker",
            title="Portfolio Allocation",
            hole=0.3
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No portfolio data found in /data/portfolio_data.csv")

# --- Growth 1 ---
with tabs[1]:
    st.subheader("Zacks Growth 1 Cross-Match")
    if not g1.empty:
        g1m = cross_match(g1, portfolio)
        st.dataframe(
            g1m.style.map(
                lambda v: "background-color: #004d00" if str(v) == "1"
                else "background-color: #665c00" if str(v) == "2"
                else "background-color: #663300" if str(v) == "3"
                else "",
                subset=["Zacks Rank"]
            ),
            use_container_width=True
        )
    else:
        st.info("No valid Zacks Growth 1 data detected.")

# --- Growth 2 ---
with tabs[2]:
    st.subheader("Zacks Growth 2 Cross-Match")
    if not g2.empty:
        g2m = cross_match(g2, portfolio)
        st.dataframe(
            g2m.style.map(
                lambda v: "background-color: #004d00" if str(v) == "1"
                else "background-color: #665c00" if str(v) == "2"
                else "background-color: #663300" if str(v) == "3"
                else "",
                subset=["Zacks Rank"]
            ),
            use_container_width=True
        )
    else:
        st.info("No valid Zacks Growth 2 data detected.")

# --- Defensive Dividend ---
with tabs[3]:
    st.subheader("Zacks Defensive Dividend Cross-Match")
    if not dd.empty:
        ddm = cross_match(dd, portfolio)
        st.dataframe(
            ddm.style.map(
                lambda v: "background-color: #004d00" if str(v) == "1"
                else "background-color: #665c00" if str(v) == "2"
                else "background-color: #663300" if str(v) == "3"
                else "",
                subset=["Zacks Rank"]
            ),
            use_container_width=True
        )
    else:
        st.info("No valid Zacks Defensive Dividend data detected.")

# --- Daily Intelligence Brief ---
with tabs[5]:
    st.subheader("📖 Fox Valley Daily Intelligence Brief")
    st.markdown("#### 🧠 AI Tactical Narrative")
    st.markdown(f"```text\n{intel['narrative']}\n```")
    now = datetime.datetime.now().strftime("%A, %B %d, %Y – %I:%M %p CST")
    st.caption(f"Generated: {now}")

    st.markdown("### 🟢 New Zacks Rank #1 Candidates (Not Currently Held)")
    if not intel["new_rank1"].empty:
        st.dataframe(intel["new_rank1"], use_container_width=True)
    else:
        st.info("No NEW Rank #1 candidates outside current holdings today.")

    st.markdown("### ✔ Held Positions Still Zacks #1")
    if not intel["held_rank1"].empty:
        st.dataframe(intel["held_rank1"], use_container_width=True)
    else:
        st.info("None of the current holdings are Rank #1 in today’s screens.")

    st.markdown("### 📋 Full Combined Zacks View (Growth1 + Growth2 + Defensive)")
    if not intel["combined"].empty:
        st.dataframe(intel["combined"], use_container_width=True)
    else:
        st.info("Upload new Zacks files to populate this view.")

# --- Automated Tactical Summary File Generation ---
def generate_tactical_summary():
    now = datetime.datetime.now()
    fname = f"data/tactical_summary_{now.strftime('%Y-%m-%d')}.md"
    try:
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"# Fox Valley Tactical Summary – {now:%B %d, %Y}\n")
            f.write(f"**Total Value:** ${total_value:,.2f}\n")
            f.write(f"**Cash:** ${cash_value:,.2f}\n\n")
            f.write("## Tactical Intelligence\n")
            f.write(intel["narrative"])
            f.write("\n\n## Notes\n")
            f.write("- Generated automatically by Fox Valley Tactical Dashboard v4.1\n")
        st.success(f"Tactical summary exported → {fname}")
    except Exception as e:
        st.error(f"Failed to write tactical summary: {e}")

# --- Auto-Run at 06:45 AM Daily ---
now = datetime.datetime.now()
if now.hour == 6 and 45 <= now.minute < 55:
    generate_tactical_summary()
