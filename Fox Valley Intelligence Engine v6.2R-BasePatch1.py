# ---------- PORTFOLIO NORMALIZATION & VALIDATION ----------
portfolio["Ticker"] = portfolio["Ticker"].astype(str).str.strip().str.upper()
if "CostBasis" in portfolio.columns and "MarketPrice" in portfolio.columns:
    portfolio["Shares"] = pd.to_numeric(portfolio.get("Shares", 0), errors="coerce")
    portfolio["MarketValue"] = portfolio["Shares"] * portfolio["MarketPrice"]
    portfolio["GainLoss$"] = (portfolio["MarketPrice"] - portfolio["CostBasis"]) * portfolio["Shares"]
    portfolio["GainLoss%"] = ((portfolio["MarketPrice"] / portfolio["CostBasis"]) - 1) * 100
    portfolio["Ticker"] = portfolio["Ticker"].str.replace(r"[^A-Z]", "", regex=True)

else:
    st.warning("⚠️ Missing CostBasis or MarketPrice columns in portfolio_data.csv")
