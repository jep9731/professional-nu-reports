"""
2_Scan_Completion.py
Scan completion / runsheet page — uses scan_final from data_loader.
Columns: global_id, ptid, scan_type, study_affiliation, scan_date,
         scan_confirmation, scan_canceled_1x, scan_canceled_reason_1x,
         scan_canceled_2x, scan_canceled_reason_2x, scanner, tracer,
         visit_diagnosis, core_pt_status
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_all_data
from utils.sidebar import render_sidebar
from utils.constants import filter_scans, SCAN_TYPES, COLORS, COLOR_SEQ, PLOTLY_LAYOUT

st.set_page_config(
    page_title="Scan Completion · ADRC Imaging",
    page_icon="🖥️",
    layout="wide",
)

_, scan_final, _ = load_all_data()
f = render_sidebar()

s = filter_scans(scan_final, f["statuses"], f["studies"], f["date_start"], f["date_end"])

st.title("🖥️ Scan Completion")
st.caption(
    f"{f['kpi_range']} · "
    f"{f['date_start'].strftime('%b %d, %Y')} – {f['date_end'].strftime('%b %d, %Y')} · "
    )
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total = len(s)

performed_mask = s["scan_confirmation"].eq("Performed")
canceled_mask = s["scan_confirmation"].eq("Canceled")

performed = performed_mask.sum()
canceled  = canceled_mask.sum()

# participants (optional but often more meaningful)
n_participants = s["global_id"].nunique()
performed_participants = s.loc[performed_mask, "global_id"].nunique()
canceled_participants  = s.loc[canceled_mask, "global_id"].nunique()

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total scan records", f"{total:,}")

k2.metric(
    "Performed",
    f"{int(performed):,}",
    delta=f"{performed / total * 100:.1f}% completion" if total else None,
)

k3.metric(
    "Canceled",
    f"{int(canceled):,}",
    delta=f"{canceled / total * 100:.1f}%" if total else None,
    delta_color="inverse",
)

k4.metric(
    "Participants scanned",
    f"{performed_participants:,}"
)

st.divider()

# ── Performed scans: modality × study ────────────────────────────────────────
col_left, col_right = st.columns([1.6, 1])

with col_left:
    st.subheader("Performed scans by modality and study")
    perf_df = s[s["scan_confirmation"] == "Performed"].copy()
    if not perf_df.empty:
        grp = (
            perf_df.groupby(["scan_type", "study_affiliation"])
                   .size()
                   .reset_index(name="Count")
        )
        grp["scan_type"] = pd.Categorical(grp["scan_type"], categories=SCAN_TYPES, ordered=True)
        grp = grp.sort_values("scan_type")
        fig = px.bar(
            grp, x="scan_type", y="Count", color="study_affiliation",
            color_discrete_sequence=COLOR_SEQ,
            labels={"scan_type": "Scan type", "study_affiliation": "Study"},
        )
        fig.update_layout(**PLOTLY_LAYOUT)
        fig.update_xaxes(title=None)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No performed scans for selected filters.")

with col_right:
    st.subheader("Completion rate by scan type")
    rate_df = (
        s.groupby("scan_type")
         .apply(lambda x: pd.Series({
             "Performed": (x["scan_confirmation"] == "Performed").sum(),
             "Total":     len(x),
         }))
         .reset_index()
    )
    rate_df["Rate (%)"] = (rate_df["Performed"] / rate_df["Total"] * 100).round(1)
    rate_df["scan_type"] = pd.Categorical(rate_df["scan_type"], categories=SCAN_TYPES, ordered=True)
    rate_df = rate_df.sort_values("Rate (%)", ascending=True)
    fig_r = px.bar(
        rate_df, x="Rate (%)", y="scan_type", orientation="h",
        color="Rate (%)",
        color_continuous_scale=[[0, COLORS["lblue"]], [1, COLORS["blue"]]],
        range_x=[0, 100],
        labels={"scan_type": ""},
        text="Rate (%)",
    )
    fig_r.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_r.update_coloraxes(showscale=False)
    fig_r.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig_r, use_container_width=True)

st.divider()

# ── Monthly scan volume ───────────────────────────────────────────────────────
st.subheader("Monthly scan volume by confirmation status")
if not s.empty:
    monthly = (
        s.assign(month=pd.to_datetime(s["scan_date"]).dt.to_period("M").astype(str))
         .groupby(["month", "scan_confirmation"])
         .size()
         .reset_index(name="Count")
    )
    fig_m = px.bar(
        monthly, x="month", y="Count", color="scan_confirmation",
        color_discrete_map={
            "Performed": COLORS["teal"],
            "Canceled":  COLORS["coral"],
        },
        labels={"month": "Month", "scan_confirmation": "Status"},
    )
    fig_m.update_layout(**PLOTLY_LAYOUT)
    fig_m.update_xaxes(tickangle=-45, title=None)
    st.plotly_chart(fig_m, use_container_width=True)

st.divider()

# ── Cancellation reason analysis ─────────────────────────────────────────────
st.subheader("Cancellation reasons")
can_rows = []
for _, row in s.iterrows():
    if row["scan_confirmation"] == "Canceled":
        for occurrence, reason_col in [
            ("1st", "scan_canceled_reason_1x"),
            ("2nd", "scan_canceled_reason_2x"),
        ]:
            if pd.notna(row.get(reason_col)):
                can_rows.append({
                    "scan_type": row["scan_type"],
                    "study": row["study_affiliation"],
                    "occurrence": occurrence,
                    "reason": row.get(reason_col, "Not recorded"),
                })

if can_rows:
    can_df = pd.DataFrame(can_rows)
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        reason_counts = (
            can_df["reason"].dropna()
            .value_counts().reset_index()
        )
        reason_counts.columns = ["Reason", "Count"]
        fig_can = px.bar(
            reason_counts.head(10),
            x="Count", y="Reason", orientation="h",
            color_discrete_sequence=[COLORS["coral"]],
            labels={"Reason": ""},
        )
        fig_can.update_layout(**PLOTLY_LAYOUT, showlegend=False, title="Top cancellation reasons")
        st.plotly_chart(fig_can, use_container_width=True)

    with col_c2:
        by_scan = (
            can_df.groupby(["scan_type", "occurrence"])
                  .size().reset_index(name="Count")
        )
        fig_byscan = px.bar(
            by_scan, x="scan_type", y="Count", color="occurrence",
            color_discrete_map={"1st": COLORS["amber"], "2nd": COLORS["coral"]},
            labels={"scan_type": "Scan type", "occurrence": "Occurrence"},
            barmode="group",
            title="Cancellations by scan type (1st vs 2nd)",
        )
        fig_byscan.update_layout(**PLOTLY_LAYOUT)
        fig_byscan.update_xaxes(title=None)
        st.plotly_chart(fig_byscan, use_container_width=True)
else:
    st.info("No cancellations recorded in the selected period.")

st.divider()

# ── Detail table ──────────────────────────────────────────────────────────────
st.subheader("Scan completion detail")
display = (
    s[["global_id", "ptid", "scan_type", "study_affiliation", "scan_date",
       "scan_confirmation", "scan_canceled_1x", "scan_canceled_reason_1x",
       "scan_canceled_2x", "scan_canceled_reason_2x",
       "scanner", "tracer", "visit_diagnosis", "core_pt_status"]]
    .sort_values("scan_date", ascending=False)
    .rename(columns={
        "global_id":               "Global ID",
        "ptid":                    "PTID",
        "scan_type":               "Scan type",
        "study_affiliation":       "Study",
        "scan_date":               "Scan date",
        "scan_confirmation":       "Confirmation",
        "scan_canceled_1x":        "Canceled 1×",
        "scan_canceled_reason_1x": "Cancel reason 1×",
        "scan_canceled_2x":        "Canceled 2×",
        "scan_canceled_reason_2x": "Cancel reason 2×",
        "scanner":                 "Scanner",
        "tracer":                  "Tracer",
        "visit_diagnosis":         "Visit diagnosis",
        "core_pt_status":          "Participant status",
    })
)
st.dataframe(display, use_container_width=True, hide_index=True, height=420)
