# DTM Analyzer

This R script analyzes Digital Terrain Models (DTM) by smoothing the DTM and subtracting it from the original. The result highlights ground structures, such as strip roads in forests.

## Installation 

To set up the environment, use the provided `environment.yml` file to create a Conda environment with all necessary dependencies for R. Run the following command in your terminal while beeing in the given folder:

```bash
conda env create -f environment.yml
```
Activate the created environment in your terminal:

```bash
conda activate dtmanalyzer
```
Start an interactive R session and restore the R environment:
```bash
R
renv::restore()
```

## Usage

Run the R script `dtmanalyzer.R` with the path of the input DTM:
```bash
Rscript dtmanalyzer.R /path/to/your/dtm_file.tif
```
The result will be saved in the folder of the given input DTM.
