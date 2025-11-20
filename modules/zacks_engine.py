# ============================================================
# 🧭 Fox Valley Intelligence Engine — Zacks Engine Module
# v7.3R-5.4 | Unified Screen Loader + Composite Scoring
# ============================================================

import os
import pandas as pd
import numpy as np

# -----------------------------
# GLOBAL VARIABLES
# -----------------------------
DATA_DIR = "data"
ZACKS_PREFIX = "zacks_custom_screen"

VALID_SCREEN_TYPES = ["Growth1", "Growth2", "DefensiveDividend"]


# ============================================================
# 1️⃣ AUTO-DETECT ZACKS SCREEN FILES (LATEST DATE)
# ============================================================
def load_zacks_files_auto(directory=DATA_DIR):
    """Automatically loads the most recent Zacks files (all three types)."""
    import re
    if not os.path.isdir(directory):
        return {}

    files = [
        f for f in os.listdir(directory)
        if f.lower().startswith(ZACKS_PREFIX) and f.endswith(".csv")
    ]
    if not files:
        return {}

    # Group by date
    date_map = {}
    for f in files:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f)
        if m:
            date_map.setdefault(m.group(1), []).append(f)

    if not date_map:
        return {}

    newest_date = sorted(date_map.keys())[-1]
    result = {}

    for f in date_map[newest_date]:
        f_lower = f.lower()
        full_path = os.path.join(directory, f)

        try:
            df = pd.read_csv(full_path)
            df.columns = [c.strip() for c in df.columns]  # clean column names

            if "growth 1" in f_lower:
                result["Growth1"] = (df, f)
            elif "growth 2" in f_lower:
                result["Growth2"] = (df, f)
            elif "defensive" in f_lower or "dividend" in f_lower:
                result["DefensiveDividend"] = (df, f)
        except Exception:
            continue

    return result


# ============================================================
# 2️⃣ PREPARATION & MERGING
# ============================================================
def prepare_screen(df, label):
    """Standardize screen structure and tag source."""
    if df is None:
        return None
    out = df.copy()
    out.columns = [c.strip() for c in out.columns]
    out["Source"] = label
    return out


def merge_zacks_screens(auto_dict):
    """Merge the most recent set of screens from Growth1, Growth2, Defensive."""
    frames = []
    for src in VALID_SCREEN_TYPES:
        item = auto_dict.get(src)
        if item:
            df, _ = item
            processed = prepare_screen(df, src)
            if processed is not None:
                frames.append(processed)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


# ============================================================
# 3️⃣ COMPOSITE CANDIDATE SCORING ENGINE
# ============================================================
def score_zacks_candidates(df):
    """Generate composite scores using Rank, Momentum, Size, and Source Weight."""
    if df is None or df.empty:
        return pd.DataFrame()

    scored = df.copy()

    # Rank Score (inverted — Rank 1 highest)
    scored["RankScore"] = (
        scored["Zacks Rank"].astype(str).str.extract(r"(\d)").astype(float)
        if "Zacks Rank" in scored.columns else 5.0
    )

    # Momentum (from Price Change %)
    scored["Momentum"] = (
        pd.to_numeric(scored["Price Change %"], errors="coerce").fillna(0)
        if "Price Change %" in scored.columns else 0.0
    )

    # Market Cap Scale
    scored["SizeScore"] = (
        pd.to_numeric(scored["Market Cap"], errors="coerce").fillna(0)
        if "Market Cap" in scored.columns else 0.0
    )

    # Source Weighted Scaling
    def weight(src):
        return 1.15 if src == "Growth1" else 1.10 if src == "Growth2" else 1.05

    scored["SourceWeight"] = scored["Source"].apply(weight)

    # Composite Score Formula
    scored["CompositeScore"] = (
        (6 - scored["RankScore"]) * 5
        + scored["Momentum"] * 0.2
        + scored["SizeScore"] * 0.00001
    ) * scored["SourceWeight"]

    return scored.sort_values("CompositeScore", ascending=False)


def get_top_n(df, n):
    """Return only the top-N candidates by composite score."""
    return df.head(n) if df is not None and not df.empty else pd.DataFrame()


# ============================================================
# 4️⃣ STYLE HELPER — HIGHLIGHT ZACKS RANK = 1
# ============================================================
def highlight_rank_1(row):
    """Highlight rows with Zacks Rank = 1."""
    try:
        if "Zacks Rank" in row and str(row["Zacks Rank"]).strip() == "1":
            return ['background-color: #ffeb3b33'] * len(row)
    except Exception:
        pass
    return [''] * len(row)
