import os
import pandas as pd
from tabulate import tabulate
from datetime import datetime

# Module imports (already committed)
from modules.tactical_scoring_engine import apply_tactical_rules
from modules.risk_and_reporting_engine import apply_stop_logic, export_to_csv, export_to_pdf
from modules.profit_risk_analyzer import evaluate_profit_risk  # NEW MODULE INTEGRATION

DATA_PATH = "data"


def load_most_recent_file(keyword: str):
    """Return the most recent CSV file in /data containing a keyword."""
    if not os.path.isdir(DATA_PATH):
        print(f"⚠ Data folder not found: {DATA_PATH}")
        return None

    files = [
        f for f in os.listdir(DATA_PATH)
        if keyword.lower() in f.lower() and f.lower().endswith(".csv")
    ]
    if not files:
        return None

    files.sort()
    latest = files[-1]
    return os.path.join(DATA_PATH, latest)


def load_portfolio():
    """Load latest portfolio CSV."""
    path = load_most_recent_file("Portfolio")
    if not path:
        print("⚠ No portfolio file found in /data.")
        return None

    print(f"\n🗂 Loading Portfolio File: {os.path.basename(path)}")
    try:
        df = pd.read_csv(path)
        df['Ticker'] = df['Ticker'].astype(str).str.upper()
        return df
    except Exception as e:
        print(f"⚠ Error loading portfolio file: {e}")
        return None


def load_zacks_files():
    """Load latest Zacks screens for Growth and Defensive groups."""
    categories = ["Growth", "Defensive"]
    loaded = {}

    for cat in categories:
        path = load_most_recent_file(cat)
        if path:
            print(f"📥 Loaded Zacks File: {os.path.basename(path)}")
            try:
                zdf = pd.read_csv(path)
                zdf['Ticker'] = zdf['Ticker'].astype(str).str.upper()
                loaded[cat] = zdf
            except Exception as e:
                print(f"⚠ Error loading {path}: {e}")

    if not loaded:
        print("\n⚠ No Zacks screening files found in /data.")
    return loaded


def show_portfolio_summary(df: pd.DataFrame):
    """Show high-level portfolio metrics."""
    if df is None or df.empty:
        print("⚠ No portfolio data to analyze.")
        return

    cols = [c for c in ["Ticker", "Quantity", "Last Price", "Current Value", "Total Gain/Loss Percent"] if c in df.columns]

    print("\n📊 Portfolio Holdings Overview")
    print(tabulate(df[cols].head(20), headers="keys", tablefmt="github", floatfmt=".2f"))

    if "Current Value" in df.columns:
        total_value = df["Current Value"].sum()
        print(f"\n💰 Estimated Total Portfolio Value: ${total_value:,.2f}")


def crossmatch_with_zacks(portfolio_df: pd.DataFrame, zacks_data: dict):
    """Match tickers across Zacks screens and apply tactical logic."""
    if portfolio_df is None or portfolio_df.empty:
        print("\n⚠ No portfolio data available for tactical analysis.")
        return None

    if not zacks_data:
        print("\n⚠ No Zacks datasets available for tactical crossmatch.")
        return None

    all_matches = []

    for category, zdf in zacks_data.items():
        if "Ticker" not in zdf.columns:
            continue

        merged = pd.merge(portfolio_df, zdf, on="Ticker", how="inner", suffixes=("", "_z"))
        if not merged.empty:
            merged["Screen Category"] = category
            all_matches.append(merged)

    if not all_matches:
        print("\n📭 No matches from Zacks screens.")
        return None

    result = pd.concat(all_matches, ignore_index=True)

    # Apply tactical logic: Rank + Stop loss controls
    result = apply_tactical_rules(result)
    result = apply_stop_logic(result)

    display_cols = [
        "Ticker", "Quantity", "Current Value", "Zacks Rank",
        "Action", "Screen Category", "Stop Recommendation"
    ]
    display_cols = [c for c in display_cols if c in result.columns]

    print("\n🛡 Tactical Intelligence Output — Actionable Orders")
    print(tabulate(result[display_cols], headers="keys", tablefmt="github", floatfmt=".2f"))

    export_to_csv(result)
    export_to_pdf(result)

    return result


def main():
    print("\n🧭 Fox Valley Intelligence Engine — Tactical Console (CLI Edition)")
    print("==================================================================\n")
    print(f"Run Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Load core data
    portfolio_df = load_portfolio()
    zacks_files = load_zacks_files()

    # Display portfolio insights
    show_portfolio_summary(portfolio_df)

    # Tactical crossmatch
    tactical_df = crossmatch_with_zacks(portfolio_df, zacks_files)

    # Profit & Risk Module
    if tactical_df is not None:
        evaluate_profit_risk(tactical_df)

    print("\n🚀 Engine Execution Complete — Final Assembly Online.")
    print("📁 Reports exported: tactical_intelligence_report.csv & .pdf")
    print("📈 Profit-Risk analyzer executed successfully.\n")


if __name__ == "__main__":
    main()
