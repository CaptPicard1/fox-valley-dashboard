import os
import pandas as pd
from tabulate import tabulate
from datetime import datetime

from modules.tactical_scoring_engine import apply_tactical_rules
from modules.risk_and_reporting_engine import apply_stop_logic, export_to_csv, export_to_pdf

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
        return df
    except Exception as e:
        print(f"⚠ Error loading portfolio file: {e}")
        return None


def load_zacks_files():
    """Load latest Zacks screens for Growth1, Growth2, Defensive."""
    categories = ["Growth1", "Growth 1", "Growth2", "Growth 2", "Defensive"]
    loaded = {}

    for cat in categories:
        path = load_most_recent_file(cat)
        if path:
            print(f"📥 Loaded Zacks File: {os.path.basename(path)}")
            try:
                loaded[cat] = pd.read_csv(path)
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

    # Try to compute Value
    if {"Shares", "Current Price"}.issubset(df.columns):
        df["Value"] = df["Shares"] * df["Current Price"]
        total_value = df["Value"].sum()
    else:
        total_value = None

    cols_to_show = [c for c in ["Ticker", "Shares", "Current Price", "Value"] if c in df.columns]

    print("\n📊 Portfolio Summary")
    print(tabulate(df[cols_to_show].head(20), headers="keys", tablefmt="github", floatfmt=".2f"))

    if total_value is not None:
        print(f"\n💰 Estimated Total Portfolio Value: ${total_value:,.2f}")


def crossmatch_with_zacks(portfolio_df: pd.DataFrame, zacks_data: dict):
    """Crossmatch portfolio tickers with Zacks lists and apply tactical logic."""
    if portfolio_df is None or portfolio_df.empty:
        print("\n⚠ No portfolio data available for crossmatch.")
        return None

    if not zacks_data:
        print("\n⚠ No Zacks data available for crossmatch.")
        return None

    if "Ticker" not in portfolio_df.columns:
        print("\n⚠ Portfolio file missing 'Ticker' column.")
        return None

    portfolio_df = portfolio_df.copy()
    portfolio_df["Ticker"] = portfolio_df["Ticker"].astype(str).str.upper()

    all_matches = []

    for category, zdf in zacks_data.items():
        if "Ticker" not in zdf.columns:
            continue

        zdf = zdf.copy()
        zdf["Ticker"] = zdf["Ticker"].astype(str).str.upper()

        if "Zacks Rank" in zdf.columns:
            zdf["Zacks Rank"] = pd.to_numeric(zdf["Zacks Rank"], errors="coerce")

        merged = pd.merge(portfolio_df, zdf, on="Ticker", how="inner", suffixes=("", "_z"))
        if not merged.empty:
            merged["Screen Category"] = category
            all_matches.append(merged)

    if not all_matches:
        print("\n📭 No matches found between portfolio and any Zacks screen.")
        return None

    result = pd.concat(all_matches, ignore_index=True)

    # Apply tactical rules (Zacks-based) and stop logic
    result = apply_tactical_rules(result)
    result = apply_stop_logic(result)

    # Select columns to display if they exist
    display_cols = [
        "Ticker",
        "Shares",
        "Current Price",
        "Gain/Loss %",
        "Zacks Rank",
        "Action",
        "Screen Category",
        "Stop Recommendation",
    ]
    display_cols = [c for c in display_cols if c in result.columns]

    print("\n🛡 Tactical Intelligence Output — Actionable Orders")
    print(tabulate(result[display_cols], headers="keys", tablefmt="github", floatfmt=".2f"))

    # Exports
    export_to_csv(result)
    export_to_pdf(result)

    return result


def main():
    print("\n🧭 Fox Valley Intelligence Engine — Tactical Console (CLI Edition)")
    print("==================================================================\n")
    print(f"Run Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    portfolio_df = load_portfolio()
    zacks_files = load_zacks_files()

    show_portfolio_summary(portfolio_df)
    crossmatch_with_zacks(portfolio_df, zacks_files)

    print("\n🚀 Engine Execution Complete — Final Assembly Online.\n")


if __name__ == "__main__":
    main()
