# -*- coding: latin-1 -*-
# Description: This script downloads elevation data (DOM, DGM, LAS) for a given area and time period 
# from the Thüringen Geoportal, extracts the content, optionally converts XYZ to GeoTIFF (EPSG:25832),
# and cleans up unnecessary files.
# Author: Marcus Engelke (2025)

import os
import requests
import zipfile
from osgeo import gdal

def download_and_extract_files(area_code, period="2020-2025", download_dir="downloads"):
    """
    Downloads and extracts the required files based on area_code and period, then removes unneeded files.
    If the period is "2010-2013" or "2014-2019", converts XYZ files to TIFF.
    """

    # Initialize variables for the period
    if period == "2020-2025":
        prefix = "32_"     # Prefix for 2020-2025
        dom_type = "dom1"  # dom1 for 2020-2025
        dgm_type = "dgm1"  # dgm1 for 2020-2025
        las_type = "las"   # las1 for 2020-2025
        download_xyz = False  # No need to convert XYZ
    elif period == "2014-2019":
        prefix = ""        # No prefix for 2014-2019
        dom_type = "dom1"  # dom1 for 2014-2019
        dgm_type = "dgm1"  # dgm1 for 2014-2019
        las_type = "las"   # las1 for 2014-2019
        download_xyz = True  # Need to convert XYZ
    elif period == "2010-2013":
        prefix = ""      # Prefix for 2010-2013
        dom_type = "dom2"  # dom2 for 2010-2013
        dgm_type = "dgm2"  # dgm2 for 2010-2013
        las_type = "las"   # las2 for 2010-2013
        download_xyz = True  # Need to convert XYZ
    else:
        print("Unknown period!")
        return None
    
    # Base URLs with placeholders for the area code and period
    base_url_dom = f"https://geoportal.geoportal-th.de/hoehendaten/DOM/dom_{period}/{dom_type}_{prefix}{area_code}_1_th_{period}.zip"
    base_url_dgm = f"https://geoportal.geoportal-th.de/hoehendaten/DGM/dgm_{period}/{dgm_type}_{prefix}{area_code}_1_th_{period}.zip"
    base_url_las = f"https://geoportal.geoportal-th.de/hoehendaten/LAS/las_{period}/{las_type}_{prefix}{area_code}_1_th_{period}.zip"
    
    # List of URLs
    urls = [base_url_dom, base_url_dgm, base_url_las]
    print(base_url_dom)
    print(base_url_dgm)
    print(base_url_las)
    
    # Create the target directory if it doesn't exist
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # Create an empty list to store extracted directories
    extracted_dirs = []

    # Download and extract the files
    for url in urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                filename = url.split("/")[-1].split("?")[0]  # Extract filename from the URL
                file_path = os.path.join(download_dir, filename)  # Full path for saving
                
                # Save the ZIP file
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"The file '{filename}' was successfully downloaded to {download_dir}.")
                
                # Extract folder name from the first ZIP file (everything after the first _ and before .zip)
                folder_name = filename.split("_", 1)[1].split(".zip")[0]  # Remove ".zip" and before the first "_"
                extract_dir = os.path.join(download_dir, folder_name)  # New folder path
                
                # Create the folder for extraction if it doesn't exist
                if not os.path.exists(extract_dir):
                    os.makedirs(extract_dir)

                # Extract the ZIP file directly into the target folder
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                print(f"Extracted the ZIP file to {extract_dir}.")
                
                if download_xyz:
                  # Process each extracted XYZ file and convert to TIFF
                  for root, dirs, files in os.walk(extract_dir):
                      for file in files:
                          if file.endswith(".xyz"):
                              xyz_file_path = os.path.join(root, file)
                              tiff_file_path = os.path.join(extract_dir, file.replace(".xyz", ".tif"))
                              
                              # Setze die Koordinatensystem (EPSG:25832)
                              proj_srs = "EPSG:25832"  # EPSG für UTM Zone 32N (Deutschland)
                              
                              # Umwandlung der XYZ-Datei in TIFF mit EPSG:25832
                              gdal.Translate(tiff_file_path, xyz_file_path, format='GTiff', 
                                             outputSRS=proj_srs)
                              
                              print(f"Datei erfolgreich umgewandelt: {tiff_file_path}")  # Verwende tiff_file_path hier
                
                # Delete all files except .tif and .laz files
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if not file.endswith(('.tif', '.laz')):
                            file_path_to_delete = os.path.join(root, file)
                            os.remove(file_path_to_delete)
                            print(f"Deleted unwanted file: {file}")
                
                # Now remove the original zip file
                os.remove(file_path)
                print(f"Deleted the ZIP file: {filename}")
                
                # Store the extracted directory in the list
                extracted_dirs.append(extract_dir)
            
            else:
                print(f"Error downloading {url}: {response.status_code}")
        except Exception as e:
            print(f"Error processing the URL {url}: {e}")
            
    return extract_dir

