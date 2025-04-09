#-----------------------------------------------------------------------------#
#### Configuration file ####
# Set your parameters and paths in this file
# R.Bienz / Adapted by Marcus Engelke
#-----------------------------------------------------------------------------#

# General setup
number_of_cores <- 32 # Number of cores used for certain calculations
remove_tempfiles <- TRUE # Should temporary files be removed?
remove_interim_results <- TRUE # Should results for each area be removed? If set to TRUE, temporary files are also removed.

# Path to the ground structure dataset
# See https://github.com/RaffiBienz/dtmanalyzer for calculation
#path_ground <- file.path("data/example_ground_structure.tif")

# Path to the forest delineation (or delineation of areas of interest)
#path_delineation <- file.path("data")
#name_delineation <- "example_forest_delineation"

# Benutzerdefinierte Eingabeaufforderungen für die Pfade
#path_ground <- readline(prompt = "Gib den Pfad zum Ground-Structure-Dataset an (z.B. data/example_ground_structure.tif): ")
#path_delineation <- readline(prompt = "Gib den Pfad zum Forest-Delineation Ordner an (z.B. data): ")

# Den Dateinamen der Delineation-Datei automatisch vom Pfad ableiten
name_delineation <- tools::file_path_sans_ext(basename(path_delineation))


# Python setup
#path_python <- file.path("C:/Users/Raffi/.conda/envs/road_finder2/python.exe") 
path_python = "python" # Path to python environment
path_script <- file.path("/src/predict_segmentation.py")

# Path to the pretrained model
path_model <- file.path("model/road_finder_model.h5")

# Global variables
window_size <- 150 # size for segmentation windows (model was trained for 150x150 m windows)
threshold_segmentation <- 0.5 # all pixels in the segmentation output above this value will be classified as strip roads
name_raster_output <- "forest_roads"

# Vectorizer setup
vectorize_segmentation <- TRUE
clip_lines <- TRUE # clip lines to forest delineation?
name_line_output <- "forest_roads"
thresh_min_area <- 20 # minimum area in m2
thresh_thinning <- 7 # minimum number of positive neighbors
win_size <- 2.5 # window size for line finder
