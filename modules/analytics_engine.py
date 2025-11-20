# ============================================================
# 🧭 Fox Valley Intelligence Engine — Analytics Engine Module
# v7.3R-5.3 | Heat Maps, Correlation, Historical Visual Analytics
# ============================================================

import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

# ------------------------------------------------------------
# Heatmap: Portfolio Weight Distribution
# ------------------------------------------------------------
def render_portfolio_weight_heatmap(portfolio_df):
    if portfolio_df is None or portfolio_df.empty:
        st.warning("Portfolio data unavailable for weight heat map.")
        return

    if "Current Value" not in portfolio_df.columns:
        st.warning("Missing 'Current Value' column for portfolio weight analysis.")
        return

    total_cv = pd.to_numeric(portfolio_df["Current Value"], errors="coerce").fillna(0).sum()
    if total_cv <= 0:
        st.warning("Total portfolio value is zero — cannot compute weights.")
        return

    weight_df = portfolio_df.copy()
    weight_df["Weight %"] = (
        pd.to_numeric(weight_df["Current Value"], errors="coerce").fillna(0) / total_cv
    ) * 100

    fig_weight = px.imshow(
        [weight_df["Weight %"]],
        labels=dict(color="Weight %"),
        x=weight_df.get("Ticker", pd.Series(range(len(weight_df)))),
        y=["Weight"],
    )
    fig_weight.update_layout(height=300)

    with st.expander("📘 Portfolio Weight Heat Map"):
        st.plotly_chart(fig_weight, use_container_width=True)


# ------------------------------------------------------------
# Heatmap: Portfolio Gain/Loss %
# ------------------------------------------------------------
def render_gain_loss_heatmap(portfolio_df):
    if portfolio_df is None or portfolio_df.empty:
        st.warning("Portfolio data unavailable for gain/loss heat map.")
        return

    gain_col_candidates = ["Gain/Loss %", "Total Gain/Loss Percent", "Today's Gain/Loss Percent"]
    gain_col = next((c for c in gain_col_candidates if c in portfolio_df.columns), None)

    if not gain_col:
        st.warning("No recognized gain/loss column found for heat map.")
        return

    gain_series = pd.to_numeric(portfolio_df[gain_col], errors="coerce").fillna(0)

    fig_gain = px.imshow(
        [gain_series],
        labels=dict(color=gain_col),
        x=portfolio_df.get("Ticker", pd.Series(range(len(gain_series)))),
        y=[gain_col],
    )
    fig_gain.update_layout(height=300)

    with st.expander("📈 Gain/Loss % Heat Map"):
        st.plotly_chart(fig_gain, use_container_width=True)


# ------------------------------------------------------------
# Heatmap: Zacks Composite Score
# ------------------------------------------------------------
def render_zacks_composite_heatmap(scored_candidates):
    if scored_candidates is None or scored_candidates.empty:
        st.warning("No Zacks score data available for heat map.")
        return

    if "CompositeScore" not in scored_candidates.columns:
        st.warning("CompositeScore column missing — heat map aborted.")
        return

    comp_df = scored_candidates[["Ticker", "CompositeScore"]].reset_index(drop=True)

    fig_comp = px.imshow(
        [comp_df["CompositeScore"]],
        labels=dict(color="Composite Score"),
        x=comp_df["Ticker"],
        y=["Composite Score"],
    )
    fig_comp.update_layout(height=300)

    with st.expander("💡 Zacks Composite Score Heat Map"):
        st.plotly_chart(fig_comp, use_container_width=True)


# ------------------------------------------------------------
# Correlation Matrix
# ------------------------------------------------------------
def render_correlation_matrix(portfolio_df):
    if portfolio_df is None or portfolio_df.empty:
        st.warning("Portfolio data unavailable for correlation matrix.")
        return

    numeric_cols = portfolio_df.select_dtypes(include=["float", "int"]).columns
    if len(numeric_cols) <= 1:
        st.warning("Not enough numeric data to compute correlation matrix.")
        return

    corr = portfolio_df[numeric_cols].corr()

    with st.expander("🧩 Correlation Matrix Heat Map"):
        fig, ax = plt.subplots(figsize=(11, 9))
        sns.heatmap(corr, cmap="coolwarm", annot=True, fmt=".2f", linewidths=0.5, ax=ax)
        st.pyplot(fig)

# ============================================================
# Unified Analytics Display Function
# ============================================================
def render_analytics_cluster(portfolio_df, scored_candidates):
    st.markdown("## 🔥 Analytics Cluster — Heat Map Suite")

    render_portfolio_weight_heatmap(portfolio_df)
    render_gain_loss_heatmap(portfolio_df)
    render_zacks_composite_heatmap(scored_candidates)
    render_correlation_matrix(portfolio_df)

