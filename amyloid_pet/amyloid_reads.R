## Amyloid Discrepant Visual SUVr Reads
## 
## Pulls Amyloid PET data from two quantification methods (IBC and GAAIN),
## identifies discrepancies between visual clinical reads and quantitative
## SUVr/Centiloid thresholds, and exports flagged cases and visualizations.
##
## SETUP: See README.md for credential and path configuration before running.

# Remove all objects from environment
rm(list = ls())

# ── Libraries ────────────────────────────────────────────────────────────────
library(tidyverse)
library(readr)
library(writexl)
library(ggrepel)
library(here)

# ── Credentials ───────────────────────────────────────────────────────────────
# Option A: source a local (gitignored) credentials file
# source("redcap_api_info.R")

# Option B: read from environment variables (recommended for servers)
# url           <- Sys.getenv("REDCAP_URL")
# imaging_token <- Sys.getenv("REDCAP_IMAGING_TOKEN")

# ── File Paths ────────────────────────────────────────────────────────────────
# Update these paths to point to your local data and output directories.
# Using here::here() anchors paths to the project root.

data_dir   <- here("amyloid_pet", "data")
output_dir <- here("amyloid_pet", "outputs")

if (!dir.exists(output_dir)) dir.create(output_dir, recursive = TRUE)

# ── Import Data ───────────────────────────────────────────────────────────────
# Replace filenames below with your actual exported REDCap/GAAIN filenames.
PET_metrics      <- read.csv(file.path(data_dir, "IC_PET_metrics.csv"))
stub             <- read.csv(file.path(data_dir, "stub.csv"))
SCAN_aPET_GAAIN  <- read.csv(file.path(data_dir, "v_ucberkeley_amyloid_mrifree_gaain.csv"))

nrow(PET_metrics)
nrow(stub)
nrow(SCAN_aPET_GAAIN)

# ── Clean Data ────────────────────────────────────────────────────────────────

# Stub — keep only global ID and participant ID
stub_clean <- stub %>%
  select("Ripple.Global.ID", "PTID") %>%
  rename(global_id = Ripple.Global.ID)

# IBC PET metrics — select, rename, and derive final clinical read
PET_metrics_clean <- PET_metrics %>%
  select(
    "Ripple.Global.ID", "Amyloid.PET.scan.date.of.occurence",
    "Amyloid.PET.Study.Affiliation..Please.check.all.that.apply.",
    "Amyloid.PET.Clinician.read..Rater..1.",
    "Amyloid.PET.Clinician.read.source..Rater..1.",
    "Amyloid.PET.Clinician.read..Rater..2.",
    "Amyloid.PET.Clinician.read.source..Rater..2.",
    "Amyloid.PET.read.CONSENSUS..All...Researcher...Clinician.",
    "Amyloid.PET.Mean.SUVr...Susan.Landau.method"
  ) %>%
  rename(
    global_id        = Ripple.Global.ID,
    scan_date        = Amyloid.PET.scan.date.of.occurence,
    study_affiliation= Amyloid.PET.Study.Affiliation..Please.check.all.that.apply.,
    clinician_read_1 = Amyloid.PET.Clinician.read..Rater..1.,
    clinician_rater_1= Amyloid.PET.Clinician.read.source..Rater..1.,
    clinician_read_2 = Amyloid.PET.Clinician.read..Rater..2.,
    clinician_rater_2= Amyloid.PET.Clinician.read.source..Rater..2.,
    consensus_read   = Amyloid.PET.read.CONSENSUS..All...Researcher...Clinician.,
    mean_SUVr        = Amyloid.PET.Mean.SUVr...Susan.Landau.method
  ) %>%
  mutate(
    method = rep("IBC", nrow(PET_metrics))   # flag the quantification method
  ) %>%
  # Filter to ADRC Imaging Core scans from 2021 onward (SCAN program start)
  filter(scan_date > "2020-12-31" & study_affiliation == "ADRC Imaging Core") %>%
  mutate(
    # Derive final read: use consensus when raters disagree
    final_read = case_when(
      clinician_read_2 == ""                        ~ clinician_read_1,
      clinician_read_1 != clinician_read_2          ~ consensus_read,
      TRUE                                           ~ clinician_read_1
    )
  ) %>%
  select(-study_affiliation)

# GAAIN (UC Berkeley) method — rename and derive binary read
SCAN_aPET_GAAIN_clean <- SCAN_aPET_GAAIN %>%
  select(PTID, AMYLOID_STATUS, SCANDATE, GAAIN_SUMMARY_SUVR, CENTILOIDS) %>%
  rename(mean_SUVr = GAAIN_SUMMARY_SUVR, scan_date = SCANDATE) %>%
  mutate(
    method     = rep("GAAIN", nrow(SCAN_aPET_GAAIN)),
    .after = PTID
  ) %>%
  mutate(
    final_read = ifelse(AMYLOID_STATUS == 0, "Negative", "Positive"),
    .after = scan_date
  ) %>%
  select(-AMYLOID_STATUS)

# ── QC Checks ─────────────────────────────────────────────────────────────────

# Cases with only one clinical rater
one_clinical_read <- PET_metrics_clean[which(PET_metrics_clean$clinician_read_2 == ""), ]
cat("Cases with one clinical read:", nrow(one_clinical_read), "\n")

# Visual/quantitative discrepancies — Negative read but SUVr >= 1.08 (IBC cutoff)
discrepant_reads_neg <- PET_metrics_clean[
  which(PET_metrics_clean$final_read == "Negative" & PET_metrics_clean$mean_SUVr >= 1.08), ]

# Visual/quantitative discrepancies — Positive read but SUVr < 1.08
discrepant_reads_pos <- PET_metrics_clean[
  which(PET_metrics_clean$final_read == "Positive" & PET_metrics_clean$mean_SUVr <= 1.08), ]

discrepant_reads_final <- rbind(discrepant_reads_neg, discrepant_reads_pos)
cat("Total visual/SUVr discrepancies:", nrow(discrepant_reads_final), "\n")

# ── Merge Datasets ─────────────────────────────────────────────────────────────

# Prepare IBC dataset for merge
PET_metrics_final <- PET_metrics_clean %>%
  select(global_id, scan_date, method, final_read, mean_SUVr)

# Join IBC metrics with stub (adds PTID)
IC_merged <- inner_join(PET_metrics_final, stub_clean, by = "global_id") %>%
  select(global_id, PTID, method, everything())

# Full outer merge with GAAIN
merged <- merge(
  IC_merged,
  SCAN_aPET_GAAIN_clean,
  by     = intersect(names(PET_metrics_final), names(SCAN_aPET_GAAIN_clean)),
  all    = TRUE,
  suffixes = c("_IC", "_GAAIN")
) %>%
  fill(PTID_GAAIN, .direction = "down") %>%
  select(-c(PTID_IC, global_id)) %>%
  rename(PTID = PTID_GAAIN)

# ── Plots ─────────────────────────────────────────────────────────────────────

# Plot 1: IBC SUVr values colored by visual read; discrepancies flagged in red
plot_1 <- ggplot(data = PET_metrics_final, aes(x = global_id, y = mean_SUVr)) +
  geom_point(size = 2, aes(shape = final_read, color = final_read)) +
  geom_hline(yintercept = 1.08, color = "black", linetype = "dashed", linewidth = .5) +
  # Flag negative reads above SUVr threshold
  geom_point(
    data = PET_metrics_final[PET_metrics_final$final_read == "Negative" &
                               PET_metrics_final$mean_SUVr >= 1.08, ],
    aes(shape = final_read, color = final_read),
    pch = 0, fill = NA, size = 4, color = "red", stroke = 1
  ) +
  # Flag positive reads below SUVr threshold
  geom_point(
    data = PET_metrics_final[PET_metrics_final$final_read == "Positive" &
                               PET_metrics_final$mean_SUVr <= 1.08, ],
    aes(shape = final_read, color = final_read),
    pch = 0, fill = NA, size = 4, color = "red", stroke = 1
  ) +
  geom_text(
    data = PET_metrics_final[PET_metrics_final$final_read == "Negative" &
                               PET_metrics_final$mean_SUVr >= 1.08, ],
    aes(label = mean_SUVr, x = global_id, y = mean_SUVr),
    position = position_dodge(0.9), vjust = -.95, size = 3.5
  ) +
  geom_text(
    data = PET_metrics_final[PET_metrics_final$final_read == "Positive" &
                               PET_metrics_final$mean_SUVr <= 1.08, ],
    aes(label = mean_SUVr, x = global_id, y = mean_SUVr),
    position = position_dodge(0.9), vjust = -.95, size = 3.5
  ) +
  labs(
    title  = "IBC Amyloid Mean SUVr by Clinical Visual Read",
    x      = "",
    y      = "Mean SUVr",
    color  = "Clinical Read",
    shape  = "Clinical Read"
  ) +
  scale_y_continuous(breaks = seq(0, 2.2, by = .2)) +
  scale_color_manual(values = c("darkred", "darkblue"),
                     breaks = c("Negative", "Positive")) +
  scale_shape_manual(values = c(19, 17),
                     breaks = c("Negative", "Positive")) +
  theme(
    legend.box.background   = element_rect(),
    legend.background       = element_blank(),
    legend.key              = element_blank(),
    legend.position         = "inside",
    legend.position.inside  = c(.9, .92),
    panel.background        = element_blank(),
    panel.grid.major        = element_blank(),
    panel.border            = element_blank(),
    axis.ticks.x            = element_blank(),
    axis.line.x             = element_blank(),
    axis.text.x             = element_blank(),
    axis.line.y             = element_line(linewidth = .5, linetype = "solid"),
    plot.title              = element_text(size = 14, hjust = .5, face = "bold")
  )

ggsave("IC_amyloid_metrics.png",
       plot = plot_1, width = 12, height = 6, units = "in", dpi = 300,
       path = output_dir)

# Plot 2: IBC vs GAAIN SUVr values by visual read (faceted)
merged_clean <- merged %>%
  filter(!is.na(mean_SUVr))

plot_2 <- ggplot(data = merged_clean,
                 aes(x = scan_date, y = mean_SUVr, group = method)) +
  geom_point(size = 2, aes(color = final_read)) +
  geom_hline(aes(yintercept = 1.08, linetype = "IBC cutoff"),
             linewidth = .5, color = "black") +
  geom_hline(aes(yintercept = 1.12, linetype = "SCAN cutoff"),
             linewidth = .5, color = "red") +
  # Flag GAAIN discrepancies (blue circles)
  geom_point(
    data = merged_clean[merged_clean$method == "GAAIN" &
                          merged_clean$final_read == "Negative" &
                          merged_clean$mean_SUVr >= 1.12, ],
    pch = 1, fill = NA, size = 4, color = "blue", stroke = 1
  ) +
  geom_text(
    data = merged_clean[merged_clean$method == "GAAIN" &
                          merged_clean$final_read == "Negative" &
                          merged_clean$mean_SUVr >= 1.12, ],
    aes(label = mean_SUVr, x = scan_date, y = mean_SUVr),
    position = position_dodge(0.9), vjust = -.95, size = 3.5
  ) +
  geom_point(
    data = merged_clean[merged_clean$method == "GAAIN" &
                          merged_clean$final_read == "Positive" &
                          merged_clean$mean_SUVr <= 1.12, ],
    pch = 1, fill = NA, size = 4, color = "blue", stroke = 1
  ) +
  geom_text(
    data = merged_clean[merged_clean$method == "GAAIN" &
                          merged_clean$final_read == "Positive" &
                          merged_clean$mean_SUVr <= 1.12, ],
    aes(label = mean_SUVr, x = scan_date, y = mean_SUVr),
    position = position_dodge(0.9), vjust = -.95, size = 3.5
  ) +
  # Flag IBC discrepancies (green circles)
  geom_point(
    data = merged_clean[merged_clean$method == "IBC" &
                          merged_clean$final_read == "Negative" &
                          merged_clean$mean_SUVr >= 1.08, ],
    pch = 1, fill = NA, size = 4, color = "green", stroke = 1
  ) +
  geom_text_repel(
    data = merged_clean[merged_clean$method == "IBC" &
                          merged_clean$final_read == "Negative" &
                          merged_clean$mean_SUVr >= 1.08, ],
    aes(label = mean_SUVr, x = scan_date, y = mean_SUVr),
    nudge_y = 0.05, size = 3.5
  ) +
  geom_point(
    data = merged_clean[merged_clean$method == "IBC" &
                          merged_clean$final_read == "Positive" &
                          merged_clean$mean_SUVr <= 1.08, ],
    pch = 1, fill = NA, size = 4, color = "green", stroke = 1
  ) +
  geom_text_repel(
    data = merged_clean[merged_clean$method == "IBC" &
                          merged_clean$final_read == "Positive" &
                          merged_clean$mean_SUVr <= 1.08, ],
    aes(label = mean_SUVr, x = scan_date, y = mean_SUVr),
    nudge_y = 0.05, size = 3.5
  ) +
  facet_wrap(method ~ .) +
  labs(
    title = "Amyloid PET Clinical Visual Reads Between IBC & SCAN Methods",
    x     = "",
    y     = "Mean SUVr",
    color = "Clinical Read:"
  ) +
  scale_y_continuous(breaks = seq(0, 2.2, by = .2)) +
  scale_color_manual(values = c("darkred", "darkblue"),
                     breaks = c("Negative", "Positive")) +
  scale_linetype_manual(
    name   = "SUVr Cutoff:",
    values = c(2, 2),
    guide  = guide_legend(override.aes = list(color = c("black", "red")))
  ) +
  theme(
    legend.box.background = element_rect(),
    legend.background     = element_blank(),
    legend.key            = element_blank(),
    legend.position       = "top",
    panel.background      = element_blank(),
    panel.border          = element_rect(fill = NA),
    axis.line.x           = element_blank(),
    axis.text.x           = element_blank(),
    axis.ticks.x          = element_blank(),
    axis.line.y           = element_line(linewidth = .5, linetype = "solid"),
    plot.title            = element_text(size = 14, hjust = .5, face = "bold")
  )

ggsave("IC_SCAN_amyloid_metrics.png",
       plot = plot_2, width = 12, height = 6, units = "in", dpi = 300,
       path = output_dir)

# Plot 3: Histogram of SUVr distributions for IBC and GAAIN
plot_3 <- ggplot(data = merged_clean, aes(x = mean_SUVr, group = method)) +
  geom_histogram(bins = 75, color = "black", position = "dodge",
                 alpha = .75, aes(fill = method)) +
  geom_vline(
    data = merged_clean[merged_clean$method == "IBC", ],
    aes(xintercept = 1.08, linetype = "IBC cutoff"),
    linewidth = .5, color = "black"
  ) +
  geom_vline(
    data = merged_clean[merged_clean$method == "GAAIN", ],
    aes(xintercept = 1.12, linetype = "SCAN cutoff"),
    linewidth = .5, color = "red"
  ) +
  facet_wrap(~factor(method, c("IBC", "GAAIN"))) +
  labs(
    title    = "Amyloid PET SUVr Values Between IBC & SCAN GAAIN Method",
    x        = "Mean SUVr Value",
    y        = "Count",
    fill     = "Method:",
    linetype = ""
  ) +
  scale_fill_manual(values = c("darkred", "darkblue"),
                    breaks = c("IBC", "GAAIN")) +
  scale_x_continuous(breaks = seq(0, 2.2, by = .2)) +
  theme(
    legend.box.background = element_rect(),
    legend.background     = element_blank(),
    legend.key            = element_blank(),
    legend.position       = "top",
    panel.background      = element_blank(),
    panel.border          = element_rect(fill = NA),
    axis.line.x           = element_line(linewidth = .5, linetype = "solid"),
    axis.line.y           = element_line(linewidth = .5, linetype = "solid"),
    plot.title            = element_text(size = 14, hjust = .5, face = "bold")
  )

ggsave("IC_SCAN_amyloid_hist.png",
       plot = plot_3, width = 12, height = 6, units = "in", dpi = 300,
       path = output_dir)

# Plot 4: GAAIN Centiloid values by visual read
merged_gaain <- merged[merged$method == "GAAIN", ]

plot_4 <- ggplot(data = merged_gaain, aes(x = scan_date, y = CENTILOIDS)) +
  geom_point(size = 2, aes(shape = final_read, color = final_read)) +
  geom_hline(yintercept = 20, color = "black", linetype = "dashed", linewidth = .5) +
  geom_point(
    data = merged_gaain[merged_gaain$final_read == "Negative" &
                          merged_gaain$CENTILOIDS > 10, ],
    pch = 0, fill = NA, size = 3.5, color = "red", stroke = 1
  ) +
  geom_text_repel(
    data = merged_gaain[merged_gaain$final_read == "Negative" &
                          merged_gaain$CENTILOIDS > 10, ],
    aes(label = CENTILOIDS, x = scan_date, y = CENTILOIDS),
    nudge_y = 0.05, size = 3.5
  ) +
  geom_point(
    data = merged_gaain[merged_gaain$final_read == "Positive" &
                          merged_gaain$CENTILOIDS < 20, ],
    pch = 0, fill = NA, size = 3.5, color = "red", stroke = 1
  ) +
  geom_text_repel(
    data = merged_gaain[merged_gaain$final_read == "Positive" &
                          merged_gaain$CENTILOIDS < 20, ],
    aes(label = CENTILOIDS, x = scan_date, y = CENTILOIDS),
    nudge_y = 0.05, size = 3.5
  ) +
  labs(
    title = "GAAIN Amyloid Centiloids by Clinical Visual Read",
    x     = "",
    y     = "Centiloid Values",
    color = "Clinical Read",
    shape = "Clinical Read"
  ) +
  scale_color_manual(values = c("darkred", "darkblue"),
                     breaks = c("Negative", "Positive")) +
  scale_shape_manual(values = c(19, 17),
                     breaks = c("Negative", "Positive")) +
  theme(
    legend.box.background  = element_rect(),
    legend.background      = element_blank(),
    legend.key             = element_blank(),
    legend.position        = "inside",
    legend.position.inside = c(.95, .92),
    panel.background       = element_blank(),
    panel.grid.major       = element_blank(),
    panel.border           = element_blank(),
    axis.ticks.x           = element_blank(),
    axis.line.x            = element_blank(),
    axis.text.x            = element_blank(),
    axis.line.y            = element_line(linewidth = .5, linetype = "solid"),
    plot.title             = element_text(size = 14, hjust = .5, face = "bold")
  )

ggsave("gaain_centiloids.png",
       plot = plot_4, width = 12, height = 6, units = "in", dpi = 300,
       path = output_dir)

# ── Export Tables ─────────────────────────────────────────────────────────────
writexl::write_xlsx(one_clinical_read,
                    file.path(output_dir, "one_clinical_read_all.xlsx"))

writexl::write_xlsx(discrepant_reads_final,
                    file.path(output_dir, "all_visual_quantitative_discrepancies.xlsx"))
