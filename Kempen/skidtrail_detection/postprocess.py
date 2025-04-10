# -*- coding: latin-1 -*-
# This script reads a raster file, applies a binary thresholding operation (values > 0.3 become 1, others become 0),
# and saves the result as a new raster file with '_results_filt' appended to the original name.
# Author: Marcus Engelke (2025)

import rasterio
import numpy as np
import os

# Paths for input and output files
input_raster = input("Bitte geben Sie den vollständigen Pfad zum Pred_Tif ein: ").strip().strip('"')
base, ext = os.path.splitext(input_raster)
output_raster = base + "_results_filt" + ext

# Load the raster
with rasterio.open(input_raster) as src:
    raster_data = src.read(1)  # Read the first raster band
    meta = src.meta  # Get the file metadata
    
# Apply the condition: values > 0.3 become 1, others become 0
binary_data = np.where(raster_data > 0.3, 1, 0).astype(np.uint8)

# Update metadata (e.g., change data type if necessary)
meta.update(dtype=rasterio.uint8, nodata=None)  # Set nodata to None, no missing values

# Save the result
with rasterio.open(output_raster, 'w', **meta) as dst:
    dst.write(binary_data, 1)

print("The binary raster has been successfully created and saved.")

