# ============================================
# FOX VALLEY INTELLIGENCE ENGINE v6.0 – Nov 2025
# Tactical Core Grid System (Strict Zacks Rank Logic)
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re
import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Fox Valley Intelligence Engine v6.0 – Tactical Core Grid",
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
        .buy {background-color:#004d00 !important; color:white;}
        .hold {background-color:#665c00 !important; color:white;}
        .trim {background-color:#663300 !important; color:white;}
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

# Apply latest known changes
sales = ["MRMD", "KE", "IPG"]
portfolio = portfolio[~portfolio["Ticker"].isin(sales)]
new_entry = pd.DataFrame([{"Ticker": "HSBC", "Shares": 70, "CostBasis": 70.41, "Value": 70 * 70.41}])
portfolio = pd.concat([portfolio, new_entry], ignore_index=True)

total_value = portfolio["Value"].sum()
cash_row = portfolio[portfolio["Ticker"].str.contains("SPAXX", na=False)]
cash_value = cash_row["Value"].sum() + 47904.80  # adds post-sale cash
cash_pct = (cash_value / total_value) * 100 if total_value > 0 else 0

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

G1_PATH = get_latest_zacks_file("*Growth*1*.csv")
G2_PATH = get_latest_zacks_file("*Growth*2*.csv")
DD_PATH = get_latest_zacks_file("*Defensive*.csv")

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

if not g1_raw.empty or not g2_raw.empty or not dd_raw.empty:
    st.sidebar.success("✅ Latest Zacks files auto-detected from /data")
else:
    st.sidebar.error("⚠️ No valid Zacks CSVs found in /data folder.")

# ---------- NORMALIZE + COMBINE ----------
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

g1 = normalize_zacks(g1_raw)
g2 = normalize_zacks(g2_raw)
dd = normalize_zacks(dd_raw)

def assign_group(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Ticker", "Zacks Rank", "Group"])
    df["Group"] = label
    return df

g1 = assign_group(g1, "Growth 1")
g2 = assign_group(g2, "Growth 2")
dd = assign_group(dd, "Defensive Dividend")
combined = pd.concat([g1, g2, dd], axis=0, ignore_index=True).drop_duplicates(subset=["Ticker"])

# ---------- DECISION MATRIX ----------
def build_decision_matrix(portfolio_df: pd.DataFrame, zdf: pd.DataFrame):
    pf_tickers = set(portfolio_df["Ticker"].astype(str))
    zdf["Held?"] = zdf["Ticker"].apply(lambda t: "✔ Held" if t in pf_tickers else "🟢 Candidate")

    def get_stop(group):
        if group == "Growth 1": return "10%"
        if group == "Growth 2": return "10%"
        if group == "Defensive Dividend": return "12%"
        return "-"

    zdf["Suggested Stop %"] = zdf["Group"].apply(get_stop)

    def get_action(rank):
        try:
            r = int(rank)
            if r == 1: return "🟢 BUY"
            elif r == 2: return "⚪ HOLD"
            else: return "🟠 TRIM"
        except:
            return ""
    zdf["Action"] = zdf["Zacks Rank"].apply(get_action)

    return zdf[["Ticker", "Zacks Rank", "Group", "Held?", "Suggested Stop %", "Action"]]

decision_matrix = build_decision_matrix(portfolio, combined)

# ---------- INTELLIGENCE BRIEF ----------
def build_brief(matrix: pd.DataFrame, cash_val: float, cash_pct: float) -> str:
    total_buy = len(matrix[matrix["Action"].str.contains("BUY")])
    total_hold = len(matrix[matrix["Action"].str.contains("HOLD")])
    total_trim = len(matrix[matrix["Action"].str.contains("TRIM")])

    lines = [
        "Fox Valley Intelligence Engine – Daily Tactical Brief",
        f"- Portfolio Value: ${total_value:,.2f}",
        f"- Cash: ${cash_val:,.2f} ({cash_pct:.2f}%)",
        f"- BUY signals: {total_buy} | HOLD: {total_hold} | TRIM: {total_trim}"
    ]

    if cash_pct < 5:
        lines.append("⚠️ Low cash — preserve capital.")
    elif cash_pct > 25:
        lines.append("🟡 Cash heavy — deploy tactically.")
    else:
        lines.append("🟢 Cash in optimal tactical range.")
    return "\n".join(lines)

brief_text = build_brief(decision_matrix, cash_value, cash_pct)

# ---------- DISPLAY ----------
tabs = st.tabs([
    "💼 Portfolio Overview",
    "📊 Decision Matrix",
    "📖 Daily Intelligence Brief"
])

# --- Portfolio Overview ---
with tabs[0]:
    st.subheader("Qualified Plan Holdings")
    st.dataframe(portfolio, use_container_width=True)
    if not portfolio.empty:
        fig = px.pie(portfolio, values="Value", names="Ticker",
                     title="Portfolio Allocation", hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

# --- Decision Matrix ---
with tabs[1]:
    st.subheader("Unified Tactical Decision Matrix")
    if not decision_matrix.empty:
        def highlight_action(val):
            if "BUY" in str(val): return "background-color:#004d00; color:white;"
            if "HOLD" in str(val): return "background-color:#665c00; color:white;"
            if "TRIM" in str(val): return "background-color:#663300; color:white;"
            return ""
        st.dataframe(
            decision_matrix.style.map(highlight_action, subset=["Action"]),
            use_container_width=True
        )
    else:
        st.info("No actionable Zacks data found.")

# --- Intelligence Brief ---
with tabs[2]:
    st.subheader("📖 Fox Valley Daily Intelligence Brief")
    st.markdown(f"```text\n{brief_text}\n```")
    st.markdown("### Tactical Summary Insights")
    st.dataframe(decision_matrix, use_container_width=True)

# --- Tactical Summary Generation ---
def generate_tactical_summary():
    now = datetime.datetime.now()
    fname = f"data/tactical_summary_{now.strftime('%Y-%m-%d')}.md"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"# Fox Valley Tactical Summary – {now:%B %d, %Y}\n\n")
        f.write(brief_text + "\n\n")
        f.write("## Decision Matrix\n")
        f.write(decision_matrix.to_markdown(index=False))
    st.success(f"Summary exported → {fname}")

now = datetime.datetime.now()
if now.hour == 6 and 45 <= now.minute < 55:
    generate_tactical_summary()
