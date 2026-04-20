# Imaging Dashboard
> **Status: Active**
 
An interactive multi-page Streamlit dashboard that extends the [Imaging Report](../imaging_report/imaging_report.Rmd) with real-time participant eligibility tracking, scan completion runsheets, and post-scan metrics for the Mesulam Center Imaging Core.
 
---
 
## Features
 
### 🏠 Home (`Home.py`)
- Summary KPIs: unique participants imaged, total scans performed, total cancellations, and participants passed screening
- Study snapshot pivot table — performed scans broken down by study affiliation and modality
- Cancellation breakdown by study and scan type
- Links to all sub-pages via the sidebar
### 📋 Eligibility (`pages/1_Eligibility.py`)
- KPIs: total eligibility records, passed screening, screen fails, pending, and scheduled after screening
- Eligibility status by modality (MRI vs. PET), grouped bar chart
- Screen-fail reason breakdown (donut chart)
- Burdensome screen-fail sub-reasons (horizontal bar chart)
- Monthly eligibility activity trend
- PET modality scheduled/pending detail tables
- Full eligibility detail log with sortable date column
### 🖥️ Scan Completion (`pages/2_Scan_Completion.py`)
- KPIs: total scan records, performed count, canceled count with rate deltas, and unique participants scanned
- Performed scans by modality and study affiliation (stacked bar chart)
- Completion rate by scan type (horizontal bar chart)
- Monthly scan volume by confirmation status
- Cancellation reason analysis: top reasons and breakdown by scan type (1st vs. 2nd occurrence)
- Full runsheet detail table
### 📊 Scan Metrics (`pages/3_Scan_Metrics.py`)
- KPIs: MRI record count, Amyloid record count, Tau record count, Amyloid reads complete (≥ 2), Tau reads complete
- **Amyloid PET:** read count distribution, clinical read result (donut), SUVR histograms (Avid and SL pipeline), SL blank reason table
- **Tau PET:** read count distribution, clinical read result (donut)
- **MRI:** FreeSurfer editing status breakdown, FreeSurfer version in use (donut), editing status × FS version cross-tab, sequences scanned histogram
- Expandable detail tables for each modality
---
 
## Tech Stack
 
| Component       | Tool                                    |
|-----------------|-----------------------------------------|
| Framework       | Python · Streamlit (multi-page)         |
| Charts          | Plotly Express / Plotly Graph Objects   |
| Data wrangling  | pandas · NumPy                          |
| Data source     | REDCap API (`requests`)                 |
| Caching         | `@st.cache_data` (1-hour TTL)           |
| Credentials     | `redcap_api_info.py` via OneDrive       |
 
---
 
## File Structure
 
```
imaging_dashboard/
├── README.md
├── Home.py                         # Landing page and summary KPIs
├── pages/
│   ├── 1_Eligibility.py            # Eligibility tracking page
│   ├── 2_Scan_Completion.py        # Scan runsheet / completion page
│   └── 3_Scan_Metrics.py          # Post-scan metrics page
└── utils/
    ├── data_loader.py              # REDCap API pulls, cleaning, and caching
    ├── sidebar.py                  # Shared sidebar filters (rendered on every page)
    └── constants.py                # Colors, date ranges, scan types, filter helpers
```
 
---
 
## Data Architecture
 
`data_loader.load_all_data()` is the single entry point for all pages. It pulls from two REDCap projects (UDS4 and Imaging), cleans and merges the results, and returns three cached DataFrames:
 
| DataFrame       | Grain                              | Key columns                                                                 |
|-----------------|------------------------------------|-----------------------------------------------------------------------------|
| `elig_final`    | One row per participant × modality | `global_id`, `ptid`, `modality`, `eligibility_date`, `elig_status`, `screen_fail`, `sf_burdensome`, `scheduled`, `core_pt_status` |
| `scan_final`    | One row per participant × scan type | `global_id`, `ptid`, `scan_type`, `study_affiliation`, `scan_date`, `scan_confirmation`, `scan_canceled_1x/2x`, `scan_canceled_reason_1x/2x`, `scanner`, `tracer`, `visit_diagnosis`, `core_pt_status` |
| `metrics_final` | One row per participant × modality | `global_id`, `ptid`, `scan_date`, `modality`, `sequences_scanned`, `editing_status`, `version`, `read_number_calc`, `read_calc`, `suvr_avid`, `suvr_sl`, `sl_blankreason`, `core_pt_status` |
 
Data is cached for one hour (`ttl=3600`) to avoid redundant API calls while navigating between pages.
 
---
 
## Sidebar Filters
 
The shared sidebar (rendered on every page via `render_sidebar()`) exposes:
 
| Filter               | Options                                                     |
|----------------------|-------------------------------------------------------------|
| KPI date range       | Overall, EAC (Feb 2025 – Jan 2026), RPPR (Feb 2025 – Jun 2026), Budget year (Jul 2025 – Jun 2026) |
| Participant status   | Actively Followed, Minimal Contact, Discontinued, Deceased  |
| Study affiliation    | Dynamically populated from `scan_final`                     |
 
---
 
## Setup
 
### Prerequisites
- Python 3.10+
- Required packages: `streamlit`, `pandas`, `numpy`, `plotly`, `requests`
```bash
pip install streamlit pandas numpy plotly requests
```
 
### Credential Configuration
 
The dashboard reads API tokens from a file named `redcap_api_info.py` located in your OneDrive root:
 
```
~/OneDrive - Northwestern University/redcap_api_info.py
```
 
That file should define the following variables:
 
```python
url            = "https://redcap.northwestern.edu/api/"
uds4_token     = "YOUR_UDS4_TOKEN"
imaging_token  = "YOUR_IMAGING_TOKEN"
```
 
See the root [README](../README.md) for the full credential setup guide.
 
### Running the Dashboard
 
```bash
streamlit run Home.py
```
 
---
 
## Relationship to the Imaging Report
 
This dashboard is a live companion to `imaging_report.Rmd`. The static R Markdown report continues to serve as the formal deliverable for grant reporting; this dashboard provides an interactive, real-time view of the same underlying REDCap data for day-to-day monitoring by the Imaging Core team.
 
---
 
## Notes
- Eligibility records are anti-joined against `scan_final` so that participants who have already been scanned do not appear in the eligibility queue
- The sidebar study filter is populated dynamically from live data, so new studies appear automatically without any code changes
- All Plotly charts use a shared `PLOTLY_LAYOUT` and color palette defined in `constants.py` for visual consistency across pages
