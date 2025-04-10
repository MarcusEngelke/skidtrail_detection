# Download and process data

These python scripts are for downloading ALS data from turingia and basic data preperation for further analysis. These scripts are needed to be run in the download_pre_postprocessing environment.

## Download and calculate CHM, LRM and VDI

`main.py` is used for downloading ALS data from turingia with given input paramters and to calculate CHM, LRM and VDI:
- download_path: path to save the data
- area_code: each area has a unique area ID (629_5610)
- data period: period from when the ALS data is from (2010-2013; 2014-2019; 2020-2025)

```bash
python main.py <download_path> <area_code> <data period>
```


