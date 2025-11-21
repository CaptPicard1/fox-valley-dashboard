import pandas as pd


def calculate_unrealized_gain(row):
    """
    Calculate unrealized gain/loss % based on cost basis.
    Expects columns: 'Current Price' and 'Cost Basis' (per share).
    Returns None if data is missing.
    """
    try:
        price = float(row.get("Current Price", None))
        cost = float(row.get("Cost Basis", None))
        if cost and cost != 0:
            return ((price - cost) / cost) * 100.0
    except Exception:
        pass
    return None


def zacks_signal(rank):
    """Map Zacks Rank (1-5) to basic tactical action."""
    mapping = {
        1: "Strong Buy",
        2: "Buy",
        3: "Hold",
        4: "Trim",
        5: "Sell",
    }
    try:
        r = int(rank)
        return mapping.get(r, "No Rating")
    except Exception:
        return "No Rating"


def apply_tactical_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Zacks-based tactical scoring and performance-based refinements.
    Expects columns: 'Zacks Rank', 'Current Price', 'Cost Basis'.
    """
    df = df.copy()

    # Gain/Loss %
    df["Gain/Loss %"] = df.apply(calculate_unrealized_gain, axis=1)

    # Base Action from Zacks rank
    if "Zacks Rank" in df.columns:
        df["Action"] = df["Zacks Rank"].apply(zacks_signal)
    else:
        df["Action"] = "No Rating"

    # Refinements based on performance
    # If holding with strong gains, suggest trim
    df.loc[
        (df["Action"] == "Hold") & (df["Gain/Loss %"].notna()) & (df["Gain/Loss %"] > 20),
        "Action",
    ] = "Trim"

    # If Zacks says Sell but gain is very high, call out profit taking
    df.loc[
        (df["Action"] == "Sell") & (df["Gain/Loss %"].notna()) & (df["Gain/Loss %"] > 30),
        "Action",
    ] = "Sell - Take Profits"

    # If Zacks says Buy and stock is down significantly, highlight dip buy
    df.loc[
        (df["Action"] == "Buy") & (df["Gain/Loss %"].notna()) & (df["Gain/Loss %"] < -10),
        "Action",
    ] = "Buy More (Dip Buy)"

    return df
