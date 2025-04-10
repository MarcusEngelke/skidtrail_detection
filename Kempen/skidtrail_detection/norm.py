# -*- coding: latin-1 -*-
# This script loads, normalizes, and stacks multiple ALS-derived raster layers 
# (DTM, CHM, LRM, VDI) into a single multi-channel GeoTIFF for further analysis.
# T. Kempen / Adapted by Marcus Engelke

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import os
import osgeo.gdal as gdal
import osgeo.gdal_array as gdn
from osgeo import osr


def get_map_extent(gdal_raster):
    """Returns a dict of {xmin, xmax, ymin, ymax, xres, yres} of a given GDAL raster file."""
    xmin, xres, xskew, ymax, yskew, yres = gdal_raster.GetGeoTransform()
    xmax = xmin + (gdal_raster.RasterXSize * xres)
    ymin = ymax + (gdal_raster.RasterYSize * yres)
    ret = {"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax, "xres": xres, "yres": yres}
    if 0. in (ymin, ymax, xmin, xmax): return None
    return ret


def read_img(input_file, dim_ordering="HWC", dtype='float32', band_mapping=None, return_extent=False):
    """Reads an image from disk and returns it as numpy array."""
    print(f"Opening file: {input_file}")
    if not os.path.isfile(input_file):
        raise RuntimeError(f"Input file does not exist: {input_file}")
    
    ds = gdal.Open(input_file)
    if ds is None:
        raise RuntimeError(f"Failed to open file: {input_file}")
    
    extent = get_map_extent(ds)

    if band_mapping is None:
        num_bands = ds.RasterCount
        band_mapping = {i + 1: i for i in range(num_bands)}
    elif isinstance(band_mapping, dict):
        num_bands = len(band_mapping)
    else:
        raise TypeError("band_mapping must be a dict.")

    arr = np.empty((num_bands, ds.RasterYSize, ds.RasterXSize), dtype=dtype)

    for source_layer, target_layer in band_mapping.items():
        arr[target_layer] = gdn.BandReadAsArray(ds.GetRasterBand(source_layer))

    if dim_ordering == "HWC":
        arr = np.transpose(arr, (1, 2, 0))
    elif dim_ordering != "CHW":
        raise ValueError("Dim ordering not supported. Use 'HWC' or 'CHW'.")

    return (arr, extent) if return_extent else arr


def normalize_percentile(data, low=1, high=99, nodata_value=0):
    """Normalizes data by applying a percentile cut stretch bandwise."""
    datamask = data != nodata_value
    pmin = np.array([np.percentile(data[:, :, i][datamask[:, :, i]], q=low) for i in range(data.shape[-1])])
    pmax = np.array([np.percentile(data[:, :, i][datamask[:, :, i]], q=high) for i in range(data.shape[-1])])
    res = np.clip((data - pmin) / (pmax - pmin + 1E-10), 0, 1)
    return res


def array_to_tif(array, dst_filename, num_bands='multi', save_background=True, src_raster: str = "", transform=None, crs=None):
    """Takes a numpy array and writes a tif. Uses deflate compression."""
    if src_raster:
        src_raster = gdal.Open(src_raster)
        x_pixels = src_raster.RasterXSize
        y_pixels = src_raster.RasterYSize
    elif transform is not None and crs is not None:
        y_pixels, x_pixels = array.shape[:2]
    else:
        raise RuntimeError("Please provide either a source raster file or geotransform and CRS.")

    bands = min(array.shape) if array.ndim == 3 else 1
    if not save_background and array.ndim == 3:
        bands -= 1

    driver = gdal.GetDriverByName('GTiff')

    datatype_mapping = {
        'byte': gdal.GDT_Byte, 'uint8': gdal.GDT_Byte, 'uint16': gdal.GDT_UInt16,
        'uint32': gdal.GDT_UInt32, 'int8': gdal.GDT_Byte, 'int16': gdal.GDT_Int16,
        'int32': gdal.GDT_Int32, 'float16': gdal.GDT_Float32, 'float32': gdal.GDT_Float32
    }
    options = ["COMPRESS=DEFLATE"]
    if array.dtype == "float16":
        options.append("NBITS=16")

    out = driver.Create(dst_filename, x_pixels, y_pixels, 1 if num_bands == 'single' else bands, datatype_mapping[str(array.dtype)], options=options)

    if src_raster:
        out.SetGeoTransform(src_raster.GetGeoTransform())
        out.SetProjection(src_raster.GetProjection())
    else:
        out.SetGeoTransform(transform)
        srs = osr.SpatialReference()
        srs.ImportFromProj4(crs)
        out.SetProjection(srs.ExportToWkt())

    if array.ndim == 2:
        out.GetRasterBand(1).WriteArray(array)
        out.GetRasterBand(1).SetNoDataValue(0)
    else:
        if num_bands == 'single':
            singleband = np.zeros(array.shape[:2], dtype=array.dtype)
            for i in range(bands):
                singleband += (i + 1) * array[:, :, i]
            out.GetRasterBand(1).WriteArray(singleband)
            out.GetRasterBand(1).SetNoDataValue(0)
        elif num_bands == 'multi':
            for i in range(bands):
                out.GetRasterBand(i + 1).WriteArray(array[:, :, i])
                out.GetRasterBand(i + 1).SetNoDataValue(0)

    out.FlushCache()


# === Hauptausführung ===
data_types = ["DTM", "CHM", "LRM", "VDI"]

base_path = input("Bitte geben Sie den vollständigen Pfad zum Datenordner ein: ").strip().replace('"', '').replace("'", "")
location_names = input("Bitte geben Sie den Location-Namen ein: ").strip().replace('"', '').replace("'", "")

data = [[np.nan_to_num(read_img(f"{base_path}/{location_names}_{t}.tif")) for t in data_types]]
data = [np.concatenate(loc, axis=2) for loc in data]

for (d, loc) in zip(data, [location_names]):
    array_to_tif(
        normalize_percentile(d).astype(np.float32),
        os.path.join(base_path, f"{loc}.tif"),
        src_raster=os.path.join(base_path, f"{loc}_DTM.tif")
    )
