# Imaging Report
 
An automated R Markdown report that generates a comprehensive HTML summary of multi-modal PET/MRI imaging activity for the Mesulam Center Imaging Core. The report pulls live data from REDCap, produces `ggplot2` visualizations and `gt` summary tables across multiple reporting periods, and is rendered automatically every week via a cron job.
 
---
 
## Files
 
| File | Purpose |
|---|---|
| `imaging_report.Rmd` | Main R Markdown report — pulls REDCap data, builds all plots and tables, renders to HTML |
| `run_imaging_report.R` | Wrapper script that renders the report programmatically with error handling and logging |
| `setup_cron.R` | Schedules `run_imaging_report.R` to run automatically every Tuesday at 9:00 AM |
 
---
 
## Report Structure
 
The report is divided into two major sections, each covering a different scope of imaging activity.
 
### Section 1 — Overall Mesulam Institute Imaging
 
Covers all confirmed scans across every study affiliated with the Mesulam Institute.
 
| Output | Description |
|---|---|
| Graph 1 | Total scans by modality (all studies, all time) |
| Graph 2 | Total **unique** participants scanned by modality (all studies, all time) |
| Graph 3 | MRI sequences acquired during the previous grant period (7/1/21–5/31/25) |
| Graph 4 | MRI sequences acquired during the RPPR period (2/1/25–6/30/26) |
| Graph 5 | Longitudinal scan timeline — all participants by modality over time |
| Graph 6 | RPPR snapshot scan timeline (2/1/25–present) |
 
MRI sequences tracked: FLAIR, T1 structural, T2 structural, rsfMRI, dMRI.
 
### Section 2 — Imaging Core Scans
 
Filtered to `ADRC_IC` study affiliation only (with an additional EAC section including CLARiTI). Covers longitudinal history from 2018 to present, plus three period-specific breakdowns.
 
**Longitudinal (2018–Present)**
 
| Output | Description |
|---|---|
| Graph 1 + Table 1 | Total longitudinal scans by modality |
| Graph 2 + Table 2 | Total **unique** participants scanned by modality |
| Graph 3 + Table 3 | Total longitudinal scans by diagnosis at time of scan |
| Graph 4 + Table 4 | Total **unique** scans by diagnosis at time of scan |
 
**RPPR Year 5 (2/1/25–6/30/26)**
 
| Output | Description |
|---|---|
| Graph 5 + Table 5 | Scan counts by modality |
| Graph 6 + Table 6 | Scan counts by modality and diagnosis at scan |
| Table 7 (cross-tab) | Unique participants by modality × diagnosis |
 
**Budget Year (7/1/25–6/30/26)**
 
| Output | Description |
|---|---|
| Graph 7 + Table 7 | Scan counts by modality |
 
**EAC Meeting (2/1/25–1/31/26) — ADRC\_IC + CLARiTI**
 
| Output | Description |
|---|---|
| Graph 1 + Table 1 | Scan counts by modality and study affiliation (stacked bar + cross-tab) |
 
---
 
## Diagnoses Tracked
 
Participant diagnoses at time of scan are decoded from REDCap raw values and include: NC, MCI, Amnestic Dementia, Non-Amnestic Dementia, Impaired Not MCI, bvFTD, PPA, Posterior Cortical Atrophy, Corticobasal Syndrome, Progressive Supranuclear Palsy Syndrome, and Lewy Body Dementia. Cases not yet presented at consensus conference appear as `NA`.
 
---
 
## Credential Setup
 
The report reads API tokens from `redcap_api_info.R`, which must exist in your OneDrive root and is never committed to this repository.
 
**File location:**
```
~/OneDrive - Northwestern University/redcap_api_info.R
```
 
**Required contents:**
```r
# redcap_api_info.R  ← DO NOT COMMIT THIS FILE
url            <- "https://redcap.yourInstitution.edu/api/"
imaging_token  <- "YOUR_IMAGING_REDCAP_TOKEN"
```
 
The report locates this file automatically using `Sys.info()[["user"]]` to resolve the OneDrive path on macOS. No manual `setwd()` is needed.
 
---
 
## Required R Packages
 
```r
install.packages(c(
  "tidyverse",   # Data wrangling, ggplot2, pivot_longer
  "redcapAPI",   # REDCap API interface
  "httr",        # HTTP requests for API pulls
  "janitor",     # Data cleaning utilities
  "gt",          # Publication-quality summary tables
  "writexl",     # Excel export (if needed)
  "readxl",      # Excel import (if needed)
  "rmarkdown",   # Report rendering (run_imaging_report.R)
  "cronR"        # Cron scheduling (setup_cron.R, macOS/Linux only)
))
```
 
---
 
## Running the Report
 
### Manually (RStudio)
 
Open `imaging_report.Rmd` in RStudio and click **Knit**. The HTML output will be saved to the same directory as the `.Rmd` file.
 
### Manually (command line / script)
 
Run `run_imaging_report.R` directly. This renders the report programmatically to the configured network output path and appends a timestamped entry to `imaging_report.log`:
 
```r
source("run_imaging_report.R")
```
 
Output is written to:
```
/Volumes/fsmresfiles/CNADC/Imaging_Core/Imaging/imaging_projects/Imaging_report/
```
 
### Automatically (cron — macOS/Linux)
 
Run `setup_cron.R` once to register the weekly cron job:
 
```r
source("setup_cron.R")
```
 
This schedules `run_imaging_report.R` to run every **Tuesday at 9:00 AM** using the `cronR` package. The cron job ID is `weekly_imaging_report`. To remove it:
 
```r
library(cronR)
cron_rm("weekly_imaging_report")
```
 
> **Note:** `setup_cron.R` requires the `fsmresfiles` network volume to be mounted and RStudio to be installed at the default macOS path (`/Applications/RStudio.app/...`). The pandoc path is set explicitly in `run_imaging_report.R` to ensure the cron environment can locate it.
 
---
 
## Output
 
The report renders to a self-contained HTML file (`imaging_report.html`) saved to the shared network drive. All rendered outputs are excluded from version control via `.gitignore`. A log file (`imaging_report.log`) in the same directory records each render attempt with timestamps and any errors.
