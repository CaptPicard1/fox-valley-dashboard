import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def apply_stop_logic(df, stop_loss_pct=-15, trim_gain_pct=25):
    """Adds stop-loss and trim recommendations based on gain/loss%."""
    df["Stop Recommendation"] = "Hold"

    df.loc[df["Gain/Loss %"] <= stop_loss_pct, "Stop Recommendation"] = "Sell - Stop Loss Trigger"
    df.loc[(df["Gain/Loss %"] >= trim_gain_pct) & (df["Action"] != "Sell"),
           "Stop Recommendation"] = "Trim - Secure Profits"

    return df


def export_to_csv(df):
    """Exports full tactical intelligence report to CSV."""
    df.to_csv("tactical_intelligence_report.csv", index=False)
    print("\n📁 CSV Exported: tactical_intelligence_report.csv")


def export_to_pdf(df):
    """Exports tactical intelligence report to PDF."""
    filename = "tactical_intelligence_report.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    elements.append(Paragraph("Fox Valley Intelligence Engine — Tactical Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Convert DataFrame to list format
    data = [df.columns.tolist()] + df.values.tolist()

    # Create table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))

    elements.append(table)
    doc.build(elements)
    print(f"\n📄 PDF Exported: {filename}")
