# -*- coding: latin-1 -*-
# Description: This script processes a LAS point cloud file in spatial chunks to compute a Vegetation Density Index (VDI),
# normalizes point heights using a DTM raster, and outputs a resampled VDI raster at a defined target resolution.
# Author: Marcus Engelke (2025)

import laspy
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling

def process_chunk(las_chunk, dtm_raster, resolution, x_min, x_max, y_min, y_max, t_lower=0.8, t_upper=12):
    """
    Process a chunk of LAS points to compute the VDI.
    
    - las_chunk: A subset of LAS points (filtered and normalized).
    - dtm_raster: DTM raster file for height normalization.
    - resolution: Desired grid resolution for VDI raster.
    - x_min, x_max, y_min, y_max: Boundaries for the chunk.
    - t_lower, t_upper: Vegetation height thresholds.
    
    Returns:
    - A VDI raster for the chunk.
    """
    try:
        # Extract z-values (height) from las_chunk
        z = las_chunk[:, 2]
        
        # Create the grid for VDI calculation
        x_bins = np.arange(x_min, x_max + resolution, resolution)
        y_bins = np.arange(y_min, y_max + resolution, resolution)
        vdi_grid = np.zeros((len(y_bins) - 1, len(x_bins) - 1), dtype=np.float32)

        # Loop through the grid and calculate VDI for each cell
        for i in range(len(x_bins) - 1):
            for j in range(len(y_bins) - 1):
                # Filter points within the current grid cell
                in_cell = (
                    (las_chunk[:, 0] >= x_bins[i]) & (las_chunk[:, 0] < x_bins[i + 1]) &
                    (las_chunk[:, 1] >= y_bins[j]) & (las_chunk[:, 1] < y_bins[j + 1])
                )
                cell_points = z[in_cell]

                # Calculate the VDI for the current cell
                if len(cell_points) > 0:
                    points_below_tupper = cell_points[cell_points <= t_upper]
                    points_below_tlower = points_below_tupper[points_below_tupper <= t_lower]

                    # Avoid division by zero
                    if len(points_below_tupper) > 0:
                        vdi_grid[j, i] = len(points_below_tlower) / len(points_below_tupper)
                    else:
                        vdi_grid[j, i] = np.nan
                else:
                    vdi_grid[j, i] = np.nan  # No data for this cell

        return vdi_grid, x_bins, y_bins
    except Exception as e:
        raise ValueError(f"Error processing chunk ({x_min}, {y_min}) - ({x_max}, {y_max}): {str(e)}")


def chunkwise_process(input_las, dtm_raster, output_vdi, chunk_size=100, resolution=2.0, target_resolution=0.5, t_lower=0.8, t_upper=12):
    """
    Process the LAS file chunkwise and calculate the VDI, then resample the VDI to a target resolution.
    
    - input_las: Path to the LAS file.
    - dtm_raster: Path to the DTM raster.
    - output_vdi: Path to the output VDI raster.
    - chunk_size: Size of each chunk (in meters).
    - resolution: Desired resolution for the VDI grid (initial).
    - target_resolution: The target resolution for the resampled VDI grid.
    """
    try:
        # Load LAS file
        las = laspy.read(input_las)

        # Load DTM raster
        with rasterio.open(dtm_raster) as dtm:
            dtm_data = dtm.read(1)
            dtm_transform = dtm.transform
        
        # Define grid boundaries based on LAS file extent
        x_min, x_max = np.min(las.x), np.max(las.x)
        y_min, y_max = np.min(las.y), np.max(las.y)

        # Ensure that the boundaries are integers for the range function
        x_min, x_max = int(np.floor(x_min)), int(np.ceil(x_max))
        y_min, y_max = int(np.floor(y_min)), int(np.ceil(y_max))

        # Prepare an empty array to hold the VDI raster data (same size as the whole area)
        full_vdi_raster = np.full((int((y_max - y_min) // resolution), int((x_max - x_min) // resolution)), np.nan, dtype=np.float32)

        # Process the LAS file in chunks
        for chunk_x in range(x_min, x_max, chunk_size):
            for chunk_y in range(y_min, y_max, chunk_size):
                # Define the chunk boundaries
                chunk_x_min = chunk_x
                chunk_x_max = min(chunk_x + chunk_size, x_max)
                chunk_y_min = chunk_y
                chunk_y_max = min(chunk_y + chunk_size, y_max)

                # Filter LAS points for the chunk
                in_chunk = (
                    (las.x >= chunk_x_min) & (las.x < chunk_x_max) &
                    (las.y >= chunk_y_min) & (las.y < chunk_y_max)
                )
                las_chunk = np.vstack((las.x[in_chunk], las.y[in_chunk], las.z[in_chunk])).transpose()

                # Normalize the LAS points
                normalized_heights = []
                for x, y, z in zip(las_chunk[:, 0], las_chunk[:, 1], las_chunk[:, 2]):
                    # Map LAS point to DTM pixel
                    col, row = ~dtm_transform * (x, y)
                    col, row = int(col), int(row)

                    # Ensure point is within DTM bounds
                    if 0 <= col < dtm_data.shape[1] and 0 <= row < dtm_data.shape[0]:
                        ground_height = dtm_data[row, col]
                        normalized_heights.append(z - ground_height)
                    else:
                        normalized_heights.append(np.nan)
                
                las_chunk[:, 2] = np.array(normalized_heights)

                # Calculate VDI for this chunk
                chunk_vdi, chunk_x_bins, chunk_y_bins = process_chunk(
                    las_chunk, dtm_raster, resolution, chunk_x_min, chunk_x_max, chunk_y_min, chunk_y_max, t_lower, t_upper)

                # Calculate the offset of the current chunk relative to the full raster
                x_offset = (chunk_x_min - x_min) // resolution
                y_offset = (chunk_y_min - y_min) // resolution

                # Place the chunk VDI values into the correct location in the full VDI raster
                full_vdi_raster[int(y_offset):int(y_offset + len(chunk_y_bins) - 1), int(x_offset):int(x_offset + len(chunk_x_bins) - 1)] = chunk_vdi

        # Flip the full VDI raster to correct the orientation
        full_vdi_raster = np.flipud(full_vdi_raster)

        # Resample the full VDI raster to the target resolution (0.5 m)
        target_width = int((x_max - x_min) // target_resolution)
        target_height = int((y_max - y_min) // target_resolution)

        # Create an empty array to hold the resampled VDI raster
        resampled_vdi_raster = np.full((target_height, target_width), np.nan, dtype=np.float32)

        # Reproject and resample the VDI raster
        transform = from_origin(x_min, y_max, target_resolution, target_resolution)
        reproject(
            full_vdi_raster,  # The input VDI raster
            resampled_vdi_raster,  # The output resampled VDI raster
            src_transform=from_origin(x_min, y_max, resolution, resolution),  # Original transform
            src_crs='EPSG:25832',  # CRS for original raster
            dst_transform=transform,  # New transform for target resolution
            dst_crs='EPSG:25832',  # CRS for the output raster
            resampling=Resampling.bilinear  # Use bilinear resampling
        )

        # Write the resampled VDI raster to disk
        metadata = {
            'driver': 'GTiff',
            'count': 1,
            'dtype': 'float32',
            'crs': 'EPSG:25832',  # Adjust CRS if needed
            'width': resampled_vdi_raster.shape[1],
            'height': resampled_vdi_raster.shape[0],
            'transform': transform
        }

        with rasterio.open(output_vdi, 'w', **metadata) as dst:
            dst.write(resampled_vdi_raster, 1)  # Write the resampled data to the first band

        print(f"Resampled VDI raster saved to: {output_vdi}")
    except Exception as e:
        raise RuntimeError(f"Error processing LAS file {input_las} with DTM {dtm_raster}: {str(e)}")
