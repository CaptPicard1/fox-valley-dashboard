# ============================================
# FOX VALLEY INTELLIGENCE ENGINE v5.5 – Nov 2025
# Zacks Tactical Rank Delta System + Alert Engine + Decision Matrix + Trailing-Stop Journal
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re
import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Fox Valley Intelligence Engine v5.5",
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

# =====================================================
# FILE MAINTENANCE – CLEANUP OLD ZACKS CSVs (> 7 DAYS)
# =====================================================
def cleanup_old_files():
    data_path = Path("data")
    removed = []
    if not data_path.exists():
        return removed
    cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
    for f in data_path.glob("zacks_custom_screen_*.csv"):
        try:
            m = re.search(r"(\d{4}-\d{2}-\d{2})", str(f))
            if m:
                file_date = datetime.datetime.strptime(m.group(1), "%Y-%m-%d")
                if file_date < cutoff:
                    f.unlink()
                    removed.append(f.name)
        except Exception:
            continue
    return removed

purged_files = cleanup_old_files()
last_cleanup = datetime.datetime.now().strftime("%Y-%m-%d %H:%M CST")

# ============================
# LOAD CORE PORTFOLIO DATA
# ============================
@st.cache_data
def load_portfolio():
    df = pd.read_csv("data/portfolio_data.csv")
    df["GainLoss%"] = pd.to_numeric(df["GainLoss%"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    return df

portfolio = load_portfolio()
total_value = portfolio["Value"].sum()
cash_value = portfolio.loc[
    portfolio["Ticker"].str.contains("SPAXX", na=False), "Value"
].sum()

# ==============================
# ZACKS FILE DISCOVERY HELPERS
# ==============================
def get_sorted_zacks(pattern: str):
    files = Path("data").glob(pattern)
    date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
    dated = []
    for f in files:
        m = date_pattern.search(str(f))
        if m:
            dated.append((m.group(1), f))
    return sorted(dated, reverse=True)

def safe_read(path: str | None) -> pd.DataFrame:
    if not path:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    tick = [c for c in df.columns if "ticker" in c.lower() or "symbol" in c.lower()]
    if tick:
        df = df.rename(columns={tick[0]: "Ticker"})
    if "Zacks Rank" not in df.columns:
        ranks = [c for c in df.columns if "rank" in c.lower()]
        if ranks:
            df = df.rename(columns={ranks[0]: "Zacks Rank"})
    keep = [c for c in ["Ticker", "Zacks Rank"] if c in df.columns]
    return df[keep].copy()

# ----------------------------------------
# Detect today + previous Zacks files
# ----------------------------------------
G1_all = get_sorted_zacks("zacks_custom_screen_*Growth1*.csv")
G2_all = get_sorted_zacks("zacks_custom_screen_*Growth2*.csv")
DD_all = get_sorted_zacks("zacks_custom_screen_*Defensive*.csv")

def pick_latest(files):
    return str(files[0][1]) if files else None

def pick_prev(files):
    return str(files[1][1]) if len(files) > 1 else None

G1 = pick_latest(G1_all)
G2 = pick_latest(G2_all)
DD = pick_latest(DD_all)

G1_prev = pick_prev(G1_all)
G2_prev = pick_prev(G2_all)
DD_prev = pick_prev(DD_all)

g1_raw = safe_read(G1)
g2_raw = safe_read(G2)
dd_raw = safe_read(DD)

g1_prev_raw = safe_read(G1_prev)
g2_prev_raw = safe_read(G2_prev)
dd_prev_raw = safe_read(DD_prev)

g1 = normalize(g1_raw)
g2 = normalize(g2_raw)
dd = normalize(dd_raw)
g1_prev = normalize(g1_prev_raw)
g2_prev = normalize(g2_prev_raw)
dd_prev = normalize(dd_prev_raw)

# Sidebar status
if any(not x.empty for x in [g1, g2, dd]):
    st.sidebar.success("✅ Latest Zacks screens auto-loaded from /data")
else:
    st.sidebar.error("⚠️ No valid Zacks CSVs found in /data folder.")

# =======================
# INTELLIGENCE ENGINE
# =======================
def build_intel(pf, g1, g2, dd, cash, total):
    combined = pd.concat([g1, g2, dd], axis=0, ignore_index=True).drop_duplicates(subset=["Ticker"])
    held = set(pf["Ticker"].astype(str))
    if "Zacks Rank" in combined.columns:
        combined["Zacks Rank"] = pd.to_numeric(combined["Zacks Rank"], errors="coerce")
        rank1 = combined[combined["Zacks Rank"] == 1]
    else:
        rank1 = pd.DataFrame()

    new = rank1[~rank1["Ticker"].isin(held)] if not rank1.empty else pd.DataFrame()
    kept = rank1[rank1["Ticker"].isin(held)] if not rank1.empty else pd.DataFrame()

    cash_pct = (cash / total) * 100 if total > 0 else 0

    narrative = [
        f"🧭 Fox Valley Tactical Brief – {datetime.datetime.now():%B %d, %Y}",
        f"Portfolio: ${total:,.2f} | Cash: ${cash:,.2f} ({cash_pct:.2f}%)",
        f"Detected Zacks Rank #1 tickers: {len(rank1)}",
        f"New Rank #1 candidates (not held): {len(new)}",
        f"Held Rank #1 positions: {len(kept)}"
    ]

    if cash_pct < 5:
        narrative.append("⚠️ Liquidity tight – prioritize profit-taking or defensive posture.")
    elif cash_pct > 25:
        narrative.append("🟡 Cash elevated – window open to redeploy into high-conviction #1s.")
    else:
        narrative.append("🟢 Cash within tactical band – standard buy/trim playbook active.")

    return {
        "combined": combined,
        "rank1": rank1,
        "new": new,
        "kept": kept,
        "cash_pct": cash_pct,
        "narrative": "\n".join(narrative)
    }

intel = build_intel(portfolio, g1, g2, dd, cash_value, total_value)

# ======================
# ALERT ENGINE (v5.3+)
# ======================
def detect_alerts(today_df, prev_df, label):
    if today_df.empty or prev_df.empty:
        return (pd.DataFrame(),) * 4
    if "Zacks Rank" not in today_df.columns or "Zacks Rank" not in prev_df.columns:
        return (pd.DataFrame(),) * 4

    merged = pd.merge(
        prev_df, today_df,
        on="Ticker", how="outer",
        suffixes=("_prev", "_today"),
        indicator=True
    )

    upgrades = merged[
        (merged["_merge"] == "both") &
        (merged["Zacks Rank_prev"] > merged["Zacks Rank_today"])
    ]
    downgrades = merged[
        (merged["_merge"] == "both") &
        (merged["Zacks Rank_prev"] < merged["Zacks Rank_today"])
    ]
    new = merged[merged["_merge"] == "right_only"]
    removed = merged[merged["_merge"] == "left_only"]

    for df in (upgrades, downgrades, new, removed):
        if not df.empty:
            df["Screen"] = label

    return upgrades, downgrades, new, removed

up1, down1, new1, rem1 = detect_alerts(g1, g1_prev, "Growth1")
up2, down2, new2, rem2 = detect_alerts(g2, g2_prev, "Growth2")
up3, down3, new3, rem3 = detect_alerts(dd, dd_prev, "Defensive")

up_all = pd.concat([up1, up2, up3], ignore_index=True) if any(
    not x.empty for x in [up1, up2, up3]
) else pd.DataFrame()
down_all = pd.concat([down1, down2, down3], ignore_index=True) if any(
    not x.empty for x in [down1, down2, down3]
) else pd.DataFrame()
new_all = pd.concat([new1, new2, new3], ignore_index=True) if any(
    not x.empty for x in [new1, new2, new3]
) else pd.DataFrame()
rem_all = pd.concat([rem1, rem2, rem3], ignore_index=True) if any(
    not x.empty for x in [rem1, rem2, rem3]
) else pd.DataFrame()

alert_log_path = Path("data/alerts_log.csv")
def log_alerts():
    if all(df.empty for df in [up_all, down_all, new_all, rem_all]):
        return None
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    combined = pd.concat(
        [df for df in [up_all, down_all, new_all, rem_all] if not df.empty],
        ignore_index=True
    )
    combined["Timestamp"] = now_str
    if alert_log_path.exists():
        old = pd.read_csv(alert_log_path)
        combined = pd.concat([old, combined], ignore_index=True)
    combined.to_csv(alert_log_path, index=False)
    return combined

alert_df = log_alerts()

# =========================
# ROI TRACKER (v5.x Core)
# =========================
def log_roi():
    path = Path("data/roi_history.csv")
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    roi = float(portfolio["GainLoss%"].mean()) if "GainLoss%" in portfolio.columns else 0.0
    new_row = pd.DataFrame([[now, total_value, cash_value, roi]],
                           columns=["Date", "Value", "Cash", "ROI"])
    if path.exists():
        df = pd.read_csv(path)
        df = pd.concat([df, new_row], ignore_index=True).drop_duplicates(
            subset=["Date"], keep="last"
        )
    else:
        df = new_row
    df.to_csv(path, index=False)
    return df

roi_df = log_roi()

# ==========================================
# TRAILING STOP JOURNAL & CASH RECONCILIATION
# ==========================================
def process_trailing_stops(portfolio_df):
    path = Path("data/trailing_stop_log.csv")
    # If log exists, load previous
    if path.exists():
        log_df = pd.read_csv(path)
    else:
        log_df = pd.DataFrame(columns=["Date","Ticker","Action","Change%","Proceeds"])
    new_entries = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for idx, row in portfolio_df.iterrows():
        if row["Value"] == 0 and row["Ticker"] not in log_df["Ticker"].tolist():
            # full exit
            new_entries.append({
                "Date": now,
                "Ticker": row["Ticker"],
                "Action": "EXIT FULL",
                "Change%": None,
                "Proceeds": 0  # should be input manually or integrate with broker API
            })
        # partial trims logic trigger if needed
        # custom logic to detect partial – user must flag or manual update
    if new_entries:
        new_df = pd.DataFrame(new_entries)
        combined = pd.concat([log_df, new_df], ignore_index=True)
        combined.to_csv(path, index=False)
        return new_df
    return None

new_trailing = process_trailing_stops(portfolio)

# ==========================================
# TACTICAL DECISION MATRIX (v5.4+)
# ==========================================
def build_decision_matrix(pf, intel):
    combined = intel["combined"]
    if combined.empty:
        return pd.DataFrame()

    df = combined.copy()
    df["Ticker"] = df["Ticker"].astype(str)
    df["Zacks Rank"] = pd.to_numeric(df["Zacks Rank"], errors="coerce")

    pf2 = pf[["Ticker", "GainLoss%", "Value"]].copy()
    pf2["Ticker"] = pf2["Ticker"].astype(str)
    df = df.merge(pf2, on="Ticker", how="left")

    df["Held?"] = df["Value"].notna()

    def score_row(row):
        rank = row["Zacks Rank"]
        held = row["Held?"]
        gain = row.get("GainLoss%", None)

        base = 40
        action = "LOW PRIORITY"
        bucket = "LOW"

        if rank == 1 and not held:
            base = 95
            action = "BUY candidate"
            bucket = "BUY"
        elif rank == 1 and held:
            if gain is not None and gain >= 25:
                base = 80
                action = "CONSIDER TRIM / REBALANCE"
                bucket = "TRIM"
            else:
                base = 85
                action = "HOLD / ACCUMULATE"
                bucket = "HOLD"
        elif rank == 2:
            if held:
                base = 70
                action = "HOLD / MONITOR"
                bucket = "HOLD"
            else:
                base = 65
                action = "SECONDARY WATCHLIST"
                bucket = "WATCH"
        else:
            if held and gain is not None:
                if gain < -15:
                    base = 55
                    action = "UNDER REVIEW (RISK)"
                    bucket = "RISK"
                elif gain > 30:
                    base = 60
                    action = "TRIM PROFITS"
                    bucket = "TRIM"

        return pd.Series({
            "Score": int(base),
            "Tactical Action": action,
            "Bucket": bucket
        })

    scored = df.apply(score_row, axis=1)
    df = pd.concat([df, scored], axis=1)

    # Add Suggested Stop % column
    def suggested_stop(rank):
        if rank == 1:
            # candidate whether held or not – use 10% for both Growth1 & Growth2
            return "10%"
        # default for others (defensive / higher risk)
        return "12%"

    df["Suggested Stop %"] = df["Zacks Rank"].apply(suggested_stop)

    df = df.sort_values("Score", ascending=False)
    cols = [
        "Ticker",
        "Zacks Rank",
        "Held?",
        "GainLoss%",
        "Value",
        "Score",
        "Suggested Stop %",
        "Tactical Action",
        "Bucket"
    ]
    return df[cols]

decision_matrix = build_decision_matrix(portfolio, intel)

# ==========================================
# DAILY BRIEF EXPORT
# ==========================================
def export_brief():
    now = datetime.datetime.now()
    fname = Path(f"data/tactical_brief_{now:%Y-%m-%d}.md")
    top_buys = decision_matrix[decision_matrix["Bucket"] == "BUY"].head(5) \
        if not decision_matrix.empty else pd.DataFrame()
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"# Fox Valley Daily Intelligence Brief – {now:%B %d, %Y}\n\n")
        f.write(intel["narrative"])
        f.write("\n\n## Top BUY Candidates (Scored)\n")
        if not top_buys.empty:
            f.write(top_buys.to_string(index=False))
        else:
            f.write("No BUY candidates identified by the matrix today.\n")
        f.write("\n\n## ROI Snapshot\n")
        f.write(roi_df.tail(1).to_string(index=False))
        f.write("\n")

# Auto-run daily export between 06:45–06:55 CST
now = datetime.datetime.now()
if now.hour == 6 and 45 <= now.minute < 55:
    export_brief()

# ============================================
# DASHBOARD – MAIN LAYOUT
# ============================================
tabs = st.tabs([
    "🚨 Tactical Alert Engine",
    "📂 Data Integrity Report",
    "💼 Portfolio",
    "📊 Growth 1",
    "📊 Growth 2",
    "💰 Defensive Dividend",
    "🧩 Tactical Summary",
    "🎯 Tactical Decision Matrix",
    "📘 Trailing Stop Journal",
    "📈 ROI Tracker"
])

# ---------- ALERT TAB ----------
with tabs[0]:
    st.subheader("🚨 Zacks Tactical Alert Engine – Day-to-Day Delta")
    if all(df.empty for df in [up_all, down_all, new_all, rem_all]):
        st.info("No detectable changes between the last two trading sessions.")
    else:
        if not up_all.empty:
            st.markdown("### 🔺 Upgrades (Improved Zacks Rank)")
            st.dataframe(
                up_all[["Ticker", "Zacks Rank_prev", "Zacks Rank_today", "Screen"]],
                use_container_width=True
            )
        if not down_all.empty:
            st.markdown("### 🔻 Downgrades (Weakened Zacks Rank)")
            st.dataframe(
                down_all[["Ticker", "Zacks Rank_prev", "Zacks Rank_today", "Screen"]],
                use_container_width=True
            )
        if not new_all.empty:
            st.markdown("### 🆕 New Entrants")
            st.dataframe(new_all[["Ticker","Screen"]], use_container_width=True)
        if not rem_all.empty:
            st.markdown("### ❌ Removals (No Longer Listed)")
            st.dataframe(rem_all[["Ticker","Screen"]], use_container_width=True)

# ---------- DATA INTEGRITY TAB ----------
with tabs[1]:
    st.subheader("📂 Data Integrity Report – Pre-Flight Check")
    st.markdown(f"**Last Cleanup:** {last_cleanup}")
    if purged_files:
        st.markdown("🧹 Removed old files: " + ", ".join(purged_files))
    else:
        st.markdown("✅ No files required cleanup today.")

    integrity_rows = []
    for name, path, df in [
        ("Growth 1", G1, g1),
        ("Growth 2", G2, g2),
        ("Defensive Dividend", DD, dd),
    ]:
        integrity_rows.append({
            "Screen": name,
            "File": Path(path).name if path else "None",
            "Records": len(df),
            "Status": "✅ Loaded" if len(df) > 0 else "❌ Missing/Empty"
        })
    st.dataframe(pd.DataFrame(integrity_rows), use_container_width=True)

# ---------- PORTFOLIO TAB ----------
with tabs[2]:
    st.subheader("💼 Qualified Plan Holdings")
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

# ---------- ZACKS HELPER ----------
def show_zacks(df, label):
    st.subheader(f"Zacks {label} Cross-Match")
    if df.empty:
        st.info(f"No valid Zacks data for {label}.")
        return
    merged = df.merge(portfolio[["Ticker"]], on="Ticker", how="left", indicator=True)
    merged["Held?"] = merged["_merge"].map(
        {"both": "✔ Held", "left_only": "🟢 Candidate"}
    )
    merged.drop(columns=["_merge"], inplace=True)
    merged["Suggested Stop %"] = (
        ["10%"] * len(merged)
        if "Growth" in label else ["12%"] * len(merged)
    )
    st.dataframe(
        merged.style.map(
            lambda v: "background-color:#004d00" if str(v) == "1"
            else "background-color:#665c00" if str(v) == "2"
            else "background-color:#663300" if str(v) == "3"
            else "",
            subset=["Zacks Rank"]
        ),
        use_container_width=True
    )

# ---------- GROWTH / DEFENSIVE TABS ----------
with tabs[3]:
    show_zacks(g1, "Growth 1")

with tabs[4]:
    show_zacks(g2, "Growth 2")

with tabs[5]:
    show_zacks(dd, "Defensive Dividend")

# ---------- TACTICAL SUMMARY TAB ----------
with tabs[6]:
    st.subheader("🧩 Tactical Summary – Executive Narrative")
    st.markdown(f"```text\n{intel['narrative']}\n```")

# ---------- TACTICAL DECISION MATRIX TAB ----------
with tabs[7]:
    st.subheader("🎯 Tactical Decision Matrix – 1–100 Scoring")
    if decision_matrix.empty:
        st.info("No decision matrix available – Zacks data missing.")
    else:
        st.markdown(
            "Sorted by **Score** (1–100). "
            "Focus first on **BUY** bucket with highest scores."
        )
        st.dataframe(decision_matrix.head(50), use_container_width=True)

# ---------- TRAILING STOP JOURNAL TAB ----------
with tabs[8]:
    st.subheader("📘 Trailing Stop Journal – Realized Exits & Proceeds")
    log_path = Path("data/trailing_stop_log.csv")
    if log_path.exists():
        log_df = pd.read_csv(log_path)
        st.dataframe(log_df.sort_values("Date", ascending=False), use_container_width=True)
    else:
        st.info("No trailing stop events recorded yet.")

# ---------- ROI TRACKER TAB ----------
with tabs[9]:
    st.subheader("📈 ROI vs Zacks 26% Annual Benchmark")
    if roi_df.empty:
        st.info("No ROI history yet.")
    else:
        fig = px.line(
            roi_df,
            x="Date",
            y="ROI",
            title="ROI History (Daily Logged)",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
        current = float(roi_df.iloc[-1]["ROI"])
        st.metric("Current ROI", f"{current:.2f}%")
        delta = current - 26.0
        if current >= 26.0:
            st.success(f"🔥 Surpassing Zacks benchmark by {delta:.2f}%")
        else:
            st.warning(f"📉 Trailing benchmark by {abs(delta):.2f}%")
