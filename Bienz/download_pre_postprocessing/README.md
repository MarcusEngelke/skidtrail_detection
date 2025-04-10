# Download and process data

These python scripts are for downloading ALS data from turingia and basic data preperation for further analysis.

## Download 

`dtm_download.py` is used for downloading dtm data from turingia with given input paramters:
- download_path: path to save the data
- area_code: each area has a unique area ID (629_5610)
- data period: period from when the ALS data is from (2010-2013; 2014-2019; 2020-2025)

```bash
python dtm_download.py <download_path> <area_code> <data period>
```

## Merge

`dtm_merge.py`is used for mosaicing neighboring tifs to one big tif. Script explains and asks for needed inputs:

```bash
python dtm_merge.py
```

## Area of Interest

`aoi.py` is used for creating and AoI for the whole given input tif which is needed fur the prediction. Script explains and asks for needed inputs:

```bash
python aoi.py
```


