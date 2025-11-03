# ============================================================
# FOX VALLEY TACTICAL DASHBOARD v4.5-lite – Nov 2025
# Stable Build: Auto Zacks Loader + Daily Intelligence (No Debug Tab)
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re, datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Fox Valley Tactical Dashboard v4.5-lite",
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
    </style>
""", unsafe_allow_html=True)

# ---------- LOAD PORTFOLIO ----------
@st.cache_data
def load_portfolio():
    df = pd.read_csv("data/portfolio_data.csv")
    # normalize types
    for c in ["GainLoss%", "Value"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].astype(str)
    return df

portfolio = load_portfolio()
total_value = portfolio["Value"].sum() if "Value" in portfolio.columns else 0.0
cash_value = 0.0
if not portfolio.empty and "Ticker" in portfolio.columns and "Value" in portfolio.columns:
    cash_rows = portfolio[portfolio["Ticker"].str.contains("SPAXX", na=False)]
    cash_value = cash_rows["Value"].sum()

# ---------- HEADER ----------
st.title("🧭 Fox Valley Tactical Dashboard")
c1, c2 = st.columns(2)
c1.metric("Total Account Value", f"${total_value:,.2f}")
c2.metric("Cash – SPAXX (Money Market)", f"${cash_value:,.2f}")
st.markdown("---")

# ---------- AUTO-DETECT LATEST ZACKS FILES ----------
def latest_by_date(patterns):
    """
    Finds the file with max YYYY-MM-DD in its name among provided glob patterns.
    Supports both underscore and space variations.
    """
    rx = re.compile(r"(\d{4}-\d{2}-\d{2})")
    found = []
    base = Path("data")
    for pat in patterns:
        for p in base.glob(pat):
            m = rx.search(p.name)
            if m:
                found.append((m.group(1), p))
    if not found:
        return None
    found.sort(key=lambda t: t[0])
    return str(found[-1][1])

G1_PATH = latest_by_date(["*Growth1*.csv", "*Growth 1*.csv"])
G2_PATH = latest_by_date(["*Growth2*.csv", "*Growth 2*.csv"])
DD_PATH = latest_by_date(["*DefensiveDividend*.csv", "*Defensive Dividends*.csv"])

def safe_read_csv(path):
    if not path:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

g1_raw = safe_read_csv(G1_PATH)
g2_raw = safe_read_csv(G2_PATH)
dd_raw = safe_read_csv(DD_PATH)

if not g1_raw.empty or not g2_raw.empty or not dd_raw.empty:
    st.sidebar.success("✅ Latest Zacks files auto-detected from /data")
else:
    st.sidebar.error("⚠️ No valid Zacks CSVs found in /data folder.")

# ---------- NORMALIZE & CROSS-MATCH (robust, no Styler) ----------
def normalize_zacks(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    # Find ticker & rank columns flexibly
    tick_col = next((c for c in out.columns if "ticker" in c.lower() or "symbol" in c.lower()), None)
    rank_col = next((c for c in out.columns if "rank" in c.lower()), None)
    res = pd.DataFrame()
    if tick_col is not None:
        res["Ticker"] = out[tick_col].astype(str)
    if rank_col is not None:
        res["Zacks Rank"] = pd.to_numeric(out[rank_col], errors="coerce")
    return res

def cross_match(zdf: pd.DataFrame, pf: pd.DataFrame) -> pd.DataFrame:
    if zdf.empty or pf.empty or "Ticker" not in pf.columns:
        return pd.DataFrame(columns=["Ticker","Zacks Rank","Held?"])
    pf_tk = pf[["Ticker"]].astype(str)
    zdf = zdf.copy()
    zdf["Ticker"] = zdf["Ticker"].astype(str)
    merged = zdf.merge(pf_tk, on="Ticker", how="left", indicator=True)
    merged["Held?"] = merged["_merge"].map({"both":"✔ Held", "left_only":"🟢 Candidate"})
    merged.drop(columns=["_merge"], inplace=True)
    # optional helper label
    merged["RankTag"] = merged["Zacks Rank"].apply(lambda r: "R1" if r==1 else ("R2" if r==2 else ("R3" if r==3 else "")))
    return merged[["Ticker","Zacks Rank","RankTag","Held?"]]

g1 = normalize_zacks(g1_raw)
g2 = normalize_zacks(g2_raw)
dd = normalize_zacks(dd_raw)

# ---------- MAIN TABS (no Debug tab) ----------
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
    if not portfolio.empty:
        st.dataframe(portfolio, use_container_width=True)
        if "Value" in portfolio.columns:
            fig = px.pie(portfolio, values="Value", names="Ticker", title="Portfolio Allocation", hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No portfolio data found in /data/portfolio_data.csv")

# --- Growth 1 ---
with tabs[1]:
    st.subheader("Zacks Growth 1 – Cross-Match")
    g1m = cross_match(g1, portfolio)
    if not g1m.empty:
        st.dataframe(g1m, use_container_width=True)
    else:
        st.info("No valid Zacks Growth 1 data detected.")

# --- Growth 2 ---
with tabs[2]:
    st.subheader("Zacks Growth 2 – Cross-Match")
    g2m = cross_match(g2, portfolio)
    if not g2m.empty:
        st.dataframe(g2m, use_container_width=True)
    else:
        st.info("No valid Zacks Growth 2 data detected.")

# --- Defensive Dividend ---
with tabs[3]:
    st.subheader("Zacks Defensive Dividend – Cross-Match")
    ddm = cross_match(dd, portfolio)
    if not ddm.empty:
        st.dataframe(ddm, use_container_width=True)
    else:
        st.info("No valid Zacks Defensive Dividend data detected.")

# --- Tactical Summary (weekly-style snapshot) ---
with tabs[4]:
    st.subheader("🧩 Weekly Tactical Summary – Zacks Intelligence")
    if not portfolio.empty and "GainLoss%" in portfolio.columns:
        avg_gain = portfolio["GainLoss%"].mean()
        st.metric("Average Gain/Loss %", f"{avg_gain:.2f}%")
    st.metric("Total Value", f"${total_value:,.2f}")
    combined = pd.concat([g1, g2, dd], ignore_index=True).drop_duplicates(subset=["Ticker"])
    if not combined.empty:
        held = combined.merge(portfolio[["Ticker"]], on="Ticker", how="inner")
        new = combined[~combined["Ticker"].isin(portfolio["Ticker"])]
        st.markdown("**🟢 New Zacks Candidates (Not Held)**")
        st.dataframe(new, hide_index=True, use_container_width=True)
        st.markdown("**✔ Held Positions Present in Zacks Universe**")
        st.dataframe(held, hide_index=True, use_container_width=True)
    else:
        st.info("Zacks files not available for summary.")

# --- Daily Intelligence Brief (actionable recs) ---
with tabs[5]:
    st.subheader("📖 Daily Intelligence Brief – Recommendations")
    st.markdown(f"**Date:** {datetime.datetime.now():%A, %B %d, %Y}")
    combined = pd.concat([g1, g2, dd], ignore_index=True).drop_duplicates(subset=["Ticker"])
    if not combined.empty:
        rank1 = combined[combined["Zacks Rank"] == 1]
        held_r1 = rank1.merge(portfolio[["Ticker"]], on="Ticker", how="inner")
        new_r1 = rank1[~rank1["Ticker"].isin(portfolio["Ticker"])]

        # Summary metrics
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("🟢 New Rank #1 Candidates", len(new_r1))
        mc2.metric("✔ Held Rank #1 Positions", len(held_r1))
        mc3.metric("💼 Portfolio Holdings", len(portfolio))

        # Action blocks
        st.markdown("---")
        st.markdown("### 🟢 Potential Buys (New Rank #1, Not Held)")
        if not new_r1.empty:
            st.dataframe(new_r1[["Ticker","Zacks Rank"]], hide_index=True, use_container_width=True)
        else:
            st.info("No new Rank #1 buy candidates today.")

        st.markdown("### 🟠 Review / Trim (Held but Not Rank #1)")
        # Held tickers that are NOT in rank1 list
        held_not_r1 = portfolio[~portfolio["Ticker"].isin(rank1["Ticker"])] if not rank1.empty else portfolio.copy()
        if not held_not_r1.empty:
            show_cols = ["Ticker","Value","GainLoss%"]
            show_cols = [c for c in show_cols if c in held_not_r1.columns]
            st.dataframe(held_not_r1[show_cols], hide_index=True, use_container_width=True)
        else:
            st.info("All held names are currently Rank #1.")

        st.markdown("### ⚪ Hold / Monitor (Held Rank #1)")
        if not held_r1.empty:
            st.dataframe(held_r1[["Ticker","Zacks Rank"]], hide_index=True, use_container_width=True)
        else:
            st.info("No held Rank #1 positions to monitor.")

        # Cash posture
        st.markdown("---")
        cash_pct = (cash_value / total_value * 100) if total_value > 0 else 0
        st.metric("Cash (SPAXX)", f"${cash_value:,.2f}")
        st.metric("Cash % of Account", f"{cash_pct:.2f}%")
        if cash_pct < 5:
            st.warning("⚠️ Low cash — limited buy flexibility.")
        elif cash_pct > 25:
            st.info("🟡 Elevated cash — consider redeployment.")
        else:
            st.success("🟢 Balanced liquidity for tactical flexibility.")

        # Provenance (so you can verify which files were used today)
        st.caption(f"Files used → Growth1: {G1_PATH or '—'} | Growth2: {G2_PATH or '—'} | Defensive: {DD_PATH or '—'}")
    else:
        st.warning("⚠️ Zacks data unavailable. Upload today’s three screens to /data.")

# --- (Optional) Weekly Markdown Export at Sunday 07:00 CST ---
def write_weekly_summary():
    now = datetime.datetime.now()
    fname = f"data/tactical_summary_{now.strftime('%Y-%m-%d')}.md"
    cash_pct = (cash_value / total_value * 100) if total_value > 0 else 0
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"# Fox Valley Tactical Summary – {now:%B %d, %Y}\n\n")
        f.write(f"Total Value: ${total_value:,.2f}\n")
        f.write(f"Cash (SPAXX): ${cash_value:,.2f} ({cash_pct:.2f}%)\n")
        f.write("- 🟢 Buy Rank #1 candidates\n- 🟠 Review non-#1 held\n- ⚪ Maintain liquidity\n")
    st.success(f"Weekly summary exported → {fname}")

now = datetime.datetime.now()
if now.weekday() == 6 and now.hour == 7:
    write_weekly_summary()

st.caption("Fox Valley Tactical Dashboard v4.5-lite – Stable Intelligence Build")
