"""
sidebar.py  –  Shared sidebar rendered on every page.
Imports constants from utils.constants (not data_loader).
Studies are populated dynamically from scan_final so they always
reflect whatever study_affiliation values are in REDCap.
"""
import streamlit as st
import pandas as pd
from datetime import date
from utils.constants import DATE_RANGES, STATUSES
from utils.data_loader import load_all_data


def render_sidebar() -> dict:
    """
    Render the shared sidebar filters and return selected values.
    Called once at the top of every page file.
    """
    _, scan_final, _ = load_all_data()

    min_date = pd.to_datetime(scan_final["scan_date"]).min().date()
    max_date = date.today()

    date_ranges = {
        "Overall": (min_date, max_date),
        **DATE_RANGES,
    }
    
    # Build dynamic study list from the real data
    all_studies = sorted(
        scan_final["study_affiliation"].dropna().unique().tolist()
    )

    with st.sidebar:
        st.markdown("## 🧠 ADRC Imaging Core")
        st.caption("Imaging Core Performance Dashboard")
        st.divider()

        kpi_range = st.selectbox(
            "KPI date range",
            list(date_ranges.keys()),
            key="kpi_range",
            )

        statuses = st.multiselect(
            "Participant status",
            STATUSES,
            default=STATUSES,
            key="statuses",
        )

        studies = st.multiselect(
            "Study",
            all_studies,
            default=all_studies,
            key="studies",
        )

        date_start, date_end = date_ranges[kpi_range]
        st.divider()
        st.caption(
            f"**Period:** {date_start.strftime('%b %d, %Y')} – "
            f"{date_end.strftime('%b %d, %Y')}"
        )

    return {
        "kpi_range": kpi_range,
        "statuses": statuses  or STATUSES,
        "studies": studies   or all_studies,
        "date_start": date_start,
        "date_end": date_end,
    }
