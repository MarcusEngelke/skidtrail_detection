####################################################################################################
#### Calculate ground structure from DTM ####
# Smooths the DTM and then subtracts the original DTM.
# Suitable for finding strip roads in forests and other ground structures.
# R.Bienz / Adapted by Marcus Engelke
####################################################################################################

# Aktivierung von renv für das Projekt
if (!requireNamespace("renv", quietly = TRUE)) install.packages("renv")
renv::activate()

# Pakete laden, die von renv verwaltet werden
library(terra)
library(imager)

# Arbeitsverzeichnis setzen
wd <- getwd()
setwd(wd)

# Verzeichnisse erstellen
dir.create("temp", showWarnings = FALSE)
dir.create("wd", showWarnings = FALSE)
dir.create("result", showWarnings = FALSE)

# Funktion zum Importieren und Resamplen von DTM-Dateien
import_and_resample_dtm <- function(file_path, target_res = 0.5) {
  if (!file.exists(file_path)) stop("Error: The specified file does not exist.")
  dtm <- rast(file_path)
  template <- rast(ext(dtm), res = target_res, crs = crs(dtm))
  dtm_resampled <- resample(dtm, template)
  return(dtm_resampled)
}

# Kommandozeilenargumente einlesen
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) stop("Error: No data path provided.")
data_path <- args[1]
cat("Data path received:", data_path, "\n")

# DTM laden
dtm <- import_and_resample_dtm(data_path, target_res = 0.5)

# DTM verarbeiten
process_dtm <- function(dtm, input_file_path) {
  dtm_img <- as.cimg(t(matrix(dtm[], ncol = ncol(dtm), byrow = TRUE)))
  dtm_img[is.na(dtm_img)] <- 0
  dtm_iso <- isoblur(dtm_img, 3)
  dtm_iso <- dtm_img - dtm_iso
  dtm_iso[dtm_iso < -1] <- -1
  dtm_iso[dtm_iso > 1] <- 1
  mag_ras <- rast(matrix(dtm_iso[], ncol = ncol(dtm), byrow = TRUE))
  crs(mag_ras) <- crs(dtm)
  ext(mag_ras) <- ext(dtm)
  origin(mag_ras) <- c(0, 0)
  output_file_path <- file.path(dirname(input_file_path), gsub("\\.tif$", "_diff.tif", basename(input_file_path)))
  writeRaster(mag_ras, filename = output_file_path, overwrite = TRUE)
  cat("Output saved to:", output_file_path, "\n")
  return(mag_ras)
}

# Struktur berechnen und speichern
process_dtm(dtm, data_path)

# Aufräumen
unlink("temp", recursive = TRUE)
