# ============================================================
# 🧭 Fox Valley Intelligence Engine — Zacks Engine Module
# v7.3R-5.3 | Screen Loader • Merge Engine • Composite Scoring
# ============================================================

import os
import pandas as pd
import numpy as np
from datetime import datetime

# -----------------------------
# GLOBAL CONSTANTS
# -----------------------------
DATA_DIR = "data"
ZACKS_PREFIX = "zacks_custom_screen"
VALID_SCREEN_TYPES = ["Growth1", "Growth2", "DefensiveDividend"]


# ============================================================
# ZACKS AUTO-DETECTION AND LOADING
# ============================================================
def load_zacks_files_auto(directory=DATA_DIR):
    """
    Auto-detects latest Zacks files in /data and groups them by date.
    Returns dict: { "Growth1": (df, filename), ... }
    """
    import re
    if not os.path.isdir(directory):
        return {}

    files = [
        f for f in os.listdir(directory)
        if f.startswith(ZACKS_PREFIX) and f.endswith(".csv")
    ]
    if not files:
        return {}

    date_map = {}
    for f in files:
        match = re.search(r"zacks_custom_screen_(\d{4}-\d{2}-\d{2})", f)
        if match:
            dt = match.group(1)
            date_map.setdefault(dt, []).append(f)

    if not date_map:
        return {}

    newest_date = sorted(date_map.keys())[-1]
    output = {}

    for f in date_map[newest_date]:
        lower = f.lower()
        full_path = os.path.join(directory, f)

        try:
            df = pd.read_csv(full_path)

            if "growth 1" in lower:
                output["Growth1"] = (df, f)
            elif "growth 2" in lower:
                output["Growth2"] = (df, f)
            elif "defensive" in lower or "dividends" in lower:
                output["DefensiveDividend"] = (df, f)
        except Exception:
            continue

    return output


# ============================================================
# SCREEN PREPARATION / NORMALIZATION
# ============================================================
def prepare_screen(df, label):
    """
    Adds Source label, normalizes column trim.
    """
    if df is None:
        return None

    clean = df.copy()
    clean.columns = [c.strip() for c in clean.columns]
    clean["Source"] = label
    return clean


def merge_zacks_screens(zacks_dict):
    """
    Combines all available screens into a unified dataframe.
    """
    prepared = []
    for label in VALID_SCREEN_TYPES:
        if label in zacks_dict:
            df, _fn = zacks_dict[label]
            p = prepare_screen(df, label)
            if p is not None:
                prepared.append(p)
    return pd.concat(prepared, ignore_index=True) if prepared else pd.DataFrame()


# ============================================================
# COMPOSITE SCORING ENGINE
# ============================================================
def score_zacks_candidates(df):
    """
    Calculates Composite Scoring based on Rank, Momentum, Cap, Source.
    Returns full sorted dataframe.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    scored = df.copy()

    # Extract RankScore (lower is better)
    if "Zacks Rank" in scored.columns:
        scored["RankScore"] = (
            scored["Zacks Rank"].astype(str).str.extract(r"(\d)").astype(float)
        )
    else:
        scored["RankScore"] = 5.0

    # Momentum % and Market Cap
    scored["Momentum"] = pd.to_numeric(
        scored.get("Price Change %", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0.0)

    scored["MarketScore"] = pd.to_numeric(
        scored.get("Market Cap", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0.0)

    def source_weight(src):
        if src == "Growth1":
            return 1.15
        elif src == "Growth2":
            return 1.10
        elif src == "DefensiveDividend":
            return 1.05
        return 1.0

    scored["SourceWeight"] = scored["Source"].apply(source_weight)

    scored["CompositeScore"] = (
        ((6 - scored["RankScore"]) * 5)
        + scored["Momentum"] * 0.25
        + scored["MarketScore"] * 0.00001
    ) * scored["SourceWeight"]

    return scored.sort_values("CompositeScore", ascending=False)


# ============================================================
# TOP-N EXTRACTION
# ============================================================
def get_top_n(df, n=10):
    """
    Returns top N rows based on CompositeScore
    """
    if df is not None and not df.empty:
        return df.head(n)
    return pd.DataFrame()


# ============================================================
# RANK 1 HIGHLIGHT HELPER FOR UI
# ============================================================
def highlight_rank_1(row):
    try:
        if "Zacks Rank" in row and str(row["Zacks Rank"]).strip() == "1":
            return ['background-color: #ffeb3b33'] * len(row)
    except Exception:
        pass
    return [''] * len(row)


# ============================================================
# END OF MODULE — zacks_engine.py
# ============================================================

