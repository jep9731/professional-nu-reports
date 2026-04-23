"""
constants.py  –  Shared look-up tables and filter helpers.
All column names match the real REDCap outputs produced by data_loader.py.
"""
from datetime import date
import pandas as pd

# ── Participant statuses (core_pt_status after _clean_uds4) ──────────────────
STATUSES = ["Actively Followed", "Minimal Contact", "Discontinued", "Deceased"]

# ── Scan types (scan_type in scan_final) ────────────────────────────────────
SCAN_TYPES = ["MRI", "Amyloid", "Tau", "FDG"]

# ── KPI date ranges ──────────────────────────────────────────────────────────
# Keys appear in the sidebar selectbox exactly as shown here.
DATE_RANGES: dict[str, tuple[date, date]] = {
    "EAC":          (date(2025, 2, 1), date(2026, 1, 30)),
    "RPPR":         (date(2025, 2, 1), date(2026, 6, 30)),
    "Budget year":  (date(2025, 7, 1), date(2026, 6, 30)),
}

# ── Plotly shared layout ──────────────────────────────────────────────────────
COLORS = {
    "blue":   "#378ADD",
    "teal":   "#1D9E75",
    "coral":  "#D85A30",
    "amber":  "#BA7517",
    "purple": "#7F77DD",
    "lblue":  "#B5D4F4",
    "gray":   "#9E9D9B",
    "green":  "#2E8B57",
}

COLOR_SEQ = [
    COLORS["blue"], COLORS["teal"], COLORS["coral"],
    COLORS["amber"], COLORS["purple"], COLORS["gray"],
]

PLOTLY_LAYOUT = dict(
    font_family="sans-serif",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)


# ── Filter helpers ────────────────────────────────────────────────────────────

def filter_elig(
    df: pd.DataFrame,
    statuses: list[str],
    start: date,
    end: date,
) -> pd.DataFrame:
    """Filter elig_final by core_pt_status and eligibility_date window."""
    mask = (
        df["core_pt_status"].isin(statuses)
        & (pd.to_datetime(df["eligibility_date"]).dt.date >= start)
        & (pd.to_datetime(df["eligibility_date"]).dt.date <= end)
    )
    return df[mask].copy()


def filter_scans(
    df: pd.DataFrame,
    statuses: list[str],
    studies: list[str],
    start: date,
    end: date,
) -> pd.DataFrame:
    """Filter scan_final by status, study, confirmation, and date."""
    status_mask = (
        df["core_pt_status"].isin(statuses)
        )
    study_mask = (
        df["study_affiliation"].isin(studies)
        if studies else pd.Series(True, index=df.index)
        )
    date_series = pd.to_datetime(df["scan_date"]).dt.date
    date_mask = (date_series >= start) & (date_series <= end)

    mask = status_mask & study_mask & date_mask
    return df[mask].copy()


def filter_metrics(
    df: pd.DataFrame,
    statuses: list[str],
    start: date,
    end: date,
) -> pd.DataFrame:
    """Filter metrics_final by core_pt_status and scan_date window."""
    mask = (
        df["core_pt_status"].isin(statuses)
        & (pd.to_datetime(df["scan_date"]).dt.date >= start)
        & (pd.to_datetime(df["scan_date"]).dt.date <= end)
    )
    return df[mask].copy()
