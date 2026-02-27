## setup_cron.R
##
## Schedules run_imaging_report.R as a weekly cron job using the cronR package.
## Run this script once to register the job; it does not need to be run again.
##
## Requirements:
##   - macOS or Linux
##   - cronR package: install.packages("cronR")
##   - here package:  install.packages("here")
##
## SETUP: Update the path below to point to your local run_imaging_report.R

library(cronR)
library(here)

# Path to the render script — update if your directory layout differs
runner_script <- here("imaging_report", "run_imaging_report.R")

# Build the cron command
cmd <- cron_rscript(runner_script)

# Schedule: every Monday at 09:00 AM
# Adjust frequency ("weekly", "daily", etc.) and time as needed
cron_add(
  command      = cmd,
  frequency    = "weekly",
  at           = "09:00",
  days_of_week = 1,          # 1 = Monday (0 = Sunday)
  id           = "weekly_imaging_report"
)

# To view all registered cron jobs:
# cron_ls()

# To remove this job:
# cron_rm("weekly_imaging_report")
