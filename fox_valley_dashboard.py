# ============================================
# FOX VALLEY INTELLIGENCE ENGINE v6.2 – Nov 2025
# Pre-Launch Execution Protocol (Apollo Build, Dark Mode)
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re
import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Fox Valley Intelligence Engine v6.2 – Pre-Launch Execution Protocol",
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
        .footer {color: #888; font-size: 0.8em; text-align: center; margin-top: 40px;}
        button {border-radius: 10px !important;}
    </style>
""", unsafe_allow_html=True)

FOOTER_HTML = (
    "<div class='footer'>Fox Valley Intelligence Engine v6.2 – "
    "Pre-Launch Execution Protocol (Apollo Build)</div>"
)

# =====================================================
# 1. PORTFOLIO LOADING & CORRECTIONS (MRMD/KE/IPG, HSBC)
# =====================================================

@st.cache_data
def load_portfolio() -> pd.DataFrame:
    df = pd.read_csv("data/portfolio_data.csv")
    if "GainLoss%" in df.columns:
        df["GainLoss%"] = pd.to_numeric(df["GainLoss%"], errors="coerce")
    if "Value" in df.columns:
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    return df


portfolio = load_portfolio().copy()

# Remove fully exited tickers
sold_tickers = ["MRMD", "KE", "IPG"]
if "Ticker" in portfolio.columns:
    portfolio = portfolio[~portfolio["Ticker"].isin(sold_tickers)].copy()

# Add HSBC if not present (70 @ 70.41) – defensive safety net
if "Ticker" in portfolio.columns:
    tickers_str = portfolio["Ticker"].astype(str).tolist()
    if "HSBC" not in tickers_str:
        hsbc_row = {
            "Ticker": "HSBC",
            "Value": 70 * 70.41,
            "GainLoss%": 0.0,
        }
        for col in portfolio.columns:
            if col not in hsbc_row:
                hsbc_row[col] = None
        portfolio = pd.concat([portfolio, pd.DataFrame([hsbc_row])], ignore_index=True)

if "Value" in portfolio.columns:
    total_value = portfolio["Value"].sum()
else:
    total_value = 0.0

if "Ticker" in portfolio.columns and "Value" in portfolio.columns:
    cash_rows = portfolio[portfolio["Ticker"].astype(str).str.contains("SPAXX", na=False)]
    cash_value = cash_rows["Value"].sum()
else:
    cash_value = 0.0

cash_pct = (cash_value / total_value) * 100 if total_value > 0 else 0.0

# =====================================================
# 2. ZACKS FILE DISCOVERY – CURRENT & PREVIOUS SESSIONS
# =====================================================

def _sorted_zacks_files(pattern: str) -> list[Path]:
    """Return Zacks CSV files in /data sorted by date parsed from filename."""
    files = list(Path("data").glob(pattern))
    date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
    dated = []
    for f in files:
        m = date_pattern.search(f.name)
        if m:
            dated.append((m.group(1), f))
    dated.sort()  # ascending by date string
    return [p for _, p in dated]


def latest_and_previous(patterns: list[str]) -> tuple[str | None, str | None]:
    """Given a list of glob patterns, return (latest, previous) path strings."""
    all_paths: list[Path] = []
    for pat in patterns:
        all_paths.extend(_sorted_zacks_files(pat))
    # remove duplicates
    all_paths = sorted(set(all_paths))
    if not all_paths:
        return None, None
    latest = str(all_paths[-1])
    prev = str(all_paths[-2]) if len(all_paths) > 1 else None
    return latest, prev


G1_CUR, G1_PREV = latest_and_previous(["*Growth 1*.csv", "*Growth1*.csv"])
G2_CUR, G2_PREV = latest_and_previous(["*Growth 2*.csv", "*Growth2*.csv"])
DD_CUR, DD_PREV = latest_and_previous(["*Defensive*.csv", "*Dividend*.csv"])


def safe_read(path: str | None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


g1_raw_cur = safe_read(G1_CUR)
g2_raw_cur = safe_read(G2_CUR)
dd_raw_cur = safe_read(DD_CUR)

g1_raw_prev = safe_read(G1_PREV)
g2_raw_prev = safe_read(G2_PREV)
dd_raw_prev = safe_read(DD_PREV)

if not g1_raw_cur.empty or not g2_raw_cur.empty or not dd_raw_cur.empty:
    st.sidebar.success("✅ Latest Zacks files auto-detected from /data")
else:
    st.sidebar.error("⚠️ No valid Zacks CSVs found in /data folder.")

# =====================================================
# 3. NORMALIZATION & GROUP TAGGING
# =====================================================

def normalize_zacks(df: pd.DataFrame, group: str) -> pd.DataFrame:
    """Normalize a Zacks CSV to Ticker + Zacks Rank + Group."""
    if df.empty:
        return pd.DataFrame(columns=["Ticker", "Zacks Rank", "Group"])
    df = df.copy()
    ticker_cols = [c for c in df.columns if "ticker" in c.lower() or "symbol" in c.lower()]
    if ticker_cols:
        df.rename(columns={ticker_cols[0]: "Ticker"}, inplace=True)
    if "Zacks Rank" not in df.columns:
        rank_cols = [c for c in df.columns if "rank" in c.lower()]
        if rank_cols:
            df.rename(columns={rank_cols[0]: "Zacks Rank"}, inplace=True)
    keep = [c for c in ["Ticker", "Zacks Rank"] if c in df.columns]
    if not keep:
        return pd.DataFrame(columns=["Ticker", "Zacks Rank", "Group"])
    out = df[keep].copy()
    out["Group"] = group
    return out


g1_cur = normalize_zacks(g1_raw_cur, "Growth 1")
g2_cur = normalize_zacks(g2_raw_cur, "Growth 2")
dd_cur = normalize_zacks(dd_raw_cur, "Defensive Dividend")

g1_prev = normalize_zacks(g1_raw_prev, "Growth 1")
g2_prev = normalize_zacks(g2_raw_prev, "Growth 2")
dd_prev = normalize_zacks(dd_raw_prev, "Defensive Dividend")

combined_cur = pd.concat([g1_cur, g2_cur, dd_cur], axis=0, ignore_index=True).drop_duplicates(subset=["Ticker"])
combined_prev = pd.concat([g1_prev, g2_prev, dd_prev], axis=0, ignore_index=True).drop_duplicates(subset=["Ticker"])

# numeric ranks
for df in [combined_cur, combined_prev]:
    if "Zacks Rank" in df.columns:
        df["Zacks Rank"] = pd.to_numeric(df["Zacks Rank"], errors="coerce")

# =====================================================
# 4. CROSS-MATCH & DECISION MATRIX (BUY / HOLD / TRIM)
# =====================================================

def cross_match(zdf: pd.DataFrame, pf: pd.DataFrame) -> pd.DataFrame:
    if zdf.empty or "Ticker" not in zdf.columns or "Ticker" not in pf.columns:
        return pd.DataFrame()
    pf_tickers = pf[["Ticker"]].astype(str)
    zdf = zdf.copy()
    zdf["Ticker"] = zdf["Ticker"].astype(str)
    merged = zdf.merge(pf_tickers, on="Ticker", how="left", indicator=True)
    merged["Held?"] = merged["_merge"].map({"both": "✔ Held", "left_only": "🟢 Candidate"})
    merged.drop(columns=["_merge"], inplace=True)
    return merged


def build_decision_matrix(
    pf: pd.DataFrame,
    combined: pd.DataFrame,
    total_val: float,
    cash_val: float
) -> pd.DataFrame:

    if combined.empty or "Ticker" not in combined.columns:
        return pd.DataFrame()

    dm = combined.copy()
    pf_tickers = set(pf["Ticker"].astype(str).tolist())
    dm["Ticker"] = dm["Ticker"].astype(str)
    dm["Held?"] = dm["Ticker"].apply(lambda t: "✔ Held" if t in pf_tickers else "🟢 Candidate")

    # Suggested stop by group
    def suggested_stop(group: str) -> str:
        if group == "Growth 1":
            return "10%"
        if group == "Growth 2":
            return "10%"
        if group == "Defensive Dividend":
            return "12%"
        return ""

    dm["Suggested Stop %"] = dm["Group"].apply(suggested_stop)

    # Strict action by Zacks Rank
    def action_from_rank(rank) -> str:
        try:
            r = int(rank)
            if r == 1:
                return "🟢 BUY"
            elif r == 2:
                return "⚪ HOLD"
            else:
                return "🟠 TRIM"
        except Exception:
            return ""

    dm["Action"] = dm["Zacks Rank"].apply(action_from_rank)

    # Allocation engine – 15% max per position, 15% cash floor
    rank1 = dm[dm["Zacks Rank"] == 1]
    n_rank1 = len(rank1)
    deployable = total_val * 0.85  # 85% of portfolio (15% cash floor)

    if total_val > 0 and n_rank1 > 0:
        raw_weight = deployable / total_val / n_rank1
        per_pos_weight = min(0.15, raw_weight)
    else:
        per_pos_weight = 0.0

    def alloc_pct(ticker: str) -> float:
        if ticker in rank1["Ticker"].values:
            return per_pos_weight * 100.0
        return 0.0

    dm["Suggested Allocation %"] = dm["Ticker"].apply(alloc_pct)

    def alloc_dollar(pct: float) -> str:
        if pct <= 0 or total_val <= 0:
            return ""
        amt = (pct / 100.0) * total_val
        return f"${amt:,.2f}"

    dm["Estimated Buy Amount"] = dm["Suggested Allocation %"].apply(alloc_dollar)

    return dm


decision_matrix = build_decision_matrix(portfolio, combined_cur, total_value, cash_value)

# =====================================================
# 5. RANK DELTAS – TODAY VS PRIOR SESSION
# =====================================================

def compute_rank_deltas(cur: pd.DataFrame, prev: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (new_rank1, dropped_rank1) across all Zacks screens."""
    if cur.empty or prev.empty or "Ticker" not in cur.columns or "Ticker" not in prev.columns:
        return pd.DataFrame(), pd.DataFrame()

    cur_s = cur[["Ticker", "Zacks Rank", "Group"]].copy()
    prev_s = prev[["Ticker", "Zacks Rank", "Group"]].copy()

    cur_s["Zacks Rank"] = pd.to_numeric(cur_s["Zacks Rank"], errors="coerce")
    prev_s["Zacks Rank"] = pd.to_numeric(prev_s["Zacks Rank"], errors="coerce")

    # Merge by ticker
    merged = cur_s.merge(
        prev_s[["Ticker", "Zacks Rank"]].rename(columns={"Zacks Rank": "Prev Rank"}),
        on="Ticker",
        how="outer"
    )

    # New rank1: current == 1 and (prev != 1 or missing)
    new_rank1 = merged[(merged["Zacks Rank"] == 1) & (merged["Prev Rank"] != 1)]
    dropped_rank1 = merged[(merged["Prev Rank"] == 1) & (merged["Zacks Rank"] != 1)]

    return new_rank1, dropped_rank1


new_rank1, dropped_rank1 = compute_rank_deltas(combined_cur, combined_prev)

# =====================================================
# 6. INTELLIGENCE BRIEF & EXECUTION PROTOCOL
# =====================================================

def build_brief(dm: pd.DataFrame, total_val: float, cash_val: float, cash_pct: float) -> str:
    if dm.empty:
        return (
            "Fox Valley Intelligence Engine – Daily Tactical Brief\n"
            f"- Portfolio Value: ${total_val:,.2f}\n"
            f"- Cash: ${cash_val:,.2f} ({cash_pct:.2f}%)\n"
            "- No active Zacks signals detected in the latest screens.\n"
        )

    buys = dm[dm["Action"].str.contains("BUY", na=False)]
    holds = dm[dm["Action"].str.contains("HOLD", na=False)]
    trims = dm[dm["Action"].str.contains("TRIM", na=False)]

    lines = [
        "Fox Valley Intelligence Engine – Daily Tactical Brief",
        f"- Portfolio Value: ${total_val:,.2f}",
        f"- Cash: ${cash_val:,.2f} ({cash_pct:.2f}%)",
        f"- BUY signals: {len(buys)} | HOLD: {len(holds)} | TRIM: {len(trims)}",
    ]

    if cash_pct < 5:
        lines.append("⚠️ Cash is tight — only the strongest Rank #1 candidates should be considered.")
    elif cash_pct > 25:
        lines.append("🟡 Cash is elevated — you can scale into select Rank #1 names.")
    else:
        lines.append("🟢 Cash is in tactical range — standard buy/trim discipline applies.")

    if not buys.empty:
        buy_list = ", ".join(buys["Ticker"].astype(str).tolist())
        lines.append(f"Primary BUY focus list (Rank #1): {buy_list}")
    else:
        lines.append("No Rank #1 BUY signals today.")

    # Delta narrative
    if not new_rank1.empty:
        lines.append(f"↑ New Rank #1 entries vs prior screen: {len(new_rank1)}")
    if not dropped_rank1.empty:
        lines.append(f"↓ Dropped from Rank #1 since prior screen: {len(dropped_rank1)}")

    return "\n".join(lines)


brief_text = build_brief(decision_matrix, total_value, cash_value, cash_pct)

def build_execution_protocol(dm: pd.DataFrame, total_val: float, cash_val: float) -> pd.DataFrame:
    """Builds a trade plan for BUY candidates with priority and allocation."""
    if dm.empty:
        return pd.DataFrame()

    buys = dm[dm["Action"] == "🟢 BUY"].copy()
    if buys.empty:
        return pd.DataFrame()

    # Priority: Growth 1 → Growth 2 → Defensive Dividend
    group_order = {"Growth 1": 1, "Growth 2": 2, "Defensive Dividend": 3}
    buys["GroupPriority"] = buys["Group"].map(group_order).fillna(99)
    buys.sort_values(["GroupPriority", "Ticker"], inplace=True)

    # Compute numeric allocation & dollars
    buys["AllocPct"] = buys["Suggested Allocation %"].astype(float)
    buys["AllocAmount"] = (buys["AllocPct"] / 100.0) * total_val
    buys["AllocAmountStr"] = buys["AllocAmount"].apply(lambda x: f"${x:,.2f}")

    # Sequence index
    buys["Sequence"] = range(1, len(buys) + 1)

    cols = [
        "Sequence",
        "Ticker",
        "Group",
        "Zacks Rank",
        "Suggested Stop %",
        "AllocPct",
        "AllocAmountStr",
    ]
    return buys[cols]


execution_plan = build_execution_protocol(decision_matrix, total_value, cash_value)

# =====================================================
# 7. STREAMLIT TABS – 7 VIEW LAYOUT
# =====================================================

tabs = st.tabs([
    "💼 Portfolio Overview",
    "📊 Growth 1",
    "📊 Growth 2",
    "💰 Defensive Dividend",
    "📈 Decision Matrix",
    "🧩 Tactical Summary",
    "📖 Daily Intelligence Brief"
])

# --- Tab 1: Portfolio Overview ---
with tabs[0]:
    st.subheader("Qualified Plan Holdings")
    st.dataframe(portfolio, use_container_width=True)

    if "Value" in portfolio.columns and "Ticker" in portfolio.columns and not portfolio.empty:
        fig = px.pie(
            portfolio,
            values="Value",
            names="Ticker",
            title="Portfolio Allocation",
            hole=0.3
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(FOOTER_HTML, unsafe_allow_html=True)

# --- Tabs 2–4: Growth 1 / Growth 2 / Defensive Dividend ---
tab_configs = [
    (tabs[1], g1_cur, "Growth 1"),
    (tabs[2], g2_cur, "Growth 2"),
    (tabs[3], dd_cur, "Defensive Dividend"),
]

for tab, df, label in tab_configs:
    with tab:
        st.subheader(f"Zacks {label} Cross-Match")
        if not df.empty:
            cm = cross_match(df, portfolio)
            if not cm.empty and "Zacks Rank" in cm.columns:
                styled = cm.style.map(
                    lambda v: "background-color: #004d00" if str(v) == "1"
                    else "background-color: #665c00" if str(v) == "2"
                    else "background-color: #663300" if str(v) == "3"
                    else "",
                    subset=["Zacks Rank"]
                )
                st.dataframe(styled, use_container_width=True)
            else:
                st.dataframe(cm, use_container_width=True)
        else:
            st.info(f"No valid Zacks {label} data detected.")

        st.markdown(FOOTER_HTML, unsafe_allow_html=True)

# --- Tab 5: Decision Matrix ---
with tabs[4]:
    st.subheader("📈 Tactical Decision Matrix – Auto-Weighted Allocation")

    if not decision_matrix.empty:
        st.dataframe(decision_matrix, use_container_width=True)
        st.markdown(
            "💹 Allocation engine: 15% max per Rank #1 position, with a 15% cash floor."
        )
        if st.button("🚀 Deploy Trade Plan (Simulation Only)"):
            st.success("Trade Plan validated – ready for Fidelity execution window.")
    else:
        st.info("No actionable Zacks data available. Upload latest screens to /data.")

    st.markdown(FOOTER_HTML, unsafe_allow_html=True)

# --- Tab 6: Tactical Summary ---
with tabs[5]:
    st.subheader("🧩 Weekly Tactical Summary")

    st.write(f"Total Value: ${total_value:,.2f}")
    st.write(f"Cash Available: ${cash_value:,.2f} ({cash_pct:.2f}%)")

    if not decision_matrix.empty:
        rank1_only = decision_matrix[decision_matrix["Zacks Rank"] == 1]
        st.markdown("### Active Zacks #1 Candidates")
        st.dataframe(rank1_only, use_container_width=True)
    else:
        st.info("No Rank #1 candidates in the current Zacks screens.")

    st.markdown("### Rank #1 Deltas vs Prior Screen")
    if not new_rank1.empty:
        st.markdown("**↑ New Rank #1 entries:**")
        st.dataframe(new_rank1, use_container_width=True)
    else:
        st.info("No new Rank #1 entries vs prior session.")

    if not dropped_rank1.empty:
        st.markdown("**↓ Dropped from Rank #1:**")
        st.dataframe(dropped_rank1, use_container_width=True)
    else:
        st.info("No drops from Rank #1 vs prior session.")

    st.markdown(FOOTER_HTML, unsafe_allow_html=True)

# --- Tab 7: Daily Intelligence Brief (with Execution Protocol) ---
with tabs[6]:
    st.subheader("📖 Fox Valley Daily Intelligence Brief")

    now_str = datetime.datetime.now().strftime("%A, %B %d, %Y – %I:%M %p CST")
    st.caption(f"Generated: {now_str}")

    st.markdown("#### 🧠 Tactical Narrative")
    st.markdown("```text\n" + brief_text + "\n```")

    st.markdown("### 🚀 Execution Protocol – Pre-Launch Trade Plan")
    if not execution_plan.empty:
        # Rename for cleaner display
        ep = execution_plan.rename(
            columns={
                "AllocPct": "Suggested Allocation %",
                "AllocAmountStr": "Estimated Buy Amount"
            }
        )
        st.dataframe(ep, use_container_width=True)

        total_alloc = ep["Suggested Allocation %"].sum()
        total_dollars = ep["Estimated Buy Amount"].replace("[\$,]", "", regex=True)
        total_dollars = pd.to_numeric(total_dollars, errors="coerce").sum()

        st.markdown(
            f"**Total Suggested Allocation to Rank #1s:** {total_alloc:.1f}% of portfolio "
            f"(~${total_dollars:,.2f} in notional buys)."
        )
        st.markdown(
            "✅ Check that this stays within your capital and risk comfort before live execution."
        )
    else:
        st.info("No Rank #1 BUY signals today — no execution plan generated.")

    st.markdown("### 🗂 Decision Matrix Snapshot")
    if not decision_matrix.empty:
        st.dataframe(decision_matrix, use_container_width=True)
    else:
        st.info("Decision Matrix is empty – upload Zacks files to enable signals.")

    st.markdown(FOOTER_HTML, unsafe_allow_html=True)

# (Optional) Tactical summary file writer (silent in background)
def generate_tactical_summary_file():
    now = datetime.datetime.now()
    fname = f"data/tactical_summary_{now.strftime('%Y-%m-%d')}.md"
    try:
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"# Fox Valley Tactical Summary – {now:%B %d, %Y}\n\n")
            f.write(brief_text + "\n\n")
            if not decision_matrix.empty:
                f.write("## Decision Matrix\n\n")
                f.write(decision_matrix.to_markdown(index=False))
    except Exception:
        pass

now = datetime.datetime.now()
if now.hour == 6 and 45 <= now.minute < 55:
    generate_tactical_summary_file()
