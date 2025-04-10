# -*- coding: latin-1 -*-
# Description: This script resamples DTM and DSM raster files to a specified resolution and calculates
# the Canopy Height Model (CHM) by subtracting the DTM from the DSM. The results are saved in a temporary folder.
# Author: Marcus Engelke (2025)
import rasterio
from rasterio.enums import Resampling
import os
from pathlib import Path

# Function to resample a raster to a new resolution
def resample_raster(input_raster, output_raster, new_resolution=0.5):
    with rasterio.open(input_raster) as src:
        # Get current resolution
        pixel_size_x, pixel_size_y = src.res

        # Calculate the new width and height
        width = int(src.width * (pixel_size_x / new_resolution))
        height = int(src.height * (pixel_size_y / new_resolution))

        # Update the transform
        new_transform = src.transform * src.transform.scale(
            (src.width / width), (src.height / height)
        )

        # Resample using bilinear interpolation
        resampled_data = src.read(
            1,
            out_shape=(height, width),
            resampling=Resampling.bilinear
        )

        # Save the resampled raster
        with rasterio.open(
            output_raster, 'w', driver='GTiff',
            height=resampled_data.shape[0], width=resampled_data.shape[1],
            count=1, dtype=resampled_data.dtype,
            crs=src.crs, transform=new_transform
        ) as dst:
            dst.write(resampled_data, 1)

        print(f"Resampling completed: {output_raster}")

# Function to calculate the Canopy Height Model (CHM)
def calculate_chm(dtm_file, dsm_file, output_chm_file):
    with rasterio.open(dtm_file) as dtm_src:
        dtm_data = dtm_src.read(1)
        dtm_transform = dtm_src.transform
        dtm_crs = dtm_src.crs

    with rasterio.open(dsm_file) as dsm_src:
        dsm_data = dsm_src.read(1)

    # Calculate CHM
    chm_data = dsm_data - dtm_data

    # Save CHM
    with rasterio.open(output_chm_file, 'w', driver='GTiff',
                       height=chm_data.shape[0], width=chm_data.shape[1],
                       count=1, dtype=chm_data.dtype,
                       crs=dtm_crs, transform=dtm_transform) as chm_dst:
        chm_dst.write(chm_data, 1)

    print(f"CHM calculation completed: {output_chm_file}")

def process_raster_folder(input_folder, new_resolution=0.5):
    try:
        input_folder = Path(input_folder)
        if not input_folder.is_dir():
            raise ValueError(f"Input path is not a directory: {input_folder}")

        # Find and assign DTM and DSM files
        dtm_file = None
        dsm_file = None

        for file in input_folder.glob("*.tif"):
            if file.name.startswith("dgm"):
                dtm_file = file
            elif file.name.startswith("dom"):
                dsm_file = file

        if not dtm_file or not dsm_file:
            raise ValueError("Could not find both DTM (dgm*.tif) and DSM (dom*.tif) files in the folder.")

        # Extract base name from DTM filename
        base_name = "_".join(dtm_file.stem.split("_")[1:])
        # Create a temporary folder inside the input folder
        temp_folder = input_folder / f"{base_name}_temp"
        os.makedirs(temp_folder, exist_ok=True)

        print(f"Output folder created: {temp_folder}")

        # Generate output file paths
        output_dtm = temp_folder / f"{base_name}_DTM.tif"
        output_dsm = temp_folder / f"{base_name}_DSM.tif"
        output_chm = temp_folder / f"{base_name}_CHM.tif"

        # Resample DTM and DSM
        resample_raster(dtm_file, output_dtm, new_resolution=new_resolution)
        resample_raster(dsm_file, output_dsm, new_resolution=new_resolution)

        # Calculate CHM
        calculate_chm(output_dtm, output_dsm, output_chm)

        print(f"Processing completed. Results saved in: {temp_folder}")
        return temp_folder  # Return the temp folder for later use

    except Exception as e:
        print(f"Error during resampling or CHM calculation: {e}")
        traceback.print_exc()  # Provides detailed traceback for debugging
        return None  # Return None if an error occurs
