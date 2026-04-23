"""
1_Eligibility.py
Eligibility tracking page — uses elig_final from data_loader.
Columns available: global_id, ptid, modality, eligibility_date, elig_status,
                   screen_fail, sf_burdensome, scheduled, modality_scheduled,
                   modality_pending, core_pt_status
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_all_data
from utils.sidebar import render_sidebar
from utils.constants import filter_elig, COLORS, COLOR_SEQ, PLOTLY_LAYOUT

st.set_page_config(
    page_title="Eligibility · ADRC Imaging",
    page_icon="📋",
    layout="wide",
)

elig_final, _, _ = load_all_data()
f = render_sidebar()

e = filter_elig(elig_final, f["statuses"], f["date_start"], f["date_end"])

st.title("📋 Eligibility")
st.caption(
    f"{f['kpi_range']} · "
    f"{f['date_start'].strftime('%b %d, %Y')} – {f['date_end'].strftime('%b %d, %Y')} · "
)
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total        = len(e)
passed       = (e["elig_status"] == "Passed Screening").sum()
failed       = (e["elig_status"] == "Screen Fail").sum()
pending      = (e["elig_status"] == "Pending").sum()
scheduled    = (e["scheduled"] == "YES").sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total eligibility records", f"{total:,}")
k2.metric("Passed screening",          f"{int(passed):,}",
          delta=f"{passed / total * 100:.1f}%" if total else None)
k3.metric("Screen fails",              f"{int(failed):,}",
          delta=f"{failed / total * 100:.1f}%" if total else None, delta_color="inverse")
k4.metric("Pending",                   f"{int(pending):,}")
k5.metric("Scheduled after screen",    f"{int(scheduled):,}")

st.divider()

# ── Charts: status breakdown and screen-fail reasons ─────────────────────────
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Eligibility status by modality")
    if not e.empty:
        status_df = (
            e.groupby(["modality", "elig_status"])
             .size()
             .reset_index(name="Count")
        )
        fig = px.bar(
            status_df, x="modality", y="Count", color="elig_status",
            color_discrete_map={
                "Passed Screening": COLORS["teal"],
                "Screen Fail":      COLORS["coral"],
                "Pending":          COLORS["amber"],
            },
            labels={"modality": "Modality", "elig_status": "Status"},
            barmode="group",
        )
        fig.update_layout(**PLOTLY_LAYOUT)
        fig.update_xaxes(title=None)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for selected filters.")

with col_right:
    st.subheader("Screen-fail reasons")
    fail_df = e[e["elig_status"] == "Screen Fail"].copy()
    if not fail_df.empty:
        reason_counts = (
            fail_df["screen_fail"]
            .dropna()
            .value_counts()
            .rename_axis("Reason")
            .reset_index(name="Count")
            )
        fig_fail = px.pie(
            reason_counts,
            names="Reason",
            values="Count",
            hole=0.45,
            color_discrete_sequence=COLOR_SEQ,
            )
        fig_fail.update_traces(textposition="inside", textinfo="percent+label")
        fig_fail.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_fail, use_container_width=True)
    else:
        st.info("No screen failures in the selected period.")

st.divider()

# ── Burdensome reason breakdown ───────────────────────────────────────────────
st.subheader("Burdensome screen-fail sub-reasons")
burden_df = e[e["screen_fail"] == "Burdensome"].copy()
if not burden_df.empty:
    bcount = (
        burden_df["sf_burdensome"]
        .dropna()
        .value_counts()
        .reset_index()
    )
    bcount.columns = ["Reason", "Count"]
    fig_b = px.bar(
        bcount, x="Count", y="Reason", orientation="h",
        color_discrete_sequence=[COLORS["amber"]],
        labels={"Reason": ""},
    )
    fig_b.update_layout(**PLOTLY_LAYOUT, showlegend=False)
    st.plotly_chart(fig_b, use_container_width=True)
else:
    st.info("No burdensome failures in the selected period.")

st.divider()

# ── Monthly eligibility trend ─────────────────────────────────────────────────
st.subheader("Monthly eligibility activity")
if not e.empty:
    monthly = (
        e.assign(month=pd.to_datetime(e["eligibility_date"]).dt.to_period("M").astype(str))
         .groupby(["month", "elig_status"])
         .size()
         .reset_index(name="Count")
    )
    fig_m = px.bar(
        monthly, x="month", y="Count", color="elig_status",
        color_discrete_map={
            "Passed Screening": COLORS["teal"],
            "Screen Fail":      COLORS["coral"],
            "Pending":          COLORS["amber"],
        },
        labels={"month": "Month", "elig_status": "Status"},
    )
    fig_m.update_layout(**PLOTLY_LAYOUT)
    fig_m.update_xaxes(tickangle=-45, title=None)
    st.plotly_chart(fig_m, use_container_width=True)

st.divider()

# ── PET modality detail ───────────────────────────────────────────────────────
pet_e = e[e["modality"] == "PET"].copy()
if not pet_e.empty and pet_e["modality_scheduled"].notna().any():
    st.subheader("PET modality scheduled / pending")
    col_a, col_b = st.columns(2)
    with col_a:
        sched_counts = (
            pet_e["modality_scheduled"]
            .dropna()
            .str.split(",").explode().str.strip()
            .value_counts().reset_index()
        )
        sched_counts.columns = ["PET modality", "Scheduled count"]
        st.dataframe(sched_counts, use_container_width=True, hide_index=True)
    with col_b:
        pend_counts = (
            pet_e["modality_pending"]
            .dropna()
            .str.split(",").explode().str.strip()
            .value_counts().reset_index()
        )
        pend_counts.columns = ["PET modality", "Pending count"]
        st.dataframe(pend_counts, use_container_width=True, hide_index=True)
    st.divider()

# ── Detail table ──────────────────────────────────────────────────────────────
st.subheader("Eligibility detail log")
display = (
    e[["global_id", "ptid", "modality", "eligibility_date",
       "elig_status", "screen_fail", "sf_burdensome", "scheduled",
       "modality_scheduled", "modality_pending", "core_pt_status"]]
    .sort_values("eligibility_date", ascending=False)
    .rename(columns={
        "global_id":          "Global ID",
        "ptid":               "PTID",
        "modality":           "Modality",
        "eligibility_date":   "Eligibility date",
        "elig_status":        "Elig. status",
        "screen_fail":        "Screen fail reason",
        "sf_burdensome":      "Burdensome detail",
        "scheduled":          "Scheduled",
        "modality_scheduled": "PET modality scheduled",
        "modality_pending":   "PET modality pending",
        "core_pt_status":     "Participant status",
    })
)
st.dataframe(display, use_container_width=True, hide_index=True, height=400)
