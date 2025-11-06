# 🧭 Fox Valley Intelligence Engine — Command Deck Evolution Log

## v5.5 (Legacy Engine)
- Original standalone Python workflow.
- No Streamlit interface; CSV-driven.
- Served as pre-GitHub proof-of-concept for Fidelity + Zacks integration.

## v6.2R-BasePatch1 (Restoration Bridge)
- Transitional build connecting legacy 5.5 logic to Streamlit framework.
- Introduced Zacks screen ingestion, 5-day crossmatch delta logic.
- Provided manual upload and data validation routines.
- Officially archived in November 2025 under Command Deck v6.3R.

## v6.3R (Command Deck)
- Unified architecture contained entirely within **fox_valley_dashboard.py**.
- Real-time Zacks crossmatch analyzer.
- Dynamic **BUY / SELL / HOLD / TRIM** balloon interface.
- Adaptive trailing-stop controller (volatility-based logic).
- Auto-sync between GitHub ↔ Streamlit deployment.
- Designed for live Fidelity portfolio monitoring.

---

### 🔧 Active File
`fox_valley_dashboard.py` — Command Deck v6.3R (Operational Core)

### 🗃️ Archived Files
`Fox Valley Intelligence Engine v6.2R-BasePatch1.py` — Restoration Bridge  
`Fox Valley Intelligence Engine v5.5.py` — Legacy Engine Prototype

---

**Captain’s Note:**  
The Command Deck architecture achieves full integration of Zacks intelligence,
Fidelity positions, and adaptive trailing-stop AI.  
All prior restoration builds have been preserved for Starfleet audit integrity.
