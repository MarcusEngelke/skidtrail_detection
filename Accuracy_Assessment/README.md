# Accuracy Assessment

These python scripts are for evaluating the results from the skid trail detection and are needed to be run in the download_pre_postprocessing environment.

## Confusion Matrix (Accuracy, Recall, Precision, F1-Score, IoU)

The script `cm.py` requires two input folders: one containing the reference TIFF files and one with the corresponding prediction TIFF files.A path for the output CSV file can also be specified. Note that the prediction and reference rasters must be generated beforehand.

```bash
python cm.py
```

## Lenght of Skid Trails inside AoI

The script `length_aoi.py` calculates the total length of polylines that intersect with given Areas of Interest (AoIs). It requires two shapefiles: one containing the polylines and the other containing the AoIs, and outputs the length of polylines within each AoI. For the predicted skid trails the center lines must be created (QGIS, Python, ...). A tutorial is given by T. Kempen (https://gitlab.gwdg.de/tanja.kempen/skidtrail-detection) - for this analysis the perimeter and area filter was not used, because it didn't work as intended.

```bash
python length_aoi.py
```

## Positional Accuracy of predicted skid trails

The script `length_per.py` calculates the percentage of polyline features that lie within a specified polygon. It clips polyline shapefiles in a given folder using the polygon and outputs the percentage of the polyline's length that falls within the polygon. Simply provide the folder path and polygon shapefile path when prompted. For the predicted skid trails the center lines must be created (QGIS, Python, ...). It is recommended to calculate the total lengths with `length_aoi.py` before.

```bash
python length_per.py
```
