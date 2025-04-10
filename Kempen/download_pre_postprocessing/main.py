# -*- coding: latin-1 -*-
# Description: This script handles the full workflow for elevation data: 
# downloading, resampling DTM/DSM, calculating the Local Relief Model (LRM), 
# and generating the Vegetation Density Index (VDI) from LAS files.
# Author: Marcus Engelke (2025)

import os
import sys
from pathlib import Path
import traceback  # Zum besseren Fehler-Tracking
from download import download_and_extract_files  # Import the function from download.py
from chm import process_raster_folder  # Importing from the Resample-CHM script
from lrm import calculate_lrm  # Importing from the LRM script (for RVT calculation)
from vdi import chunkwise_process  # Importing from the VDI script (VDI calculation)

def main(data_folder, area_code, period = "2020-2025"):
    """
    Main process for downloading and extracting data, resampling DTM/DSM, LRM calculation, and VDI calculation.

    - data_folder: Folder containing all relevant data and subfolders.
    - area_code: Area code to use in the download URLs.
    - period: The time period for data download (default is "2020-2025").
    """
    print(f"Processing folder: {data_folder}")
    print(f"Area code: {area_code}")
    print(f"Period: {period}")
    
    
    # Step 0: Download and extract the required files for the given area and period
    data_folder = download_and_extract_files(area_code, period=period, download_dir=data_folder)
    print(data_folder)
    # Step 1: Process all DTM/DSM data in the given folder (resampling)
    temp_folder = process_raster_folder(data_folder, new_resolution=0.5)
    if not temp_folder:
        print("Error during resampling. Exiting.")
        return

    # Step 2: Calculate the Local Relief Model (LRM)
    print(f"Calculating Local Relief Model (LRM) for the resampled DTM")
    lrm_output = calculate_lrm(data_folder)  # This now handles both file searching and LRM calculation
    
    if lrm_output:
        print(f"LRM calculation completed.")
    else:
        print("Error during LRM calculation.")
        return  # Or handle the error as appropriate
  
    try:
        # Step 3: Find the resampled DTM file in temp_folder
        dtm_file = None
        for dtm_file_candidate in temp_folder.glob("*_DTM.tif"):
            dtm_file = dtm_file_candidate
            break
        
        if not dtm_file:
            print("Error: Resampled DTM file not found in temp folder.")
            return

        # Step 4: Process LAS files
        las_files = list(Path(data_folder).glob("*.laz"))  # Search for LAS files in the data folder
        if not las_files:
            print("Error: No LAS files found in the specified folder.")
            return
        
        for las_file in las_files:
            output_vdi = temp_folder / f"{las_file.stem}_VDI.tif"
            output_vdi_name = output_vdi.name.replace('las_', '')
            output_vdi = output_vdi.with_name(output_vdi_name)
            
            try:
                print(f"Processing LAS file: {las_file}")
                chunkwise_process(str(las_file), str(dtm_file), str(output_vdi))  # No more parameters needed
                print(f"VDI calculation completed for {las_file}. Result saved to {output_vdi}")
            except Exception as e:
                print(f"Error processing {las_file}: {e}")
                traceback.print_exc()  # Prints the traceback for more detail

    except Exception as e:
        print(f"An error occurred during the processing: {e}")
        traceback.print_exc()  # Prints the traceback for more detail
    
if __name__ == "__main__":
    # Check if the folder path, area code, and period are provided as command line arguments
    if len(sys.argv) != 4:
        print("Usage: python main.py <input_folder> <area_code> <period>")
        sys.exit(1)

    input_folder = sys.argv[1]  # Get the input folder from the command-line argument
    area_code = sys.argv[2]  # Get the area code from the command-line argument
    period = sys.argv[3]  # Get the period from the command-line argument

    # Ensure the provided input folder exists
    if not Path(input_folder).is_dir():
        print(f"Error: {input_folder} is not a valid directory.")
        sys.exit(1)

    # Run the main function to orchestrate both processes
    main(input_folder, area_code, period)