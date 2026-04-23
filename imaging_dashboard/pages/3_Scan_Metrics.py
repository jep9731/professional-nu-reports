"""
3_Scan_Metrics.py
Post-scan metrics page — uses metrics_final from data_loader.
Columns: global_id, ptid, scan_date, modality, sequences_scanned,
         sequences_scanned_count, editing_status, version,
         read_number_calc, read_calc, suvr_avid, suvr_sl,
         sl_blankreason, core_pt_status
Modality values: "MRI", "Amyloid", "Tau"
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_all_data
from utils.sidebar import render_sidebar
from utils.constants import filter_metrics, COLORS, COLOR_SEQ, PLOTLY_LAYOUT

st.set_page_config(
    page_title="Scan Metrics · ADRC Imaging",
    page_icon="📊",
    layout="wide",
)

_, _, metrics_final = load_all_data()
f = render_sidebar()

m = filter_metrics(metrics_final, f["statuses"], f["date_start"], f["date_end"])

mri_m     = m[m["modality"] == "MRI"].copy()
amyloid_m = m[m["modality"] == "Amyloid"].copy()
tau_m     = m[m["modality"] == "Tau"].copy()

st.title("📊 Scan Metrics")
st.caption(
    f"{f['kpi_range']} · "
    f"{f['date_start'].strftime('%b %d, %Y')} – {f['date_end'].strftime('%b %d, %Y')} · "
)
st.divider()

# ── Read completion logic (MODALITY-SPECIFIC) ─────────────────────────────

def amyloid_reads_complete_fn(df):
    if df.empty or "read_number_calc" not in df:
        return 0
    return df["read_number_calc"].eq(2).sum()

def tau_reads_complete_fn(df):
    if df.empty or "read_number_calc" not in df:
        return 0

    # Tau encoding is NOT binary/comparable like Amyloid
    # Based on your data: valid "complete" appears to be value == 5
    return df["read_number_calc"].eq(5).sum()

# ── Top-level KPIs ────────────────────────────────────────────────────────────
n_mri     = len(mri_m)
n_amyloid = len(amyloid_m)
n_tau     = len(tau_m)

# PET Reads
amyloid_reads_complete = amyloid_reads_complete_fn(amyloid_m)
tau_reads_complete = tau_reads_complete_fn(tau_m)

# MRI editing statuses
mri_edited   = mri_m["editing_status"].eq("Edited").sum()   if not mri_m.empty else 0
mri_problems = mri_m["editing_status"].eq("Problem").sum()  if not mri_m.empty else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("MRI records",                  f"{n_mri:,}")
k2.metric("Amyloid records",              f"{n_amyloid:,}")
k3.metric("Tau records",                  f"{n_tau:,}")
k4.metric("Amyloid reads complete (≥2)",  f"{int(amyloid_reads_complete):,}",
          delta=f"{amyloid_reads_complete / n_amyloid * 100:.1f}% of amyloid" if n_amyloid else None)
k5.metric("Tau reads complete (≥2)",      f"{int(tau_reads_complete):,}",
          delta=f"{tau_reads_complete / n_tau * 100:.1f}% of tau" if n_tau else None)

st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Amyloid PET clinical reads
# ════════════════════════════════════════════════════════════════════════════════
st.subheader("🔬 Amyloid PET — Clinical read summary")

if amyloid_m.empty:
    st.info("No amyloid records in the selected period.")
else:
    col_a1, col_a2 = st.columns(2)

    with col_a1:
        st.markdown("**Read count distribution**")
        read_counts = (
            amyloid_m["read_number_calc"]
            .value_counts(dropna=False)
            .reset_index()
        )
        read_counts.columns = ["Read number", "Count"]
        read_counts["Read number"] = read_counts["Read number"].fillna("Not recorded").astype(str)
        fig_ar = px.bar(
            read_counts.sort_values("Read number"),
            x="Read number", y="Count",
            color_discrete_sequence=[COLORS["blue"]],
            text="Count",
        )
        fig_ar.update_traces(textposition="outside")
        fig_ar.update_layout(**PLOTLY_LAYOUT, showlegend=False)
        fig_ar.update_xaxes(title="Number of clinical reads completed")
        st.plotly_chart(fig_ar, use_container_width=True)

    with col_a2:
        st.markdown("**Clinical read result (read_calc)**")
        calc_counts = (
            amyloid_m["read_calc"]
            .value_counts(dropna=False)
            .reset_index()
        )
        calc_counts.columns = ["Result", "Count"]
        calc_counts["Result"] = calc_counts["Result"].fillna("Pending / Not recorded").astype(str)
        fig_ac = px.pie(
            calc_counts, names="Result", values="Count",
            hole=0.42,
            color_discrete_sequence=COLOR_SEQ,
        )
        fig_ac.update_traces(textposition="inside", textinfo="percent+label")
        fig_ac.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_ac, use_container_width=True)

    # SUVR summary
    st.markdown("**SUVR summary**")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        has_avid = amyloid_m["suvr_avid"].notna().any()
        if has_avid:
            fig_savid = px.histogram(
                amyloid_m.dropna(subset=["suvr_avid"]),
                x="suvr_avid", nbins=20,
                color_discrete_sequence=[COLORS["blue"]],
                labels={"suvr_avid": "SUVR (Avid)"},
                title="Amyloid SUVR — Avid",
            )
            fig_savid.update_layout(**PLOTLY_LAYOUT, showlegend=False)
            st.plotly_chart(fig_savid, use_container_width=True)
        else:
            st.info("No SUVR Avid values recorded.")
    with col_s2:
        has_sl = amyloid_m["suvr_sl"].notna().any()
        if has_sl:
            fig_ssl = px.histogram(
                amyloid_m.dropna(subset=["suvr_sl"]),
                x="suvr_sl", nbins=20,
                color_discrete_sequence=[COLORS["teal"]],
                labels={"suvr_sl": "SUVR (SL pipeline)"},
                title="Amyloid SUVR — SL pipeline",
            )
            fig_ssl.update_layout(**PLOTLY_LAYOUT, showlegend=False)
            st.plotly_chart(fig_ssl, use_container_width=True)
        else:
            has_blank = amyloid_m["sl_blankreason"].notna().any()
            if has_blank:
                st.markdown("**SL blank reasons**")
                blank_counts = (
                    amyloid_m["sl_blankreason"]
                    .value_counts().reset_index()
                )
                blank_counts.columns = ["Reason", "Count"]
                st.dataframe(blank_counts, use_container_width=True, hide_index=True)
            else:
                st.info("No SUVR SL values or blank reasons recorded.")

    with st.expander("Amyloid detail table"):
        amyloid_display = (
            amyloid_m[["global_id", "ptid", "scan_date",
                       "read_number_calc", "read_calc", "suvr_avid", "suvr_sl", "sl_blankreason",
                        "core_pt_status"]]
            .sort_values("scan_date", ascending=False)
            .rename(columns={
                "global_id":         "Global ID",
                "ptid":              "PTID",
                "scan_date":         "Scan date",
                "read_number_calc":  "Read number",
                "read_calc":         "Read result",
                "suvr_avid":         "SUVR (Avid)",
                "suvr_sl":           "SUVR (SL)",
                "sl_blankreason":    "SL blank reason",
                "core_pt_status":    "Participant status",
            })
        )
        st.dataframe(amyloid_display, use_container_width=True, hide_index=True)

st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Tau PET clinical reads
# ════════════════════════════════════════════════════════════════════════════════
st.subheader("🔬 Tau PET — Clinical read summary")

if tau_m.empty:
    st.info("No tau records in the selected period.")
else:
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("**Read count distribution**")
        tau_read_counts = (
            tau_m["read_number_calc"]
            .value_counts(dropna=False)
            .reset_index()
        )
        tau_read_counts.columns = ["Read number", "Count"]
        tau_read_counts["Read number"] = tau_read_counts["Read number"].fillna("Not recorded").astype(str)
        fig_tr = px.bar(
            tau_read_counts.sort_values("Read number"),
            x="Read number", y="Count",
            color_discrete_sequence=[COLORS["purple"]],
            text="Count",
        )
        fig_tr.update_traces(textposition="outside")
        fig_tr.update_layout(**PLOTLY_LAYOUT, showlegend=False)
        fig_tr.update_xaxes(title="Number of clinical reads completed")
        st.plotly_chart(fig_tr, use_container_width=True)

    with col_t2:
        st.markdown("**Clinical read result (read_calc)**")
        tau_calc_counts = (
            tau_m["read_calc"]
            .value_counts(dropna=False)
            .reset_index()
        )
        tau_calc_counts.columns = ["Result", "Count"]
        tau_calc_counts["Result"] = tau_calc_counts["Result"].fillna("Pending / Not recorded").astype(str)
        fig_tc = px.pie(
            tau_calc_counts, names="Result", values="Count",
            hole=0.42,
            color_discrete_sequence=[COLORS["purple"], COLORS["amber"], COLORS["gray"]],
        )
        fig_tc.update_traces(textposition="inside", textinfo="percent+label")
        fig_tc.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_tc, use_container_width=True)

    with st.expander("Tau detail table"):
        tau_display = (
            tau_m[["global_id", "ptid", "scan_date",
                   "read_number_calc", "read_calc", "core_pt_status"]]
            .sort_values("scan_date", ascending=False)
            .rename(columns={
                "global_id":         "Global ID",
                "ptid":              "PTID",
                "scan_date":         "Scan date",
                "read_number_calc":  "Read number",
                "read_calc":         "Read result",
                "core_pt_status":    "Participant status",
            })
        )
        st.dataframe(tau_display, use_container_width=True, hide_index=True)

st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 3 — MRI FreeSurfer editing status and version
# ════════════════════════════════════════════════════════════════════════════════
st.subheader("🧲 MRI — FreeSurfer editing status and version")

if mri_m.empty:
    st.info("No MRI records in the selected period.")
else:
    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown("**Editing status breakdown**")
        edit_counts = (
            mri_m["editing_status"]
            .value_counts(dropna=False)
            .reset_index()
        )
        edit_counts.columns = ["Status", "Count"]
        edit_counts["Status"] = edit_counts["Status"].fillna("Not recorded").astype(str)
        edit_color_map = {
            "Edited":       COLORS["teal"],
            "Not Edited":   COLORS["lblue"],
            "Problem":      COLORS["coral"],
            "Excluded":     COLORS["gray"],
            "Not recorded": COLORS["amber"],
        }
        fig_edit = px.bar(
            edit_counts, x="Status", y="Count",
            color="Status",
            color_discrete_map=edit_color_map,
            text="Count",
        )
        fig_edit.update_traces(textposition="outside")
        fig_edit.update_layout(**PLOTLY_LAYOUT, showlegend=False)
        fig_edit.update_xaxes(title=None)
        st.plotly_chart(fig_edit, use_container_width=True)

    with col_m2:
        st.markdown("**FreeSurfer version in use**")
        ver_counts = (
            mri_m["version"]
            .value_counts(dropna=False)
            .reset_index()
        )
        ver_counts.columns = ["Version", "Count"]
        ver_counts["Version"] = ver_counts["Version"].fillna("Not recorded").astype(str)
        fig_ver = px.pie(
            ver_counts, names="Version", values="Count",
            hole=0.42,
            color_discrete_sequence=COLOR_SEQ,
        )
        fig_ver.update_traces(textposition="inside", textinfo="percent+label")
        fig_ver.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_ver, use_container_width=True)

    # Editing status × FS version cross-tab
    st.markdown("**Editing status × FreeSurfer version**")
    cross = (
        mri_m.groupby(
            [mri_m["editing_status"].fillna("Not recorded"),
             mri_m["version"].fillna("Not recorded")]
        )
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"editing_status": "Editing status"})
    )
    st.dataframe(cross, use_container_width=True, hide_index=True)

    # Sequences scanned
    if mri_m["sequences_scanned"].notna().any():
        st.divider()
        st.markdown("**MRI sequences scanned (count per scan)**")
        fig_seq = px.histogram(
            mri_m, x="sequences_scanned_count",
            color_discrete_sequence=[COLORS["blue"]],
            labels={"sequences_scanned_count": "Number of sequences scanned"},
            nbins=8,
        )
        fig_seq.update_layout(**PLOTLY_LAYOUT, showlegend=False)
        st.plotly_chart(fig_seq, use_container_width=True)

    with st.expander("MRI detail table"):
        mri_display = (
            mri_m[["global_id", "ptid", "scan_date", "sequences_scanned",
                    "sequences_scanned_count", "editing_status", "version", "core_pt_status"]]
            .sort_values("scan_date", ascending=False)
            .rename(columns={
                "global_id":               "Global ID",
                "ptid":                    "PTID",
                "scan_date":               "Scan date",
                "sequences_scanned":       "Sequences scanned",
                "sequences_scanned_count": "# sequences",
                "editing_status":          "Editing status",
                "version":                 "FS version",
                "core_pt_status":          "Participant status",
            })
        )
        st.dataframe(mri_display, use_container_width=True, hide_index=True)
