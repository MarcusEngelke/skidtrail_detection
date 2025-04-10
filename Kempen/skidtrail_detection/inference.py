# -*- coding: latin-1 -*-
# Applies a trained PyTorch model to an ALS-derived multi-band raster stack 
# and writes the prediction as a new GeoTIFF file.
# T. Kempen / Adapted by Marcus Engelke

import os
import osgeo.gdal as gdal
import osgeo.gdal_array as gdn
from osgeo import osr
import numpy as np
import torch
from matplotlib import pyplot as plt
import time
from sys import stdout

def get_map_extent(gdal_raster):
    xmin, xres, _, ymax, _, yres = gdal_raster.GetGeoTransform()
    xmax = xmin + (gdal_raster.RasterXSize * xres)
    ymin = ymax + (gdal_raster.RasterYSize * yres)
    if 0. in (ymin, ymax, xmin, xmax): return None
    return {"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax, "xres": xres, "yres": yres}

def read_img(input_file, dim_ordering="HWC", dtype='float32', band_mapping=None, return_extent=False):
    if not os.path.isfile(input_file):
        raise RuntimeError("Input file does not exist. Given path: {}".format(input_file))
    ds = gdal.Open(input_file)
    extent = get_map_extent(ds)
    if band_mapping is None:
        band_mapping = {i + 1: i for i in range(ds.RasterCount)}
    arr = np.empty((len(band_mapping), ds.RasterYSize, ds.RasterXSize), dtype=dtype)
    for src_band, tgt_band in band_mapping.items():
        arr[tgt_band] = gdn.BandReadAsArray(ds.GetRasterBand(src_band))
    if dim_ordering == "HWC":
        arr = np.transpose(arr, (1, 2, 0))
    elif dim_ordering != "CHW":
        raise ValueError("Invalid dim_ordering. Choose 'HWC' or 'CHW'.")
    return (arr, extent) if return_extent else arr

def array_to_tif(array, dst_filename, num_bands='multi', save_background=True, src_raster="", transform=None, crs=None):
    if src_raster != "":
        src_raster = gdal.Open(src_raster)
        x_pixels, y_pixels = src_raster.RasterXSize, src_raster.RasterYSize
    elif transform and crs:
        y_pixels, x_pixels = array.shape[:2]
    else:
        raise RuntimeError("Provide either a source raster file or geotransform and CRS.")
    bands = min(array.shape) if array.ndim == 3 else 1
    if not save_background and array.ndim == 3: bands -= 1
    driver = gdal.GetDriverByName('GTiff')
    datatype_mapping = {
        'byte': gdal.GDT_Byte, 'uint8': gdal.GDT_Byte, 'uint16': gdal.GDT_UInt16,
        'uint32': gdal.GDT_UInt32, 'int8': gdal.GDT_Byte, 'int16': gdal.GDT_Int16,
        'int32': gdal.GDT_Int32, 'float16': gdal.GDT_Float32, 'float32': gdal.GDT_Float32
    }
    options = ["COMPRESS=DEFLATE"]
    if array.dtype == np.float16:
        options.append("NBITS=16")
    out = driver.Create(dst_filename, x_pixels, y_pixels, 1 if num_bands == 'single' else bands,
                        datatype_mapping[str(array.dtype)], options=options)
    if src_raster != "":
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
    elif num_bands == 'single':
        singleband = sum((i + 1) * array[:, :, i] for i in range(bands))
        out.GetRasterBand(1).WriteArray(singleband)
        out.GetRasterBand(1).SetNoDataValue(0)
    else:
        for i in range(bands):
            out.GetRasterBand(i + 1).WriteArray(array[:, :, i])
            out.GetRasterBand(i + 1).SetNoDataValue(0)
    out.FlushCache()

def compute_pyramid_patch_weight_loss(width, height):
    xc, yc = width * 0.5, height * 0.5
    Dcx = np.square(np.arange(width) - xc + 0.5)
    Dcy = np.square(np.arange(height) - yc + 0.5)
    Dc = np.sqrt(Dcx[np.newaxis].T + Dcy)
    De_x = np.sqrt(np.minimum(
        np.square(np.arange(width) - 0.5),
        np.square(np.arange(width) - width + 0.5)))
    De_y = np.sqrt(np.minimum(
        np.square(np.arange(height) - 0.5),
        np.square(np.arange(height) - height + 0.5)))
    De = np.minimum(De_x[np.newaxis].T, De_y)
    alpha = (width * height) / np.sum(De / (Dc + De))
    return alpha * (De / (Dc + De))

def predict_on_array_cf(model,
                        arr,
                        in_shape,
                        out_bands,
                        stride=None,
                        drop_border=0,
                        batchsize=64,
                        dtype="float32",
                        device="cpu",
                        augmentation=False,
                        no_data=None,
                        verbose=False,
                        report_time=False,
                        return_data_region=False):
    """
    Applies a pytorch segmentation model to an array in a strided manner.

    Channels first version.

    Call model.eval() before use!

    Args:
        model: pytorch model - make sure to call model.eval() before using this function!
        arr: CHW array for which the segmentation should be created
        stride: stride with which the model should be applied. Default: output size
        batchsize: number of images to process in parallel
        dtype: desired output type (default: float32)
        augmentation: whether to average over rotations and mirrorings of the image or not. triples computation time.
        no_data: a no-data vector. its length must match the number of layers in the input array.
        verbose: whether or not to display progress
        report_time: if true, returns (result, execution time)

    Returns:
        An array containing the segmentation.
    """
    t0 = None

    # model.eval()

    if augmentation:
        operations = (lambda x: x,
                      lambda x: np.rot90(x, 1, axes=(1, 2)),
                      # lambda x: np.rot90(x, 2),
                      # lambda x: np.rot90(x, 3),
                      # lambda x: np.flip(x,0),
                      lambda x: np.flip(x, 1))

        inverse = (lambda x: x,
                   lambda x: np.rot90(x, -1, axes=(1, 2)),
                   # lambda x: np.rot90(x, -2),
                   # lambda x: np.rot90(x, -3),
                   # lambda x: np.flip(x,0),
                   lambda x: np.flip(x, 1))
    else:
        operations = (lambda x: x,)
        inverse = (lambda x: x,)

    assert in_shape[1] == in_shape[2], "Input shape must be equal in last two dims."
    out_shape = (out_bands, in_shape[1] - 2 * drop_border, in_shape[2] - 2 * drop_border)
    in_size = in_shape[1]
    out_size = out_shape[1]
    stride = stride or out_size
    pad = (in_size - out_size) // 2
    assert pad % 2 == 0, "Model input and output shapes have to be divisible by 2."

    original_size = arr.shape
    ymin = 0
    xmin = 0

    if no_data is not None:
        # assert arr.shape[-1]==len(no_data_vec), "Length of no_data_vec must match number of channels."
        # data_mask = np.all(arr[:,:,0].reshape( (-1,arr.shape[-1]) ) != no_data, axis=1).reshape(arr.shape[:2])
        nonzero = np.nonzero(arr[0, :, :] - no_data)
        if len(nonzero[0]) == 0:
            if return_data_region:
                return None, (0, 0, 0, 0)
            else:
                return None
        ymin = np.min(nonzero[0])
        ymax = np.max(nonzero[0])
        xmin = np.min(nonzero[1])
        xmax = np.max(nonzero[1])
        img = arr[:, ymin:ymax, xmin:xmax]

    else:
        img = arr

    weight_mask = compute_pyramid_patch_weight_loss(out_size, out_size)
    final_output = np.zeros((out_bands,) + img.shape[1:], dtype=dtype)

    op_cnt = 0
    for op, inv in zip(operations, inverse):
        img = op(img)
        img_shape = img.shape
        x_tiles = int(np.ceil(img.shape[2] / stride))
        y_tiles = int(np.ceil(img.shape[1] / stride))

        y_range = range(0, (y_tiles + 1) * stride - out_size, stride)
        x_range = range(0, (x_tiles + 1) * stride - out_size, stride)

        y_pad_after = y_range[-1] + in_size - img.shape[1] - pad
        x_pad_after = x_range[-1] + in_size - img.shape[2] - pad

        output = np.zeros((out_bands,) + (img.shape[1] + y_pad_after - pad, img.shape[2] + x_pad_after - pad),
                          dtype=dtype)
        division_mask = np.zeros(output.shape[1:], dtype=dtype) + 1E-7
        img = np.pad(img, ((0, 0), (pad, y_pad_after), (pad, x_pad_after)), mode='reflect')

        patches = len(y_range) * len(x_range)

        def patch_generator():
            for y in y_range:
                for x in x_range:
                    yield img[:, y:y + in_size, x:x + in_size]

        patch_gen = patch_generator()

        y = 0
        x = 0
        patch_idx = 0
        batchsize_ = batchsize

        t0 = time.time()

        while patch_idx < patches:
            batchsize_ = min(batchsize_, patches, patches - patch_idx)
            patch_idx += batchsize_
            if verbose: stdout.write("\r%.2f%%" % (100 * (patch_idx + op_cnt * patches) / (len(operations) * patches)))

            batch = np.zeros((batchsize_,) + in_shape, dtype=dtype)

            for j in range(batchsize_):
                batch[j] = next(patch_gen)

            with torch.no_grad():
                prediction = model(torch.from_numpy(batch).to(device=device, dtype=torch.float32))
                prediction = prediction.detach().cpu().numpy()
            if drop_border > 0:
                prediction = prediction[:, :, drop_border:-drop_border, drop_border:-drop_border]

            for j in range(batchsize_):
                output[:, y:y + out_size, x:x + out_size] += prediction[j] * weight_mask[None, ...]
                division_mask[y:y + out_size, x:x + out_size] += weight_mask
                x += stride
                if x + out_size > output.shape[2]:
                    x = 0
                    y += stride

        output = output / division_mask[None, ...]
        output = inv(output[:, :img_shape[1], :img_shape[2]])
        final_output += output
        img = arr[:, ymin:ymax, xmin:xmax] if no_data is not None else arr
        op_cnt += 1
        if verbose: stdout.write("\rAugmentation step %d/%d done.\n" % (op_cnt, len(operations)))

    if verbose: stdout.flush()

    final_output = final_output / len(operations)

    if no_data is not None:
        final_output = np.pad(final_output,
                              ((0, 0), (ymin, original_size[1] - ymax), (xmin, original_size[2] - xmax)),
                              mode='constant',
                              constant_values=0)

    if report_time:
        return final_output, time.time() - t0
    elif return_data_region:
        return final_output, (ymin, ymax, xmin, xmax)
    else:
        return final_output


# ------------------------------------------------------------------------------
# EXECUTION
# ------------------------------------------------------------------------------

# Aktuelles Verzeichnis des Skripts ermitteln
script_dir = os.path.dirname(os.path.realpath(__file__))

# Relativer Pfad zum Modell
model_path = os.path.join(script_dir, "models", "UNet_test_iou_lossfn_lr_0.0005_bands__0__1__2__3__train_split_0.8_2023-01-04.pt")

# Modell laden
model = torch.jit.load(model_path)
model.to("cpu")  # Falls du das Modell auf CPU ausführen möchtest
model.eval()

input_file = input("Bitte geben Sie den vollständigen Pfad zum Rasterstack ein: ").strip().strip('"')
img = read_img(input_file, dim_ordering="CHW")[[0, 1, 2, 3]]

pred = predict_on_array_cf(model, img, in_shape=(4,448,448), out_bands=1, stride=224, augmentation=True)

base, ext = os.path.splitext(input_file)
output_path = base + "_pred" + ext

array_to_tif(pred.transpose(1, 2, 0), output_path, src_raster=input_file)
