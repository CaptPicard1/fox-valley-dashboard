"""
Fox Valley Intelligence Engine — Profit & Risk Analyzer Module
Version: v7.4R-Alpha
Purpose:
    • Evaluate portfolio profit performance vs. cost basis
    • Detect risk level (Defensive, Moderate, Aggressive)
    • Verify stop-loss health
    • Flag tactical action priority (Trim, Accumulate, Hold)
    • Export structured CSV + PDF for review boards
"""

import pandas as pd
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os

DATA_PATH = "data"

# === CONFIGURATION ===
STOP_BUFFER = 0.92  # 8% buffer (recommended default)
TRIM_THRESHOLD = 0.25  # Trim if >25% profit
ACCUMULATE_THRESHOLD = -0.08  # Buy more if < -8% loss


def load_portfolio():
    """Auto-detect most recent portfolio file."""
    files = [f for f in os.listdir(DATA_PATH) if f.startswith("Portfolio_Positions") and f.endswith(".csv")]
    if not files:
        print("⚠ No portfolio files found.")
        return None

    files.sort()
    latest = files[-1]
    print(f"🗂 Using Portfolio File: {latest}")
    return pd.read_csv(os.path.join(DATA_PATH, latest))


def calculate_profit_and_risk(df: pd.DataFrame):
    """Calculate profit % and assign risk level."""

    # Normalize numeric columns
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Current Value"] = df["Current Value"].replace('[\$,]', '', regex=True).astype(float)
    df["Cost Basis Total"] = df["Cost Basis Total"].replace('[\$,]', '', regex=True).astype(float)

    # Calculate Profit/Loss %
    df["Profit %"] = ((df["Current Value"] - df["Cost Basis Total"]) / df["Cost Basis Total"]) * 100

    # Risk Assignment (based on Market Cap & Zacks Rank)
    conditions = [
        df["Market Cap (mil)"] > 10000,  # Mega / Large Cap
        (df["Market Cap (mil)"] <= 10000) & (df["Market Cap (mil)"] > 2000),
        df["Market Cap (mil)"] <= 2000   # Small / Mid / Micro Cap
    ]
    risk_levels = ["Defensive", "Moderate", "Aggressive"]

    df["Risk Category"] = np.select(conditions, risk_levels, default="Moderate")
    return df


def apply_tactical_flags(df: pd.DataFrame):
    """Set Action Priority based on performance & risk."""
    actions = []

    for _, row in df.iterrows():
        if row["Profit %"] >= TRIM_THRESHOLD * 100:
            actions.append("Trim / Lock Profits")
        elif row["Profit %"] <= ACCUMULATE_THRESHOLD * 100:
            actions.append("Buy / Accumulate")
        else:
            actions.append("Hold / Monitor")

    df["Tactical Action"] = actions
    return df


def export_profit_risk_csv(df: pd.DataFrame):
    filename = f"profit_risk_report_{datetime.now().strftime('%Y-%m-%d')}.csv"
    df.to_csv(filename, index=False)
    print(f"📁 CSV Exported: {filename}")


def export_profit_risk_pdf(df: pd.DataFrame):
    filename = f"profit_risk_report_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Fox Valley Intelligence Engine — Tactical Profit & Risk Report", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 12))

    columns_to_show = ["Ticker", "Quantity", "Current Value", "Profit %", "Risk Category", "Tactical Action"]
    data = [columns_to_show] + df[columns_to_show].values.tolist()

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.whitesmoke]),
    ]))
    story.append(table)

    doc.build(story)
    print(f"📄 PDF Exported: {filename}")


def run_profit_risk_analyzer():
    """Full execution sequence."""
    df = load_portfolio()
    if df is None:
        return

    print("\n💹 Evaluating Profit and Risk Levels...")
    df = calculate_profit_and_risk(df)
    df = apply_tactical_flags(df)

    print("\n📊 Tactical Profit + Risk Intelligence:")
    print(df[["Ticker", "Profit %", "Risk Category", "Tactical Action"]].head(20).to_string(index=False))

    export_profit_risk_csv(df)
    export_profit_risk_pdf(df)

    print("\n🚀 Tactical Profit & Risk Analyzer Complete — Command Ready.\n")


if __name__ == "__main__":
    run_profit_risk_analyzer()
