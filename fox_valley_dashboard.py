# 🧭 Fox Valley Intelligence Engine v7.3R-3
# Enterprise Command Deck — Final Stable Build (Nov 12 2025)
# -------------------------------------------------------------------
# Purpose:
#   Fully-integrated Streamlit dashboard for portfolio tracking,
#   Zacks Growth 1, Growth 2, Defensive Dividend screens,
#   tactical decision intelligence, Top-8 candidate selection,
#   and daily/weekly summaries.
# -------------------------------------------------------------------

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import io, datetime

# ---------------------------------------------------------------
# 🧩 Streamlit Page Configuration
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Fox Valley Intelligence Engine v7.3R-3",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------
# ⚙️ Utility Functions
# ---------------------------------------------------------------

def archive_old_portfolios(data_path: Path):
    """Move all but newest portfolio CSVs to /archive_ prefix."""
    files = sorted(data_path.glob("Portfolio_Positions_*.csv"), key=lambda f: f.stat().st_mtime)
    if len(files) <= 1:
        return
    newest = files[-1]
    for f in files[:-1]:
        archived = f.parent / f"archive_{f.name}"
        if not archived.exists():
            f.rename(archived)

def load_latest_csv(data_path: Path, pattern: str, label: str):
    """Load the latest matching CSV file and report diagnostics."""
    matches = sorted(data_path.glob(pattern), key=lambda f: f.stat().st_mtime)
    if not matches:
        st.warning(f"⚠️ No {label} files found.")
        return None, None
    latest = matches[-1]
    df = pd.read_csv(latest)
    df = df.dropna(how="all")
    st.write(f"📁 Active {label} File: {latest.name}")
    st.write(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df, latest.name

def detect_cash(df: pd.DataFrame):
    """Detect cash rows (SPAXX/CORE) and compute totals."""
    cash_keywords = ["cash", "spaxx", "core", "money"]
    mask = df.apply(lambda col: col.astype(str).str.lower().str.contains("|".join(cash_keywords), na=False))
    cash_rows = df.loc[mask.any(axis=1)]
    value_cols = [c for c in df.columns if "value" in c.lower()]
    total_value = pd.to_numeric(df[value_cols[0]], errors="coerce").sum() if value_cols else 0.0
    cash_value = pd.to_numeric(cash_rows[value_cols[0]], errors="coerce").sum() if not cash_rows.empty else 0.0
    st.write(f"🔍 Value column used: {value_cols[0] if value_cols else 'None found'}")
    st.write(f"🔍 Estimated total account value: ${total_value:,.2f}")
    st.write(f"🔍 Estimated cash value: ${cash_value:,.2f}")
    return total_value, cash_value

def summarize_zacks(df, label):
    if df is None:
        return ""
    return f"{label}: {len(df)} rows, {len(df.columns)} cols"

def top_candidates(g1, g2, dd):
    combined = pd.concat([g1, g2, dd], ignore_index=True)
    combined = combined.drop_duplicates(subset=["Ticker"], keep="first")
    rank1 = combined[combined["Zacks Rank"].astype(str).str.strip().eq("1")]
    top = rank1.head(8)
    return top

# ---------------------------------------------------------------
# 🚀 Main App
# ---------------------------------------------------------------

def main():
    st.title("🧭 Fox Valley Intelligence Engine – Enterprise Command Deck (v7.3R-3)")
    st.caption("Final Stable Build – November 12 2025 | Diagnostics + Top-8 Analyzer Active")

    data_path = Path("data")
    if not data_path.exists():
        st.error("❌ /data folder not found.")
        return

    archive_old_portfolios(data_path)

    # ---- Load Portfolio
    portfolio, p_name = load_latest_csv(data_path, "Portfolio_Positions_*.csv", "Portfolio")
    if portfolio is not None:
        total_value, cash_value = detect_cash(portfolio)
    else:
        total_value = cash_value = 0.0

    # ---- Load Zacks Screens
    g1, g1_name = load_latest_csv(data_path, "zacks_custom_screen_*Growth 1*.csv", "Zacks Growth 1")
    g2, g2_name = load_latest_csv(data_path, "zacks_custom_screen_*Growth 2*.csv", "Zacks Growth 2")
    dd, dd_name = load_latest_csv(data_path, "zacks_custom_screen_*Defensive Dividends*.csv", "Zacks Defensive Dividends")

    # ---- Diagnostics Console
    with st.expander("🧩 Diagnostic Console", expanded=True):
        if portfolio is not None:
            st.write("Active Portfolio File:", p_name)
            st.write("Portfolio columns:", list(portfolio.columns))
        st.write(summarize_zacks(g1, "Growth 1"))
        st.write(summarize_zacks(g2, "Growth 2"))
        st.write(summarize_zacks(dd, "Defensive Dividends"))

    # ---- Navigation Tabs
    tabs = st.tabs([
        "💼 Portfolio Overview", "📊 Growth 1", "📊 Growth 2",
        "💰 Defensive Dividends", "⚙️ Tactical Matrix",
        "⭐ Top-8 Candidates", "🧩 Weekly Tactical Summary", "📖 Daily Intelligence Brief"
    ])

    # ---- Tab 1 – Portfolio
    with tabs[0]:
        if portfolio is not None:
            st.metric("Total Account Value", f"${total_value:,.2f}")
            st.metric("Cash Available to Trade", f"${cash_value:,.2f}")
            st.dataframe(portfolio)
        else:
            st.warning("No portfolio data available.")

    # ---- Tabs 2-4 – Zacks Screens
    for i, (df, lbl) in enumerate([(g1,"Growth 1"),(g2,"Growth 2"),(dd,"Defensive Dividends")], start=1):
        with tabs[i]:
            if df is not None: st.dataframe(df)
            else: st.warning(f"No {lbl} data loaded.")

    # ---- Tactical Matrix
    with tabs[4]:
        if all(x is not None for x in [g1, g2, dd]):
            combined = pd.concat([g1, g2, dd], ignore_index=True).drop_duplicates(subset=["Ticker"])
            st.dataframe(combined)
        else:
            st.warning("Incomplete data for matrix generation.")

    # ---- Top-8 Candidates
    with tabs[5]:
        if all(x is not None for x in [g1, g2, dd]):
            top8 = top_candidates(g1, g2, dd)
            st.dataframe(top8)
        else:
            st.warning("Cannot generate Top-8 without all Zacks screens.")

    # ---- Weekly Summary + Daily Brief
    now = datetime.datetime.now()
    with tabs[6]:
        st.markdown(f"**Weekly Tactical Summary** – Generated {now:%A, %b %d %Y}")
        st.write(f"Total Holdings in Portfolio: {len(portfolio) if portfolio is not None else 0}")
        st.write(f"Zacks Rank #1 Symbols Detected: {len(pd.concat([g1,g2,dd]).query('`Zacks Rank` == 1')) if all([g1,g2,dd]) else 0}")

    with tabs[7]:
        st.markdown("### Fox Valley Daily Intelligence Brief")
        st.write(f"• Total account value: ${total_value:,.2f}")
        st.write(f"• Cash available (SPAXX / Core): ${cash_value:,.2f}")
        st.write(f"• Generated {now:%A, %B %d, %Y – %I:%M %p}")

if __name__ == "__main__":
    main()
