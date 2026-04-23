#######################################################################################################
# Imaging Core Dashboard
# Created By: Joshua Pasaye
#
# Purpose: The purpose of this dashboard is to create an interactive dashboard that extends
# the 'imaging_report' html report that only reports on scan completion numbers.
# This dashboard combines eligibility data, scan completion numbers, and post-scan metrics
# for a comprehensive summary of imaging accomplished by the Mesulam Institute and the Imaging Core.
# This dashboard will be run every week but can be changed at the direction of the Imaging Core
# director. Please review the README.doc for detailed instructions of how to run the script.
#######################################################################################################

import streamlit as st
import pandas as pd
from utils.data_loader import load_all_data
from utils.sidebar import render_sidebar
from utils.constants import filter_scans, filter_elig, SCAN_TYPES

st.set_page_config(
    page_title="Neuroimaging Dashboard",
    page_icon=":brain:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load data and filters ─────────────────────────────────────────────────────
elig_final, scan_final, metrics_final = load_all_data()
f = render_sidebar()

s = filter_scans(
    scan_final,
    f["statuses"],
    f["studies"],
    f["date_start"],
    f["date_end"],
)
e = filter_elig(
    elig_final,
    f["statuses"],
    f["date_start"],
    f["date_end"],
)

# ── Page header ───────────────────────────────────────────────────────────────
st.title("🧠 ADRC Imaging Core Dashboard")
st.caption(
    f"**{f['kpi_range']}** · "
    f"{f['date_start'].strftime('%b %d, %Y')} – {f['date_end'].strftime('%b %d, %Y')} · "
)
st.divider()

# ── Summary KPIs ──────────────────────────────────────────────────────────────
total_participants = s["global_id"].nunique()
total_scans        = len(s[s["scan_confirmation"] == "Performed"])
total_canceled     = s["scan_canceled_1x"].notna().sum() + s["scan_canceled_2x"].notna().sum()
screen_pass        = (e["elig_status"] == "Passed Screening").sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Unique participants imaged", f"{total_participants:,}")
c2.metric("Total scans performed",      f"{total_scans:,}")
c3.metric("Total scan cancellations",   f"{total_canceled:,}")
c4.metric("Passed screening (elig.)",   f"{int(screen_pass):,}")

st.divider()

# ── Study snapshot: performed scans per study × modality ─────────────────────
st.subheader("Study snapshot — performed scans by modality")
st.caption("Counts reflect scans with 'Performed' confirmation within the selected period and filters.")

performed = s[s["scan_confirmation"] == "Performed"].copy()

if performed.empty:
    st.info("No performed scans found for the current filters.")
else:
    # Pivot: rows = study_affiliation, columns = scan_type
    pivot = (
        performed
        .groupby(["study_affiliation", "scan_type"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=[c for c in SCAN_TYPES if c in performed["scan_type"].unique()], fill_value=0)
    )

    # Add row totals
    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("Total", ascending=False).reset_index()
    pivot = pivot.rename(columns={"study_affiliation": "Study"})

    # Column totals row
    totals_row = pivot.select_dtypes("number").sum()
    totals_row["Study"] = "**TOTAL**"
    pivot = pd.concat([pivot, totals_row.to_frame().T], ignore_index=True)

    st.dataframe(pivot, use_container_width=True, hide_index=True)

st.divider()

# ── Scan cancellation breakdown ───────────────────────────────────────────────
st.subheader("Cancellations by scan type")

canceled_rows = []
for _, row in s.iterrows():
    if pd.notna(row.get("scan_canceled_1x")):
        canceled_rows.append({
            "scan_type": row["scan_type"],
            "study":     row["study_affiliation"],
            "reason":    row.get("scan_canceled_reason_1x"),
            "occurrence": "1st",
        })
    if pd.notna(row.get("scan_canceled_2x")):
        canceled_rows.append({
            "scan_type": row["scan_type"],
            "study":     row["study_affiliation"],
            "reason":    row.get("scan_canceled_reason_2x"),
            "occurrence": "2nd",
        })

if canceled_rows:
    cancel_df = pd.DataFrame(canceled_rows)
    cancel_pivot = (
        cancel_df.groupby(["study", "scan_type"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"study": "Study"})
    )
    st.dataframe(cancel_pivot, use_container_width=True, hide_index=True)
else:
    st.info("No cancellations in the selected period.")

st.divider()
st.markdown(
    "Navigate to **Eligibility**, **Scan Completion**, or **Scan Metrics** using the sidebar."
)
