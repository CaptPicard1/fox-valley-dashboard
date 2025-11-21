import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def apply_stop_logic(df: pd.DataFrame, stop_loss_pct: float = -15.0, trim_gain_pct: float = 25.0) -> pd.DataFrame:
    """
    Add stop-loss and trim recommendations based on Gain/Loss % and current Action.
    Expects 'Gain/Loss %' and 'Action' columns.
    """
    df = df.copy()
    if "Gain/Loss %" not in df.columns:
        df["Gain/Loss %"] = None

    df["Stop Recommendation"] = "Hold"

    # Stop loss
    df.loc[
        df["Gain/Loss %"].notna() & (df["Gain/Loss %"] <= stop_loss_pct),
        "Stop Recommendation",
    ] = "Sell - Stop Loss Trigger"

    # Trim profits where strong gains but not already a Sell
    df.loc[
        df["Gain/Loss %"].notna()
        & (df["Gain/Loss %"] >= trim_gain_pct)
        & (df["Action"] != "Sell"),
        "Stop Recommendation",
    ] = "Trim - Secure Profits"

    return df


def export_to_csv(df: pd.DataFrame, filename: str = "tactical_intelligence_report.csv"):
    """Export full tactical intelligence DataFrame to CSV."""
    df.to_csv(filename, index=False)
    print(f"\n📁 CSV Exported: {filename}")


def export_to_pdf(df: pd.DataFrame, filename: str = "tactical_intelligence_report.pdf"):
    """Export tactical intelligence report to a simple PDF table."""
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []

    title = Paragraph("Fox Valley Intelligence Engine — Tactical Report", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Limit columns for PDF if there are too many
    cols = [
        c
        for c in [
            "Ticker",
            "Shares",
            "Current Price",
            "Gain/Loss %",
            "Zacks Rank",
            "Action",
            "Screen Category",
            "Stop Recommendation",
        ]
        if c in df.columns
    ]

    data = [cols] + df[cols].astype(str).values.tolist()

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements.append(table)
    doc.build(elements)
    print(f"📄 PDF Exported: {filename}")
