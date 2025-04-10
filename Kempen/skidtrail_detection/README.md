# Skid Trail Detection

These Python Scripts use normalized DTM, CHM, LRM and VDI for predicting skid trails in forests.

## Intallation

Create the needed environment with the `environment.yml`:
```
conda env create -f environment.yml
```

Activate the environment through your terminal and install missing libraries with pip:
```bash
conda activate skidroad_detection
```

## Download Model

Download the already trained model from T. Kempen and place it into the models folder.
https://gitlab.gwdg.de/tanja.kempen/skidtrail-detection/-/blob/main/models/UNet_test_iou_lossfn_lr_0.0005_bands__0__1__2__3__train_split_0.8_2023-01-04.pt?ref_type=heads

## Usage

Execute `norm.py` after download and preprocess is finished to normalise the input data. Script explains and asks for needed inputs:
```bash
python norm.py
```

Execute `inference.py` to predict skid trails based on the raster stack. Script explains and asks for needed inputs:
```bash
python inference.py
```

Execute `postprocess.py` to filter the predicted values according to T. Kempen:
```bash
python postprocess.py
```
