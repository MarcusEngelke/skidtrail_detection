# Accuracy Assessment

These python scripts are for evaluating the results from the skid trail detection and are needed to be run in the download_pre_postprocessing environment.

## Confusion Matrix (Accuracy, Recall, Precision, F1-Score, IoU)

The script requires two input folders: one containing the reference TIFF files and one with the corresponding prediction TIFF files.A path for the output CSV file can also be specified. Note that the prediction and reference rasters must be generated beforehand.

```bash
python cm.py
```
