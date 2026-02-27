## run_imaging_report.R
##
## Renders imaging_report.Rmd to an HTML report programmatically.
## Intended to be called directly or via the cron job set up in setup_cron.R.
##
## SETUP: Set the paths below to match your local environment before running.

library(rmarkdown)
library(here)

# ── Pandoc Path ───────────────────────────────────────────────────────────────
# Required when running outside of RStudio (e.g., from cron).
# Update this to the pandoc binary on your system.
# Find yours by running: rmarkdown::find_pandoc()

Sys.setenv(RSTUDIO_PANDOC = "/Applications/RStudio.app/Contents/Resources/app/quarto/bin/tools/x86_64")

# ── Paths ─────────────────────────────────────────────────────────────────────
rmd_file   <- here("imaging_report", "imaging_report.Rmd")
output_dir <- here("imaging_report", "Output")
log_file   <- file.path(output_dir, "imaging_report.log")

# Create output directory if it doesn't exist
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# ── Render with Logging ───────────────────────────────────────────────────────
log_con <- NULL

tryCatch({
  log_con <- file(log_file, open = "a")
  sink(log_con, append = TRUE)
  sink(log_con, append = TRUE, type = "message")

  cat("\n==== Rendering started at", as.character(Sys.time()), "====\n")

  render(
    input      = rmd_file,
    output_dir = output_dir,
    quiet      = TRUE
  )

  cat("Rendering completed successfully at", as.character(Sys.time()), "\n")
  cat("==== Rendering finished at", as.character(Sys.time()), "====\n")

}, error = function(e) {
  cat("ERROR during rendering at", as.character(Sys.time()), ":\n")
  cat(conditionMessage(e), "\n")
  cat("==== Rendering finished at", as.character(Sys.time()), "====\n")

}, finally = {
  if (!is.null(log_con)) {
    sink(type = "message")
    sink()
    close(log_con)
  }
})
