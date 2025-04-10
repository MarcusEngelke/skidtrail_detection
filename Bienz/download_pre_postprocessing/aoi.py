# -*- coding: latin-1 -*-
# Description: This script converts the bounding box of a GeoTIFF file to a shapefile.
# It extracts the bounding box of the raster and saves it as a shapefile in the same directory.
# Author: Marcus Engelke (2025)
import os
import rasterio
import geopandas as gpd
from shapely.geometry import box

def tif_to_shp(tif_path):
    """
    Converts the bounding box of a GeoTIFF file to a shapefile.
    """
    if not os.path.exists(tif_path):
        print(f"Error: File {tif_path} not found.")
        return

    # Get the directory and filename without extension for saving the shapefile
    dir_path = os.path.dirname(tif_path)
    base_name = os.path.splitext(os.path.basename(tif_path))[0]
    shp_path = os.path.join(dir_path, f"{base_name}_bounding_box.shp")

    # Open the TIFF file
    with rasterio.open(tif_path) as src:
        # Get the bounding box of the raster
        bounds = src.bounds
        # Create a polygon from the bounding box
        bounding_box = box(bounds[0], bounds[1], bounds[2], bounds[3])

        # Create a GeoDataFrame with the bounding box polygon
        gdf = gpd.GeoDataFrame(geometry=[bounding_box], crs=src.crs)

        # Save the bounding box as a shapefile
        gdf.to_file(shp_path)
        print(f"Shapefile saved: {shp_path}")

if __name__ == "__main__":
    tif_path = input("Enter the path to the TIFF file: ").replace('"', '').replace("'", "").strip()
    tif_to_shp(tif_path)
