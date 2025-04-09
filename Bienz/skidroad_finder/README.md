# Skid Trail Detection

This R and Python Script uses a manipulated DTM for predicting skid trails in forests.

## Intallation

Installation is simmilar to the original repository (https://github.com/RaffiBienz/skidroad_finder).

Create the needed environment:
```
conda create -y -n skidroad_finder python==3.8
```

Activate the environment through your terminal:
```bash
conda activate skidroad_finder
pip install -r ./src/requirements.txt
```

Setup R according to R. Bienz

## Download Model

Download the already trained model from R. Bienz and place it into the model folder.
https://drive.google.com/file/d/1-19k1sK8yHX16nlxd5rZcjLhEjcobTg0

## Usage

Execute main.R with needed arguments:
```bash
Rscript ./src/main.R <Path to dtm(tif)> <Path to Area of Interest(shp)>
```



