# -*- coding: latin-1 -*-
# Description: This script locates resampled DTM and DSM files, calculates the Local Relief Model (LRM) 
# using RVT tools, and saves the result in the appropriate output directory.
# Author: Marcus Engelke (2025)

import rvt.default
import os
from pathlib import Path
import traceback  # Zum besseren Fehler-Tracking

def calculate_lrm(data_folder):
    """
    Finds the resampled DTM and DSM files in the specified folder, 
    performs the Local Relief Model (LRM) calculation, and saves the result.
    
    - data_folder: Folder containing the relevant data.
    """
    try:
        # Step 1: Find the resampled DTM and DSM files
        dtm_file = None
        dsm_file = None

        # Search for the resampled DTM and DSM files
        for file in Path(data_folder).glob("*_temp/*_DTM.tif"):
            dtm_file = file
        for file in Path(data_folder).glob("*_temp/*_DSM.tif"):
            dsm_file = file

        # Check if both files are found
        if not dtm_file or not dsm_file:
            raise ValueError("Error: Resampled DTM or DSM files not found.")
        
        # Step 2: Load the DEM (DTM)
        dict_dem = rvt.default.get_raster_arr(str(dtm_file))
        
        if dict_dem is None:
            raise ValueError(f"Error loading DTM file {dtm_file}, check the file path or format.")

        dem_arr = dict_dem["array"]  # numpy array of DEM
        dem_resolution = dict_dem["resolution"]
        dem_res_x = dem_resolution[0]  # resolution in X direction
        dem_res_y = dem_resolution[1]  # resolution in Y direction
        dem_no_data = dict_dem["no_data"]

        # Set default values for RVT
        default = rvt.default.DefaultValues()
        default.slrm_rad_cell = 10  # Radius for local trend in pixels

        # Step 3: Calculate the Local Relief Model (LRM) using the provided DEM data
        slrm_arr = default.get_slrm(dem_arr=dem_arr)

        # Step 4: Save the result to the specified custom output file path
        default.save_slrm(dem_path=str(dtm_file), custom_dir=None, save_float=True, save_8bit=False)
        
        for file in Path(data_folder).glob("*_temp/*_SLRM_R10.tif"):
            dtm_file = file
        
            # Erstellen des neuen Dateinamens
            new_name = dtm_file.stem.replace("_DTM_SLRM_R10", "_LRM")  # Ersetze den alten Teil mit dem neuen
            new_file = dtm_file.with_name(new_name + dtm_file.suffix)  # Kombiniere den neuen Namen mit der Endung
        
            # Umbenennen der Datei
            dtm_file.rename(new_file)
        
        print(f"LRM calculation completed")
        return str(dtm_file)  # Optionally, return the path of the processed DTM file if needed

    except Exception as e:
        print(f"Error calculating LRM: {e}")
        traceback.print_exc()  # Prints the traceback for more detail
        return None
