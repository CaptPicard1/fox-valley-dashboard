# ============================================================
# 🧭 Fox Valley Intelligence Engine — Tactical Engine Module
# v7.3R-5.3 | Order Intake + Tactical Logging Framework
# ============================================================

import streamlit as st
from datetime import datetime
from modules.diagnostics_engine import log_event


# ------------------------------------------------------------
# Tactical Order Input & Validation
# ------------------------------------------------------------
def capture_orders(buy_ticker, buy_shares, sell_ticker, sell_shares):
    """
    Returns cleaned buy/sell order details.
    If no order, returns None.
    """
    orders = []

    if buy_ticker and buy_shares > 0:
        orders.append({
            "type": "BUY",
            "ticker": buy_ticker.upper().strip(),
            "shares": int(buy_shares),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    if sell_ticker and sell_shares > 0:
        orders.append({
            "type": "SELL",
            "ticker": sell_ticker.upper().strip(),
            "shares": int(sell_shares),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    return orders if orders else None


# ------------------------------------------------------------
# Tactical Event Logging
# ------------------------------------------------------------
def log_tactical_orders(orders):
    """
    Writes tactical orders to Diagnostics Engine.
    """
    if not orders:
        return

    for order in orders:
        details = f"{order['type']} → {order['ticker']} × {order['shares']}"
        log_event("Tactical Order Received", details)


# ------------------------------------------------------------
# Tactical Operations Renderer
# ------------------------------------------------------------
def render_tactical_panel(buy_ticker, buy_shares, sell_ticker, sell_shares):
    """
    UI block for tactical order review.
    """
    st.markdown("## 🎯 Tactical Operations Panel")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Buy Order")
        st.write(f"**Ticker:** {buy_ticker or '—'}")
        st.write(f"**Shares:** {buy_shares or 0}")

    with col2:
        st.markdown("### Sell Order")
        st.write(f"**Ticker:** {sell_ticker or '—'}")
        st.write(f"**Shares:** {sell_shares or 0}")

    with col3:
        st.markdown("### Order Status")
        st.info("Order execution module placeholder — integration pending.")


# ------------------------------------------------------------
# Unified Tactical Controller
# ------------------------------------------------------------
def process_and_render_tactical(buy_ticker, buy_shares, sell_ticker, sell_shares):
    """
    Handles order capture, logging, and panel rendering.
    """
    orders = capture_orders(buy_ticker, buy_shares, sell_ticker, sell_shares)
    log_tactical_orders(orders)
    render_tactical_panel(buy_ticker, buy_shares, sell_ticker, sell_shares)

