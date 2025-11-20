# ============================================================
# 🧭 Fox Valley Intelligence Engine — UI Bridge Module
# v7.3R-5.4 | Unified UI Rendering: Metrics, Panels, Logging
# ============================================================

import streamlit as st
import pandas as pd

# ------------------------------------------------------------
# METRIC CARDS (Top Overview)
# ------------------------------------------------------------
def render_metric_cards(total_value, available_cash, avg_gain):
    colA, colB, colC = st.columns(3)

    with colA:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("### 💰 Estimated Total Value")
        st.markdown(f"## ${total_value:,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("### 💵 Cash Available to Trade")
        st.markdown(f"## ${available_cash:,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

    with colC:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Avg Gain/Loss %")
        if avg_gain is not None:
            st.markdown(f"## {avg_gain:.2f}%")
        else:
            st.markdown("## —")
        st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------
# DIAGNOSTICS CONSOLE
# ------------------------------------------------------------
def render_diagnostics(manual_cash, portfolio_filename, zacks_files):
    st.markdown("## ⚙️ Diagnostics Console")

    if manual_cash > 0:
        st.info("Manual cash override active — using sidebar override value.")
    else:
        st.info("Using cash reported from portfolio file.")

    if portfolio_filename:
        st.caption(f"Active Portfolio File: **{portfolio_filename}**")

    if not zacks_files:
        st.warning("No Zacks screen files detected in /data for the latest date.")
    else:
        st.success("Zacks screens loaded successfully.")


# ------------------------------------------------------------
# TACTICAL OPERATIONS PANEL
# ------------------------------------------------------------
def render_tactical_panel(buy_ticker, buy_shares, sell_ticker, sell_shares):
    st.markdown("## 🎯 Tactical Operations Panel")
    st.write(f"**Buy Order** — Ticker: {buy_ticker}, Shares: {buy_shares}")
    st.write(f"**Sell Order** — Ticker: {sell_ticker}, Shares: {sell_shares}")
    st.caption("Order execution module placeholder — integration pending.")


# ------------------------------------------------------------
# GENERIC DATA DISPLAY ENGINE
# Accepts both dict of dataframes OR single dataframe
# ------------------------------------------------------------
def show_dataframe(data_dict):
    """
    Accepts:
    - Dict: { 'Growth1 Screen': (df, filename), ... }
    - Single DataFrame
    """
    # Case 1: Single DataFrame
    if isinstance(data_dict, pd.DataFrame):
        st.dataframe(data_dict, use_container_width=True)
        return

    # Case 2: Dictionary containing label: (dataframe, filename)
    if isinstance(data_dict, dict):
        for label, value in data_dict.items():
            try:
                df, filename = value  # unpack tuple
            except Exception:
                continue

            st.markdown(f"### 📄 {label} — `{filename}`")
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠ Unsupported data format for display.")


# ------------------------------------------------------------
# EVENT LOG — Summary Panel
# ------------------------------------------------------------
def render_event_log(portfolio_df, portfolio_filename, scored_candidates, available_cash):
    st.markdown("## 📘 Portfolio Summary")
    if portfolio_df is not None:
        st.write(f"Positions Loaded: {len(portfolio_df)}")
        st.write(f"Portfolio File: `{portfolio_filename}`")
    else:
        st.warning("No portfolio file detected.")

    st.markdown("## 📒 Zacks Screening Summary")
    if scored_candidates is not None and not scored_candidates.empty:
        st.write(f"Candidates Ranked: {len(scored_candidates)}")
    else:
        st.warning("No valid Zacks candidates found.")

    if available_cash < 0:
        st.error("Cash value is negative — check portfolio file formatting.")


# ------------------------------------------------------------
# FOOTER — Styling & System Signature
# ------------------------------------------------------------
def render_footer():
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center; color:gray;">
            🧭 Fox Valley Intelligence Engine — Command Deck v7.3R-5.4<br>
            Modular Engine Architecture | Real-Time Tactical Systems Active
        </div>
        """,
        unsafe_allow_html=True
    )
