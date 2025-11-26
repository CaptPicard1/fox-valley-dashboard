"""
Fox Valley Intelligence Engine — Tactical Dashboard
Version: v7.4R
Purpose:
    • Load Portfolio + Zacks Screens
    • Execute Tactical Crossmatch and Profit/Risk Analyzer
    • Render actionable dashboard in Streamlit
"""

import streamlit as st
import pandas as pd
import glob

from fox_valley_intelligence_engine import (
    load_portfolio,
    load_zacks_files,
    crossmatch_with_zacks
)

from modules.profit_risk_analyzer import run_profit_risk_analyzer


# ==========================
# Page Setup
# ==========================
st.set_page_config(
    page_title="Fox Valley Tactical Command Deck",
    layout="wide",
)

st.title("🧭 Fox Valley Intelligence Engine — Tactical Command Deck")
st.caption("v7.4R | Portfolio Risk, Profit, and Tactical Intelligence")


# ==========================
# Load Data Sources
# ==========================
portfolio_df = load_portfolio()
zacks_data = load_zacks_files()

if portfolio_df is None:
    st.error("⚠ No Portfolio Data Found — Please upload a valid CSV to /data folder.")
    st.stop()

if not zacks_data:
    st.warning("⚠ No Zacks Files Found — Tactical Screens Required.")


# ==========================
# Display Portfolio Summary
# ==========================
st.subheader("📊 Portfolio Overview")

cols_to_show = [
    "Ticker", "Quantity", "Current Value",
    "Total Gain/Loss Percent", "Percent Of Account",
]

df_display = portfolio_df.copy()
df_display["Current Value"] = df_display["Current Value"].replace('[\$,]', '', regex=True).astype(float)
df_display["Percent Of Account"] = df_display["Percent Of Account"].replace('[\%,]', '', regex=True).astype(float)

st.dataframe(df_display[cols_to_show], use_container_width=True)


# ==========================
# Tactical Zacks Crossmatch
# ==========================
st.subheader("🛡 Tactical Intelligence — Zacks Crossmatch")

if st.button("Run Tactical Crossmatch"):
    with st.spinner("Analyzing tactical signals..."):
        result = crossmatch_with_zacks(portfolio_df, zacks_data)
        if result is not None and not result.empty:
            st.success("🔍 Tactical Crossmatch Complete — Orders Ready")
            st.dataframe(result, use_container_width=True)
        else:
            st.warning("📭 No tactical matches found. Check Zacks screens or portfolio tickers.")


# ==========================
# Profit & Risk Analyzer
# ==========================
st.subheader("💹 Profit & Risk Monitoring")

if st.button("Generate Profit & Risk Intelligence"):
    with st.spinner("Evaluating profit strength, stop-loss health, and tactical flags..."):
        run_profit_risk_analyzer()
        st.success("🚀 Profit & Risk Analysis Complete — Reports Generated")
        st.info("📁 Check root folder for: profit_risk_report.csv and profit_risk_report.pdf")


# ==========================
# Footer
# ==========================
st.markdown("---")
st.caption("🔒 Fox Valley Intelligence Engine | Confidential Tactical Analytics Suite")
