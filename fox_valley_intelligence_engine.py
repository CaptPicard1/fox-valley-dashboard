import os
import pandas as pd
from tabulate import tabulate
from datetime import datetime

# ===== PATH SETTINGS =====
DATA_PATH = "data"

# ===== FILE LOADERS =====
def load_portfolio_file():
    """Loads the most recent portfolio CSV file from /data folder."""
    files = [f for f in os.listdir(DATA_PATH) if "Portfolio" in f and f.endswith(".csv")]
    if not files:
        print("No portfolio file found in /data directory.")
        return None
    latest_file = sorted(files)[-1]
    print(f"\n🗂 Loading Portfolio File: {latest_file}")
    return pd.read_csv(os.path.join(DATA_PATH, latest_file))

def load_zacks_files():
    """Loads the three Zacks screening files: Growth1, Growth2, DefensiveDividend."""
    categories = ["Growth1", "Growth 1", "Growth2", "Growth 2", "Defensive"]
    loaded_files = {}

    for file in os.listdir(DATA_PATH):
        for cat in categories:
            if cat in file and file.endswith(".csv"):
                df = pd.read_csv(os.path.join(DATA_PATH, file))
                loaded_files[cat] = df
                print(f"📥 Loaded Zacks File: {file}")

    if not loaded_files:
        print("\n⚠ No Zacks files found in /data.")
    return loaded_files

# ===== ANALYSIS FUNCTIONS =====
def show_portfolio_summary(df):
    """Displays key portfolio metrics."""
    if df is None or df.empty:
        print("⚠ No portfolio data to analyze.")
        return

    df["Value"] = df["Shares"] * df["Current Price"]
    total_value = df["Value"].sum()

    print("\n📊 Portfolio Summary")
    print(tabulate(df.head(10), headers='keys', tablefmt='github', floatfmt=".2f"))
    print(f"\n💰 Estimated Total Portfolio Value: ${total_value:,.2f}")

def crossmatch_with_zacks(portfolio_df, zacks_data):
    """Crossmatches portfolio holdings with Zacks recommendations."""
    if portfolio_df is None or not zacks_data:
        print("\n⚠ Cannot crossmatch — missing data.")
        return

    portfolio_df["Ticker"] = portfolio_df["Ticker"].str.upper()
    matches = []

    for cat, zacks_df in zacks_data.items():
        zacks_df["Ticker"] = zacks_df["Ticker"].str.upper()
        merged = pd.merge(portfolio_df, zacks_df, on="Ticker", how="inner")
        if not merged.empty:
            merged["Screen Category"] = cat
            matches.append(merged)

    if matches:
        result = pd.concat(matches, ignore_index=True)
        print("\n🎯 Portfolio Holdings with Active Zacks Screening Matches:")
        print(tabulate(result[["Ticker", "Shares", "Current Price", "Zacks Rank", "Screen Category"]],
                       headers='keys', tablefmt='github', floatfmt=".2f"))
    else:
        print("\n📭 No matches found between portfolio and Zacks screens.")

def main():
    print("\n🧭 Fox Valley Intelligence Engine — Tactical Console (CLI Edition)")
    print("============================================================\n")

    portfolio_df = load_portfolio_file()
    zacks_files = load_zacks_files()

    show_portfolio_summary(portfolio_df)
    crossmatch_with_zacks(portfolio_df, zacks_files)

    print("\n🚀 Bravo Segment Complete — Core Engine is Operational.")
    print("Next: Tactical Scoring, Stop Levels, Buy/Sell Signals (Charlie Segment).")

if __name__ == "__main__":
    main()

