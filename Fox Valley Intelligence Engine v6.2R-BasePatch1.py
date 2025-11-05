# ---------- PORTFOLIO LOAD + NORMALIZATION ----------
import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fox Valley Intelligence Engine v6.2R", layout="wide")

# Automatically locate the data folder no matter where Streamlit runs
data_path = os.path.join(os.path.dirname(__file__), "data", "Portfolio_Positions_Nov-05-2025.csv")

st.write(f"📂 Attempting to load: {data_path}")

try:
    portfolio = pd.read_csv(data_path)
    st.success("✅ Portfolio loaded successfully!")
except Exception as e:
    st.error(f"❌ Unable to load Portfolio_Positions_Nov-05-2025.csv: {e}")
    st.stop()

# --- Clean column names ---
portfolio.columns = [c.strip() for c in portfolio.columns]

# --- Rename Fidelity headers ---
portfolio.rename(columns={
    "Symbol": "Ticker",
    "Quantity": "Shares",
    "Last Price": "MarketPrice",
    "Cost Basis Total": "CostBasis",
    "Current Value": "MarketValue",
    "Total Gain/Loss Dollar": "GainLoss$",
    "Total Gain/Loss Percent": "GainLoss%"
}, inplace=True)
Commit changes
v6.2R-FidelitySync-Stable Patch 18 — Absolute data folder path verified for Streamlit Cloud


