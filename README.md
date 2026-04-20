# Northwestern University — Neuroimaging Analytics Pipeline
 
Clinical research R & Python scripts developed during my role as Clinical Research Coordinator at the Northwestern University Mesulam Center for Cognitive Neurology and Alzheimer's Disease. These scripts support multi-modal PET/MRI imaging data management, quality control, and automated reporting for the Imaging Core.
 
> **Note:** All scripts connect to internal REDCap databases and institutional file systems. No data, credentials, or PHI are included in this repository. See [Credential Setup](#credential-setup) below before running.
 
---
 
## Repository Structure
 
```
professional-nu-reports/
├── amyloid_pet/
│   └── amyloid_reads.R          # Amyloid PET visual/SUVr discrepancy analysis
├── imaging_dashboard/
│   ├── README.md                # Dashboard documentation
│   ├── Home.py                  # Landing page and summary KPIs
│   ├── pages/
│   │   ├── 1_Eligibility.py     # Eligibility tracking page
│   │   ├── 2_Scan_Completion.py # Scan runsheet / completion page
│   │   └── 3_Scan_Metrics.py   # Post-scan metrics page
│   └── utils/
│       ├── data_loader.py       # REDCap API pulls, cleaning, and caching
│       ├── sidebar.py           # Shared sidebar filters
│       └── constants.py         # Colors, date ranges, filter helpers
├── imaging_report/
│   ├── imaging_report.Rmd       # Automated HTML imaging report (R Markdown)
│   ├── run_imaging_report.R     # Script to render the report programmatically
│   └── setup_cron.R             # Schedules weekly report via cron job
└── tau_pet_metrics/
    └── Tau_PET_Metrics.Rmd      # Tau PET read discrepancy analysis & reporting
```
 
---
 
## Scripts Overview
 
### `amyloid_pet/amyloid_reads.R`
Pulls and cleans Amyloid PET data from two methods — **IBC (Imaging Core)** and **GAAIN (UC Berkeley)** — then identifies discrepancies between visual clinical reads and quantitative SUVr/Centiloid values. Produces four `ggplot2` visualizations and exports discrepancy tables to Excel.
 
**Key techniques:** REDCap API, `tidyverse`, `ggplot2`, `ggrepel`, multi-source data merging, threshold-based QC flagging.
 
---
 
### `imaging_dashboard/` 
An interactive multi-page Streamlit dashboard and live companion to `imaging_report.Rmd`. Provides real-time participant eligibility tracking, scan completion runsheets, and post-scan metrics for day-to-day Imaging Core monitoring. Data is pulled directly from two REDCap projects (UDS4 and Imaging) and cached for one hour per session.
 
**Pages:**
- **Home** — Summary KPIs, study snapshot pivot table, and cancellation breakdown
- **Eligibility** — Screening status by modality, screen-fail reasons, burdensome sub-reasons, and monthly activity trend
- **Scan Completion** — Performed vs. canceled scans by modality and study, completion rates, monthly volume, and cancellation reason analysis
- **Scan Metrics** — Amyloid PET clinical reads and SUVR distributions, Tau PET read summary, MRI FreeSurfer editing status and version tracking
**Key techniques:** REDCap API (`requests`), `pandas`, `Streamlit`, `Plotly Express`, `@st.cache_data`, multi-page app architecture.
 
See the [dashboard README](imaging_dashboard/README.md) for full setup instructions and data architecture details.
 
---
 
### `imaging_report/imaging_report.Rmd`
Parameterized R Markdown report that generates an HTML dashboard of Imaging Core scan metrics across MRI, Amyloid PET, Tau PET, and FDG PET modalities. Includes longitudinal scan timelines, diagnosis distributions, and period-specific counts (budget year and RPPR reporting window).
 
**Key techniques:** REDCap API, `tidyverse`, `ggplot2`, `gt` tables, `pivot_longer`, automated narrative generation.
 
---
 
### `imaging_report/run_imaging_report.R`
Wrapper script that renders `imaging_report.Rmd` programmatically using `rmarkdown::render()`, with error handling and logging.
 
---
 
### `imaging_report/setup_cron.R`
Uses the `cronR` package to schedule `run_imaging_report.R` to run automatically every Monday at 9:00 AM, producing a fresh weekly report with no manual intervention.
 
---
 
### `tau_pet_metrics/Tau_PET_Metrics.Rmd`
R Markdown report analyzing Tau PET read concordance across researcher and clinician raters for Imaging Core and PPA study scans. Identifies discrepant reads, flags individual raters, and produces summary tables and plots.
 
**Key techniques:** REDCap API, `pivot_longer/wider`, rowwise consensus logic, `knitr::kable`, `ggplot2`, `scales`.
 
---
 
## Credential Setup
 
### R scripts
 
Tokens are **never** stored in this repository. 
 
#### Option A — Local credentials file (recommended for local use)
 
Create a file called `redcap_api_info.R` in your working directory (listed in `.gitignore` and will never be committed):
 
```r
# redcap_api_info.R  ← DO NOT COMMIT THIS FILE
url            <- "https://redcap.yourInstitution.edu/api/"
imaging_token  <- "YOUR_IMAGING_REDCAP_TOKEN"
dr_token       <- "YOUR_DATA_REQUEST_REDCAP_TOKEN"
uds3_token     <- "YOUR_UDS3_REDCAP_TOKEN"
uds4_token     <- "YOUR_UDS4_REDCAP_TOKEN"
```
 
Then source it at the top of each script:
```r
source("redcap_api_info.R")
```
 
#### Option B — Environment variables (recommended for servers/cron)
 
Add the following to your `~/.Renviron` file:
 
```
REDCAP_URL=https://redcap.yourInstitution.edu/api/
REDCAP_IMAGING_TOKEN=your_token_here
REDCAP_DR_TOKEN=your_token_here
```
 
Then read them in R:
```r
url           <- Sys.getenv("REDCAP_URL")
imaging_token <- Sys.getenv("REDCAP_IMAGING_TOKEN")
```
 
### Python / Streamlit dashboard
 
The dashboard reads API tokens from a file named `redcap_api_info.py` located in your OneDrive root (listed in `.gitignore` and will never be committed):
 
```
~/OneDrive - Northwestern University/redcap_api_info.py
```
 
```python
# redcap_api_info.py  ← DO NOT COMMIT THIS FILE
url            = "https://redcap.yourInstitution.edu/api/"
uds4_token     = "YOUR_UDS4_REDCAP_TOKEN"
imaging_token  = "YOUR_IMAGING_REDCAP_TOKEN"
```
 
---
 
## Required Packages
 
### R
 
```r
install.packages(c(
  "tidyverse",   # Data wrangling and ggplot2
  "redcapAPI",   # REDCap API interface
  "httr",        # HTTP requests
  "readxl",      # Read Excel files
  "writexl",     # Write Excel files
  "openxlsx",    # Multi-sheet Excel output
  "janitor",     # Data cleaning utilities
  "gt",          # Publication-quality tables
  "knitr",       # R Markdown rendering
  "scales",      # Axis formatting
  "ggrepel",     # Non-overlapping plot labels
  "rmarkdown",   # Report rendering
  "cronR",       # Cron job scheduling (macOS/Linux)
  "here"         # Relative file paths
))
```
 
### Python (imaging dashboard)
 
```bash
pip install streamlit pandas numpy plotly requests
```
 
To run the dashboard:
 
```bash
cd imaging_dashboard
streamlit run Home.py
```
 
---
 
## Output Files
 
All output files (CSVs, Excel files, PNGs, HTML reports) are excluded from version control via `.gitignore`. Scripts write to a local `Output/` directory relative to the project root.
