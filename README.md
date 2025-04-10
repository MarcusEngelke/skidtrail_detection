# skidtrail_detection
semi-automatic skidtrail detection in forests based on two different models

This repository is based on two different models for predicting skid trails in forests. The Bienz model is based on the work of Raffael Bienz (https://github.com/RaffiBienz/skidroad_finder) and the Kempen model is based on the work of Tanja Kempen (https://gitlab.gwdg.de/tanja.kempen/skidtrail-detection). 

Created by Marcus Engelke for his master thesis.

The given models were improved for a more automated processing for big forest areas in Thuringia, Germany. Both models were pretrained and are based on a U-Net architecture.

## Bienz Method

## Kempen Method

## Create download_pre_postprocessing environment

To set up the environment, use the provided environment.yml file to create a Conda environment with all necessary dependencies for Python.

```bash
conda env create -f environment.yml
```

To activate this enviroment use:

```bash
conda activate download_pre_postprocessing
```

### Usage of download_pre_postprocessing envrionment
- Method Bienz:
  - Download Data
  - Merge Data
  - Create AoI
- Method Kempen:
  - Download, Merge and Preprocess Data
  - Postprocess Data 
