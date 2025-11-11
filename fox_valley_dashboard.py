# 🧭 Fox Valley Intelligence Engine v7.2R – Enterprise Command Deck
# Final Stable Build (Nov 11, 2025)
# Streamlit Enterprise Portfolio Dashboard – Clean, Fault-Tolerant, Auto-Archiving Build

import streamlit as st
import pandas as pd
import datetime
import shutil
from pathlib import Path

# ------------------------------------------------
# APP CONFIGURATION
# ------------------------------------------------
st.set_page_config(page_title="Fox Valley Intelligence Engine", layout="wide")
st.title("🧭 Fox Valley Intelligence Engine – Enterprise Command Deck (v7.2R)")
st.caption("Final Stable Build – November 11, 2025")

# ------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------
def get_latest(pattern: str):
    files = sorted(Path("data").glob(pattern), key=lambda f: f.stat().st_mtime)
    return files[-1] if files else None


def archive_old_portfolios():
    data_path = Path("data")
    archive_path = Path("archive")
    archive_path.mkdir(exist_ok=True)
    portfolios = sorted(data_path.glob("Portfolio_Positions_*.csv"), key=lambda f: f.stat().st_mtime)
    if len(portfolios) > 1:
        for old_file in portfolios[:-1]:
            dest = archive_path / f"archive_{old_file.name}"
            shutil.move(str(old_file), str(dest))
            st.sidebar.info(f"📦 Archived: {old_file.name}")


def load_portfolio():
    portfolio_file = get_latest("data/Portfolio_Positions_*.csv")
    if not portfolio_file:
        st.error("⚠️ No portfolio files found in /data.")
        return pd.DataFrame(), 0.0, 0.0, None

    st.sidebar.success(f"📁 Active Portfolio File: {portfolio_file.name}")

    df = pd.read_csv(portfolio_file, skiprows=range(15), thousands=",", dtype=str)
    df = df.dropna(how="all")

    # Clean and normalize
    df.columns = [c.strip() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]
    df.replace(r"[\$,]", "", regex=True, inplace=True)

    # Identify and calculate totals
    cash_value = 0.0
    total_value = 0.0
    value_cols = [c for c in df.columns if "value" in c.lower() or "total" in c.lower()]
    for c in value_cols:
        try:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        except:
            pass

    # Detect cash rows
    cash_mask = df.apply(lambda row: row.astype(str).str.contains("CASH|MONEY|MMKT|USD", case=False, na=False)).any(axis=1)
    cash_value = df.loc[cash_mask, value_cols].sum(numeric_only=True).sum()
    total_value = df[value_cols].sum(numeric_only=True).sum()

    # Extract tickers
    if "Symbol" in df.columns:
        df.rename(columns={"Symbol": "Ticker"}, inplace=True)

    return df, total_value, cash_value, portfolio_file


def load_zacks(pattern):
    f = get_latest(pattern)
    if not f:
        return pd.DataFrame()
    df = pd.read_csv(f)
    df.columns = [c.strip() for c in df.columns]
    if "Ticker" not in df.columns:
        possible = [c for c in df.columns if "ticker" in c.lower() or "symbol" in c.lower()]
        if possible:
            df.rename(columns={possible[0]: "Ticker"}, inplace=True)
    if "Zacks Rank" not in df.columns:
        possible = [c for c in df.columns if "rank" in c.lower()]
        if possible:
            df.rename(columns={possible[0]: "Zacks Rank"}, inplace=True)
    return df[["Ticker", "Zacks Rank"]].dropna()


def cross_match(zdf, portfolio):
    if zdf.empty or portfolio.empty:
        return pd.DataFrame()
    return pd.merge(zdf, portfolio, on="Ticker", how="left", indicator=True)


def build_intel(portfolio, g1, g2, dd):
    if portfolio.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    combined = pd.concat([g1, g2, dd], ignore_index=True)
    combined.drop_duplicates(subset=["Ticker"], inplace=True)

    held = portfolio["Ticker"].dropna().tolist()
    rank1 = combined[combined["Zacks Rank"].astype(str).str.strip() == "1"]
    new_candidates = rank1[~rank1["Ticker"].isin(held)]
    held_rank1 = rank1[rank1["Ticker"].isin(held)]

    return new_candidates, held_rank1, combined


# ------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------
archive_old_portfolios()
portfolio, total_value, cash_value, portfolio_file = load_portfolio()
g1 = load_zacks("data/*Growth 1*.csv")
g2 = load_zacks("data/*Growth 2*.csv")
dd = load_zacks("data/*Defensive*.csv")

if not any([g1.empty, g2.empty, dd.empty]):
    st.sidebar.success("✅ Zacks Screens Loaded Successfully")
else:
    st.sidebar.warning("⚠️ One or more Zacks screens not found or empty.")

tabs = st.tabs(["💼 Portfolio Overview", "📊 Growth 1", "📊 Growth 2",
                "💰 Defensive Dividend", "⚙️ Tactical Matrix",
                "🧩 Weekly Tactical Summary", "📖 Daily Brief"])

# --- Portfolio Overview ---
with tabs[0]:
    if not portfolio.empty:
        st.metric("Total Account Value", f"${total_value:,.2f}")
        st.metric("Cash Available to Trade", f"${cash_value:,.2f}")
        st.dataframe(portfolio, use_container_width=True)
    else:
        st.warning("No portfolio data available.")

# --- Growth 1 ---
with tabs[1]:
    g1m = cross_match(g1, portfolio)
    if not g1m.empty:
        st.dataframe(g1m, use_container_width=True)
    else:
        st.info("No Growth 1 matches found.")

# --- Growth 2 ---
with tabs[2]:
    g2m = cross_match(g2, portfolio)
    if not g2m.empty:
        st.dataframe(g2m, use_container_width=True)
    else:
        st.info("No Growth 2 matches found.")

# --- Defensive Dividend ---
with tabs[3]:
    ddm = cross_match(dd, portfolio)
    if not ddm.empty:
        st.dataframe(ddm, use_container_width=True)
    else:
        st.info("No Defensive Dividend matches found.")

# --- Tactical Decision Matrix ---
new_candidates, held_rank1, combined = build_intel(portfolio, g1, g2, dd)
with tabs[4]:
    st.subheader("⚙️ Tactical Decision Matrix")
    if not new_candidates.empty:
        st.success("🟢 New #1 Candidates to Review")
        st.dataframe(new_candidates, use_container_width=True)
    if not held_rank1.empty:
        st.info("⚪ Current Holdings Still #1")
        st.dataframe(held_rank1, use_container_width=True)
    if new_candidates.empty and held_rank1.empty:
        st.warning("No actionable #1 signals today.")

# --- Weekly Tactical Summary ---
with tabs[5]:
    st.subheader("🧩 Weekly Tactical Summary")
    st.write("Auto-generated tactical summary will appear here.")

# --- Daily Intelligence Brief ---
with tabs[6]:
    st.subheader("📖 Fox Valley Daily Intelligence Brief")
    st.write(f"Generated: {datetime.datetime.now():%A, %B %d, %Y – %I:%M %p CST}")
    st.write("Summary of all tactical signals for review.")
