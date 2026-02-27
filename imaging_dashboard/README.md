# Imaging Dashboard

> **Status: In Development**

An interactive R Shiny dashboard that extends the [Imaging Report](../imaging_report/imaging_report.Rmd) with real-time participant eligibility tracking and expanded scan metrics for the Mesulam Center Imaging Core.

---

## Planned Features

### Eligibility Tracker
- Filter participants by study affiliation, diagnosis, age, and scan history
- Flag participants who meet eligibility criteria for upcoming scans
- Track eligibility status changes over time

### Scan Metrics
- Live scan counts by modality (MRI, Amyloid PET, Tau PET, FDG PET)
- Progress toward RPPR and budget year targets
- Recruitment funnel — screened → eligible → scheduled → scanned
- Dropout and loss-to-follow-up tracking

### Reporting
- Exportable summary tables (Excel/CSV)
- Date range filtering for any reporting period
- Downloadable plots for grant reports and presentations

---

## Planned Tech Stack

| Component      | Tool                  |
|----------------|-----------------------|
| Framework      | R Shiny               |
| UI             | `shinydashboard` or `bslib` |
| Tables         | `gt` / `DT`           |
| Plots          | `ggplot2`             |
| Data source    | REDCap API (`httr`)   |
| Data wrangling | `tidyverse`           |

---

## Planned File Structure

```
imaging_dashboard/
├── README.md
├── app.R                  # Main Shiny app entry point
├── R/
│   ├── data_pull.R        # REDCap API calls
│   ├── eligibility.R      # Eligibility logic
│   ├── scan_metrics.R     # Scan count calculations
│   └── plots.R            # Reusable ggplot2 functions
├── www/
│   └── custom.css         # Dashboard styling
└── Output/                # gitignored exports
```

---

## Relationship to Imaging Report

This dashboard is designed as a companion to `imaging_report.Rmd`. The static report will continue to serve as the formal deliverable for grant reporting, while this dashboard provides a live, interactive view of the same underlying data for day-to-day monitoring.

---

## Setup (Coming Soon)

Credential and REDCap configuration will follow the same pattern as the rest of this repo. See the root [README](../README.md) for the credential setup guide.

---

## Notes

- [ ] Finalize eligibility criteria logic per study
- [ ] Determine hosting — local only vs. Shinyapps.io vs. institutional server
- [ ] Confirm REDCap fields needed for eligibility module
