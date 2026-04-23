# data_loader.py
# Centralizes all REDCap API pulls and data cleaning for the Neuroimaging Dashboard.
# Import this module in each page and call load_all_data() to get cached dataframes.
#
# Usage in any page file:
#   from data_loader import load_all_data
#   elig_final, scan_final, metrics_final = load_all_data()
 
import requests
import pandas as pd
import numpy as np
import streamlit as st
from io import StringIO
from pathlib import Path
import os
 
 
# ---------------------------------------------------------------------------
# Token / config loading
# ---------------------------------------------------------------------------
 
def _load_tokens() -> dict:
    """
    Locate and exec redcap_api_info.py from OneDrive, returning all variables
    it defines (including uds4_token, imaging_token, url) as a dict.
    Raises FileNotFoundError if the file cannot be located.
    """
    home = str(Path.home())
    od_loc = os.path.join(home, "OneDrive - Northwestern University")
    token_path = Path(od_loc) / "redcap_api_info.py"
 
    if not token_path.exists():
        raise FileNotFoundError(
            f"REDCap token file not found: {token_path}\n"
            "Ensure redcap_api_info.py exists in your OneDrive root."
        )
 
    namespace: dict = {}
    with open(token_path, "r") as f:
        exec(f.read(), namespace)  # noqa: S102
    return namespace
 
 
# ---------------------------------------------------------------------------
# Helper: collapse REDCap checkboxes
# ---------------------------------------------------------------------------
 
def _collapse_redcap_checkboxes(df: pd.DataFrame, prefix: str, new_col: str) -> pd.DataFrame:
    """Collapse REDCap checkbox columns (prefix___choice) into a single comma-separated column."""
    checkbox_cols = [col for col in df.columns if col.startswith(f"{prefix}___")]
    if not checkbox_cols:
        return df
    df[new_col] = df[checkbox_cols].apply(
        lambda row: ",".join(
            col.split("___")[1] for col in checkbox_cols if row[col] == 1
        ),
        axis=1,
    )
    return df.drop(columns=checkbox_cols)
 
 
# ---------------------------------------------------------------------------
# Raw pulls
# ---------------------------------------------------------------------------
 
def _pull_uds4(url: str, token: str) -> pd.DataFrame:
    formData = {
        "token": token,
        "content": "record",
        "format": "csv",
        "type": "flat",
        "csvDelimiter": "",
        "fields[0]": "global_id",
        "fields[1]": "ptid",
        "fields[2]": "core_pt_status",
        "rawOrLabel": "raw",
        "exportCheckboxLabel": "false",
        "exportSurveyFields": "true",
        "exportDataAccessGroups": "false",
        "returnFormat": "csv",
    }
    response = requests.post(url, data=formData, timeout=60)
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text))
    df["ptid"] = df.groupby("global_id")["ptid"].ffill()
    df["core_pt_status"] = df.groupby("global_id")["core_pt_status"].ffill()
    return df
 
 
def _pull_imaging(url: str, token: str) -> pd.DataFrame:
    formData = {
        "token": token,
        "content": "record",
        "format": "csv",
        "type": "flat",
        "csvDelimiter": "",
        # Stub
        "fields[0]": "global_id",
        "fields[1]": "ptid",
        # Eligibility
        "fields[2]": "eligibility_date",
        "fields[3]": "elig_status_mri",
        "fields[4]": "screen_fail_mri",
        "fields[5]": "sf_burdensome_mri",
        "fields[6]": "mri_scheduled",
        "fields[7]": "eligibility_date_pet",
        "fields[8]": "elig_status_pet",
        "fields[9]": "screen_fail_pet",
        "fields[10]": "sf_burdensome_pet",
        "fields[11]": "scheduled_pet_2",
        "fields[12]": "petmodality_elig_yes",
        "fields[13]": "petmodality_elig_pending",
        # Runsheets
        "fields[14]": "study_affiliation_mri",
        "fields[15]": "scan_occur_confirmation_mri",
        "fields[16]": "scan_canceled_mri_1x",
        "fields[17]": "scan_canceled_reason_mri_1x",
        "fields[18]": "scan_canceled_mri_2x",
        "fields[19]": "scan_canceled_reason_mri_2x",
        "fields[20]": "mri_date",
        "fields[21]": "mri_scanner",
        "fields[22]": "study_affiliation_amyloid",
        "fields[23]": "scan_occur_confirmation_amyloid",
        "fields[24]": "scan_canceled_amyloid",
        "fields[25]": "scan_canceled_reason_amyloid",
        "fields[26]": "scan_canceled_amyloid_2x",
        "fields[27]": "scan_canceled_reason_amyloid_2x",
        "fields[28]": "amyloid_date",
        "fields[29]": "pet_tracer_amyloid",
        "fields[30]": "pet_scanner_amyloid",
        "fields[31]": "study_affiliation_tau",
        "fields[32]": "scan_occur_confirmation_tau",
        "fields[33]": "scan_canceled_tau",
        "fields[34]": "scan_canceled_reason_tau",
        "fields[35]": "scan_canceled_tau_2x",
        "fields[36]": "scan_canceled_reason_tau_2x",
        "fields[37]": "tau_date",
        "fields[38]": "pet_tracer_tau",
        "fields[39]": "pet_scanner_tau",
        "fields[40]": "study_affiliation_fdg",
        "fields[41]": "scan_occur_confirmation_fdg",
        "fields[42]": "scan_canceled_fdg",
        "fields[43]": "scan_canceled_reason_fdg",
        "fields[44]": "scan_canceled_fdg_2x",
        "fields[45]": "scan_canceled_reason_fdg_2x",
        "fields[46]": "fdg_date",
        "fields[47]": "pet_tracer_fdg",
        "fields[48]": "pet_scanner_fdg",
        "fields[49]": "mc_calcdx_visit_mri",
        "fields[50]": "mc_calcdx_visit_amyloid",
        "fields[51]": "mc_calcdx_visit_tau",
        "fields[52]": "mc_calcdx_visit_fdg",
        # Metrics
        "fields[53]": "flair_sequence_scanned",
        "fields[54]": "t1_structural_sequence_scanned",
        "fields[55]": "t2_structural_sequence_scanned",
        "fields[56]": "rsfmri_sequence_scanned",
        "fields[57]": "dif_sequence_scanned",
        "fields[58]": "fs_editing_status",
        "fields[59]": "fs_version",
        "fields[60]": "amyloid_read_number_calc",
        "fields[61]": "amyloid_read_calc",
        "fields[62]": "amyloid_suvr_avid",
        "fields[63]": "amyloid_suvr_sl",
        "fields[64]": "amyloid_suvr_sl_blankreason",
        "fields[65]": "tau_read_number_calc",
        "fields[66]": "tau_read_calc",
        "rawOrLabel": "raw",
        "exportCheckboxLabel": "false",
        "exportSurveyFields": "true",
        "exportDataAccessGroups": "false",
        "returnFormat": "csv",
    }
    response = requests.post(url, data=formData, timeout=60)
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text))
 
    # Fill ptid from tracking arm
    ptid_map = (
        df[df["redcap_event_name"] == "tracking_arm_1"]
        .set_index("global_id")["ptid"]
    )
    df["ptid"] = df["ptid"].fillna(df["global_id"].map(ptid_map))
 
    # Rename columns
    df.rename(
        columns={
            "eligibility_date": "eligibility_date_mri",
            "scheduled_pet_2": "pet_scheduled"
        },
        inplace=True,
    )
 
    # Keep only imaging visit rows
    df = df[df["redcap_event_name"] == "imaging_visit_arm_1"]
 
    # Drop ___998/997/996/995 columns
    df = df.drop(df.filter(regex=r"___\d{3}").columns, axis=1).copy()
 
    # Collapse checkbox groups
    checkbox_fields = [
        ("screen_fail_mri", "screen_fail_mri"),
        ("sf_burdensome_mri", "sf_burdensome_mri"),
        ("screen_fail_pet", "screen_fail_pet"),
        ("sf_burdensome_pet", "sf_burdensome_pet"),
        ("scheduled_pet_2", "pet_scheduled"),
        ("petmodality_elig_yes", "pet_modality_scheduled"),
        ("petmodality_elig_pending", "pet_modality_pending"),
        ("scan_canceled_reason_mri_1x", "scan_canceled_reason_mri_1x"),
        ("scan_canceled_reason_mri_2x", "scan_canceled_reason_mri_2x"),
        ("scan_canceled_reason_amyloid", "scan_canceled_reason_amyloid"),
        ("scan_canceled_reason_amyloid_2x", "scan_canceled_reason_amyloid_2x"),
        ("scan_canceled_reason_tau", "scan_canceled_reason_tau"),
        ("scan_canceled_reason_tau_2x", "scan_canceled_reason_tau_2x"),
        ("scan_canceled_reason_fdg", "scan_canceled_reason_fdg"),
        ("scan_canceled_reason_fdg_2x", "scan_canceled_reason_fdg_2x"),
        ("fs_version", "fs_version"),
    ]
    for prefix, new_col in checkbox_fields:
        df = _collapse_redcap_checkboxes(df, prefix, new_col)
 
    return df
 
 
# ---------------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------------
 
def _clean_uds4(raw: pd.DataFrame) -> pd.DataFrame:
    status_map = {
        "actv": "Actively Followed",
        "dec": "Deceased",
        "disc": "Discontinued",
        "min": "Minimal Contact",
    }
    raw["core_pt_status"] = raw["core_pt_status"].map(status_map)
    clean = (
        raw[["global_id", "ptid", "core_pt_status"]]
        .dropna(subset=["ptid"])
        .astype({"global_id": str, "ptid": int, "core_pt_status": str})
    )
    return clean
 
 
def _build_scan_final(imaging_df: pd.DataFrame, uds4_clean: pd.DataFrame) -> pd.DataFrame:

    BASE_COLS = [
    "global_id",
    "ptid",
    ]

    SCAN_COLS = [
    # MRI (stable)
    "study_affiliation_mri",
    "scan_occur_confirmation_mri",
    "scan_canceled_mri_1x",
    "scan_canceled_reason_mri_1x",
    "scan_canceled_mri_2x",
    "scan_canceled_reason_mri_2x",
    "mri_date",
    "mri_scanner",
    "mc_calcdx_visit_mri",

    # Amyloid (robust handling below)
    "study_affiliation_amyloid",
    "scan_occur_confirmation_amyloid",
    "scan_canceled_amyloid",
    "scan_canceled_reason_amyloid",
    "scan_canceled_amyloid_2x",
    "scan_canceled_reason_amyloid_2x",
    "amyloid_date",
    "pet_tracer_amyloid",
    "pet_scanner_amyloid",
    "mc_calcdx_visit_amyloid",

    # Tau
    "study_affiliation_tau",
    "scan_occur_confirmation_tau",
    "scan_canceled_tau",
    "scan_canceled_reason_tau",
    "scan_canceled_tau_2x",
    "scan_canceled_reason_tau_2x",
    "tau_date",
    "pet_tracer_tau",
    "pet_scanner_tau",
    "mc_calcdx_visit_tau",

    # FDG
    "study_affiliation_fdg",
    "scan_occur_confirmation_fdg",
    "scan_canceled_fdg",
    "scan_canceled_reason_fdg",
    "scan_canceled_fdg_2x",
    "scan_canceled_reason_fdg_2x",
    "fdg_date",
    "pet_tracer_fdg",
    "pet_scanner_fdg",
    "mc_calcdx_visit_fdg",
    ]

    scan_df = imaging_df[BASE_COLS + [c for c in SCAN_COLS if c in imaging_df.columns]].copy()

    # -----------------------------
    # VALUE MAPS
    # -----------------------------
    amyloid_tracer_map = {
        1: "18F-Florbetapir",
        2: "18F-Florbetaben",
        3: "Flutafuranol (NAV4694)"
    }

    tau_tracer_map = {
        1: "Flortaucipir (F-AV-1451)",
        2: "MK-6240",
        3: "PI-2620"
    }

    fdg_tracer_map = {1: "Fludeoxyglucose"}

    pet_scanner_map = {
        1: "BioGraph 40 TrueV",
        2: "BioGraph Vision"
    }

    mri_scanner_map = {
        1: "TRIO",
        2: "Prisma - VE11C",
        3: "Prisma - XA60"
    }

    canceled_mri_map = {
        "1": "Participant did not come",
        "2": "Contraindication discovered at the scanner",
        "3": "Participant refused to enter scanner",
        "4": "Participant physical limitations",
        "5": "Scanner issue",
        "6": "Other",
    }

    cancel_pet_map = {
        "1": "Ligand manufacturing issue",
        "2": "Dose delivery issue",
        "3": "Dose out of range",
        "4": "Participant no show",
        "5": "Participant refusal",
        "6": "Injection issue",
        "7": "Scanner issue",
        "8": "Scheduling issue",
        "9": "Scan lost",
        "10": "Other",
    }

    visit_dx_map = {
        1: "Behavioral Variant Frontotemporal Dementia",
        3: "Mild Cognitive Impairment",
        5: "Normal Control",
        6: "Lewy Body Dementia",
        10: "Posterior Cortical Atrophy",
        11: "Progressive Supranuclear Palsy Syndrome",
        13: "Amnestic Multidomain Dementia Syndrome",
        14: "Primary Progressive Aphasia",
        16: "Corticobasal Syndrome",
        21: "Non-Amnestic Multidomain Dementia",
        22: "Impaired Not MCI",
    }

    # -----------------------------
    # APPLY MAPPINGS (vectorized)
    # -----------------------------
    for col in scan_df.columns:
        if col.startswith("pet_tracer_amyloid"):
            scan_df[col] = scan_df[col].map(amyloid_tracer_map)
        elif col.startswith("pet_tracer_tau"):
            scan_df[col] = scan_df[col].map(tau_tracer_map)
        elif col.startswith("pet_tracer_fdg"):
            scan_df[col] = scan_df[col].map(fdg_tracer_map)
        elif col.startswith("pet_scanner"):
            scan_df[col] = scan_df[col].map(pet_scanner_map)
        elif col.startswith("mri_scanner"):
            scan_df[col] = scan_df[col].map(mri_scanner_map)
        elif col.startswith("scan_canceled_reason_mri"):
            scan_df[col] = scan_df[col].map(canceled_mri_map)
        elif "scan_canceled_reason_" in col:
            scan_df[col] = scan_df[col].map(cancel_pet_map)
        elif col.startswith("mc_calcdx_visit"):
            scan_df[col] = scan_df[col].map(visit_dx_map)

    # -----------------------------
    # LONG FORMAT SPECS
    # -----------------------------
    SCAN_TYPES = {
        "MRI": "mri",
        "Amyloid": "amyloid",
        "Tau": "tau",
        "FDG": "fdg",
    }

    COMMON_COLS = [
        "study_affiliation",
        "scan_confirmation",
        "scan_canceled_1x",
        "scan_canceled_reason_1x",
        "scan_canceled_2x",
        "scan_canceled_reason_2x",
        "date",
        "tracer",
        "scanner",
        "mc_calcdx_visit",
    ]

    chunks = []

    # -----------------------------
    # BUILD LONG DATASET (FIXED)
    # -----------------------------
    for scan_type, p in SCAN_TYPES.items():

        if p == "mri":
            cols = [
                f"study_affiliation_{p}",
                f"scan_occur_confirmation_{p}",
                f"scan_canceled_{p}_1x",
                f"scan_canceled_reason_{p}_1x",
                f"scan_canceled_{p}_2x",
                f"scan_canceled_reason_{p}_2x",
                f"{p}_date",
                "mri_scanner",
                f"mc_calcdx_visit_{p}",
            ]
        else:
            cols = [
                f"study_affiliation_{p}",
                f"scan_occur_confirmation_{p}",
                f"scan_canceled_{p}",
                f"scan_canceled_reason_{p}",
                f"scan_canceled_{p}_2x",
                f"scan_canceled_reason_{p}_2x",
                f"{p}_date",
                f"pet_tracer_{p}",
                f"pet_scanner_{p}",
                f"mc_calcdx_visit_{p}",
            ]

        rename_map = dict(zip(cols, COMMON_COLS))

        tmp = scan_df[["global_id", "ptid"] + cols].copy()
        tmp = tmp.rename(columns=rename_map)

        # -----------------------------
        # VECTORISED CONFIRMATION LOGIC
        # -----------------------------
        cancel_cols = [c for c in tmp.columns if "scan_canceled" in c]

        has_cancel = tmp[cancel_cols].notna().any(axis=1)
        confirm = tmp["scan_confirmation"]

        tmp["scan_confirmation"] = np.select(
            [
                has_cancel,
                confirm == 1,
                confirm == 2,
            ],
            [
                "Canceled",
                "Performed",
                "Canceled",
            ],
            default=np.nan
        )

        tmp["scan_type"] = scan_type
        chunks.append(tmp)

    # -----------------------------
    # CONCAT
    # -----------------------------
    scan_long = pd.concat(chunks, ignore_index=True)

    scan_long = scan_long[
        scan_long["scan_confirmation"].isin(["Performed", "Canceled"])
        | scan_long["date"].notna()
    ].copy()

    scan_long["scan_confirmation"] = scan_long["scan_confirmation"].fillna("Unknown")

    # -----------------------------
    # JOIN UDS4
    # -----------------------------
    final = scan_long.merge(uds4_clean, on=["global_id", "ptid"], how="inner")

    final = final.drop_duplicates(
        subset=["global_id", "ptid", "scan_type", "study_affiliation", "date"],
        keep="first",
    )

    final = final.rename(columns={
        "mc_calcdx_visit": "visit_diagnosis",
        "date": "scan_date",
    })

    final["study_affiliation"] = final["study_affiliation"].replace(
        {"Imaging_Core": "ADRC_IC"}
    )

    final["ptid"] = final["ptid"].astype(int)

    return final.sort_values(["global_id", "scan_date"])
 
def _build_elig_final(imaging_df: pd.DataFrame, uds4_clean: pd.DataFrame,
                      scan_final: pd.DataFrame) -> pd.DataFrame:
    elig_df = imaging_df[[
        "global_id", "ptid",
        "eligibility_date_mri", "elig_status_mri", "screen_fail_mri",
        "sf_burdensome_mri", "mri_scheduled",
        "eligibility_date_pet", "elig_status_pet", "screen_fail_pet",
        "sf_burdensome_pet", "pet_scheduled", "pet_modality_scheduled", "pet_modality_pending",
    ]].copy()
 
    stub_cols = ["global_id", "ptid", "eligibility_date_mri", "eligibility_date_pet",
                 "pet_scheduled", "pet_modality_scheduled", "pet_modality_pending"]
    for col in elig_df.columns:
        if col not in stub_cols:
            elig_df[col] = pd.to_numeric(elig_df[col], errors="coerce").astype("Int64")
 
    mri_schedule_map = {1: "Yes", 0: "No"}
    status_map = {1: "Screen Fail", 2: "Passed Screening", 3: "Pending"}
    screen_fail_map = {1: "Contraindication", 2: "Burdensome", 3: "Too Impaired"}
    burdensome_map = {
        1: "Travel", 2: "Working", 3: "Caregiver",
        4: "Claustrophobic", 5: "Other", 6: "General Disinterest",
    }
 
    for col in elig_df.columns[elig_df.columns.str.startswith("mri_scheduled")]:
        elig_df[col] = elig_df[col].map(mri_schedule_map)
    for col in elig_df.columns[elig_df.columns.str.startswith("elig_status")]:
        elig_df[col] = elig_df[col].map(status_map)
    for col in elig_df.columns[elig_df.columns.str.startswith("screen_fail")]:
        elig_df[col] = elig_df[col].map(screen_fail_map)
    for col in elig_df.columns[elig_df.columns.str.startswith("sf_burdensome")]:
        elig_df[col] = elig_df[col].map(burdensome_map)
 
    # Lengthen
    id_vars = ["global_id", "ptid"]
    mri_df = elig_df[id_vars + ["eligibility_date_mri", "elig_status_mri", "screen_fail_mri",
                                 "sf_burdensome_mri", "mri_scheduled"]].rename(columns={
        "eligibility_date_mri": "eligibility_date", "elig_status_mri": "elig_status",
        "screen_fail_mri": "screen_fail", "sf_burdensome_mri": "sf_burdensome",
        "mri_scheduled": "scheduled",
    }).assign(modality="MRI")
 
    pet_df = elig_df[id_vars + ["eligibility_date_pet", "elig_status_pet", "screen_fail_pet",
                                 "sf_burdensome_pet", "pet_scheduled", "pet_modality_scheduled",
                                 "pet_modality_pending"]].rename(columns={
        "eligibility_date_pet": "eligibility_date", "elig_status_pet": "elig_status",
        "screen_fail_pet": "screen_fail", "sf_burdensome_pet": "sf_burdensome",
        "pet_scheduled": "scheduled", "pet_modality_scheduled": "modality_scheduled",
        "pet_modality_pending": "modality_pending",
    }).assign(modality="PET")
 
    elig_long = pd.concat([mri_df, pet_df], ignore_index=True)
    elig_long["scheduled"] = elig_long["scheduled"].str.upper()
 
    # Join UDS4
    merged = pd.merge(elig_long, uds4_clean, how="inner", on=["global_id", "ptid"])
    merged["ptid"] = merged["ptid"].astype(int)
    merged.dropna(subset=["eligibility_date"], inplace=True)
 
    # Anti-join: keep only rows not already in scan_final
    final = merged[~merged["global_id"].isin(scan_final["global_id"])].drop_duplicates()
    final = final.sort_values(["global_id", "eligibility_date"])
    final = final.replace(r"^\s*$", np.nan, regex=True)
    final = final[["global_id", "ptid", "modality", "eligibility_date", "elig_status",
                   "screen_fail", "sf_burdensome", "scheduled", "modality_scheduled",
                   "modality_pending", "core_pt_status"]]
    return final
 
 
def _build_metrics_final(imaging_df: pd.DataFrame, uds4_clean: pd.DataFrame) -> pd.DataFrame:
    metrics_df = imaging_df[[
        "global_id", "ptid",
        "mri_date", "study_affiliation_mri",
        "flair_sequence_scanned", "t1_structural_sequence_scanned",
        "t2_structural_sequence_scanned", "rsfmri_sequence_scanned", "dif_sequence_scanned",
        "fs_editing_status", "fs_version",
        "amyloid_date", "study_affiliation_amyloid", "amyloid_read_number_calc",
        "amyloid_read_calc", "amyloid_suvr_avid", "amyloid_suvr_sl", "amyloid_suvr_sl_blankreason",
        "tau_date", "study_affiliation_tau", "tau_read_number_calc", "tau_read_calc",
    ]].copy()
 
    edit_map = {1: "Not Edited", 2: "Edited", 3: "Problem", 4: "Excluded"}
    fs_version_map = {"1": "5.1.0", "2": "6.0.0", "3": "6.0.0 dev", "4": "7"}
    suvr_sl_blank_map = {
        1: "No proximate MRI", 2: "MRI Cannot be edited",
        3: "Amyloid pipeline failed", 4: "Other",
    }
 
    for col in metrics_df.columns[metrics_df.columns.str.startswith("fs_editing_status")]:
        metrics_df[col] = metrics_df[col].map(edit_map)
    for col in metrics_df.columns[metrics_df.columns.str.startswith("fs_version")]:
        metrics_df[col] = metrics_df[col].map(fs_version_map)
    for col in metrics_df.columns[metrics_df.columns.str.startswith("amyloid_suvr_sl_blankreason")]:
        metrics_df[col] = metrics_df[col].map(suvr_sl_blank_map)

    # Collapse sequences into a single string + count
    seq_cols = [
        "flair_sequence_scanned", "t1_structural_sequence_scanned",
        "t2_structural_sequence_scanned", "rsfmri_sequence_scanned", "dif_sequence_scanned",
    ]
    metrics_df["sequences_scanned"] = metrics_df[seq_cols].apply(
        lambda row: ", ".join(
            c.replace("_sequence_scanned", "").replace("_structural", "")
            for c in seq_cols if row[c] == 1
        ) or None,
        axis=1,
    )
    metrics_df["sequences_scanned_count"] = metrics_df[seq_cols].sum(axis=1)
    metrics_long = metrics_df.drop(columns=seq_cols).copy()
 
    # Lengthen
    id_vars = ["global_id", "ptid"]
    mri_df = metrics_long[id_vars + ["mri_date", "study_affiliation_mri", "sequences_scanned",
                                      "sequences_scanned_count", "fs_editing_status",
                                      "fs_version"]].rename(columns={
        "mri_date": "scan_date", "study_affiliation_mri": "study_affiliation",
        "fs_editing_status": "editing_status", "fs_version": "version",
    }).assign(modality="MRI")
 
    apet_df = metrics_long[id_vars + ["amyloid_date", "study_affiliation_amyloid",
                                       "amyloid_read_number_calc", "amyloid_read_calc",
                                       "amyloid_suvr_avid", "amyloid_suvr_sl",
                                       "amyloid_suvr_sl_blankreason"]].rename(columns={
        "amyloid_date": "scan_date", "study_affiliation_amyloid": "study_affiliation",
        "amyloid_read_number_calc": "read_number_calc", "amyloid_read_calc": "read_calc",
        "amyloid_suvr_avid": "suvr_avid", "amyloid_suvr_sl": "suvr_sl",
        "amyloid_suvr_sl_blankreason": "sl_blankreason",
    }).assign(modality="Amyloid")
 
    tpet_df = metrics_long[id_vars + ["tau_date", "study_affiliation_tau",
                                       "tau_read_number_calc", "tau_read_calc"]].rename(columns={
        "tau_date": "scan_date", "study_affiliation_tau": "study_affiliation",
        "tau_read_number_calc": "read_number_calc", "tau_read_calc": "read_calc",
    }).assign(modality="Tau")
 
    combined = pd.concat([mri_df, apet_df, tpet_df], ignore_index=True)
 
    final = pd.merge(combined, uds4_clean, how="inner", on=["global_id", "ptid"]).drop_duplicates(
        subset=["global_id", "ptid", "scan_date", "modality", "study_affiliation"]
    )
    final.dropna(subset=["scan_date"], inplace=True)
    final = final.sort_values(["global_id", "scan_date"]).reset_index(drop=True)
    final = final.astype(
        {"ptid": "int64", "sequences_scanned_count": "int64", "read_number_calc": "int64"},
        errors="ignore",
    )
    final = final[[
        "global_id", "ptid", "scan_date", "modality", "sequences_scanned",
        "sequences_scanned_count", "editing_status", "version", "read_number_calc",
        "read_calc", "suvr_avid", "suvr_sl", "sl_blankreason", "core_pt_status"
    ]]
    return final
 
 
# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
 
@st.cache_data(ttl=3600, show_spinner="Loading REDCap data...")
def load_all_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Pull and clean all REDCap data. Results are cached for 1 hour (ttl=3600).
    Returns:
        elig_final    – eligibility tracking (one row per participant × modality)
        scan_final    – scan completion / runsheets (one row per participant × scan type)
        metrics_final – scan metrics (one row per participant × modality)
    """
    cfg = _load_tokens()
    url          = cfg["url"]
    uds4_token   = cfg.get("uds4_token")
    imaging_token = cfg.get("imaging_token")
 
    if not uds4_token:
        raise ValueError("uds4_token not found in redcap_api_info.py")
    if not imaging_token:
        raise ValueError("imaging_token not found in redcap_api_info.py")
 
    uds4_raw    = _pull_uds4(url, uds4_token)
    imaging_raw = _pull_imaging(url, imaging_token)
    uds4_clean  = _clean_uds4(uds4_raw)
 
    scan_final    = _build_scan_final(imaging_raw, uds4_clean)
    elig_final    = _build_elig_final(imaging_raw, uds4_clean, scan_final)
    metrics_final = _build_metrics_final(imaging_raw, uds4_clean)
 
    return elig_final, scan_final, metrics_final

