# -*- coding: latin-1 -*-
# Description: This script downloads DGM data based on an area code and period, extracts the files,
# and converts XYZ files to TIFF format if found.import os
# Author: Marcus Engelke (2025)

import os
import sys
import requests
import zipfile
from osgeo import gdal  # Für die Umwandlung von XYZ in TIFF

def download_and_extract_dgm(area_code, period, download_dir):
    """
    Downloads and extracts only the DGM files based on area_code and period, then removes unneeded files.
    Converts XYZ files to TIFF if they are found in the extracted content.
    """

    # Initialisiere Variablen je nach Periode
    if period == "2020-2025":
        prefix = "32_"
        dgm_type = "dgm1"
    elif period == "2014-2019":
        prefix = ""
        dgm_type = "dgm1"
    elif period == "2010-2013":
        prefix = ""
        dgm_type = "dgm2"
    else:
        print("Unknown period!")
        return None

    # Erstelle die URL für den Download
    base_url_dgm = f"https://geoportal.geoportal-th.de/hoehendaten/DGM/dgm_{period}/{dgm_type}_{prefix}{area_code}_1_th_{period}.zip"
    print(f"Downloading from: {base_url_dgm}")

    # Erstelle das Download-Verzeichnis, falls es nicht existiert
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    try:
        response = requests.get(base_url_dgm, stream=True)
        if response.status_code == 200:
            filename = base_url_dgm.split("/")[-1]
            file_path = os.path.join(download_dir, filename)

            # Extrahiere den Ordnernamen aus dem ZIP-Dateinamen
            folder_name = filename.split("_", 1)[1].split(".zip")[0]
            extract_dir = os.path.join(download_dir, folder_name)

            # Erstelle den Zielordner
            os.makedirs(extract_dir, exist_ok=True)

            # Speichere die ZIP-Datei
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded: {filename}")

            # Entpacke die ZIP-Datei
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"Extracted to: {extract_dir}")

            # Überprüfe auf Dateien und führe die Umwandlung durch
            xyz_found = False
            for root, _, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith(".xyz"):
                        xyz_found = True  # Wenn XYZ-Datei gefunden wird
                    if not file.endswith(('.xyz', '.meta', '.tif')):
                        os.remove(os.path.join(root, file))  # Lösche alle anderen Dateien
                        print(f"Deleted: {file}")

            # Falls XYZ-Dateien gefunden wurden, dann Umwandlung in TIFF
            if xyz_found:
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file.endswith(".xyz"):
                            xyz_file_path = os.path.join(root, file)
                            tiff_file_path = os.path.join(extract_dir, file.replace(".xyz", ".tif"))
                            
                            # Setze das Koordinatensystem (EPSG:25832)
                            proj_srs = "EPSG:25832"  # EPSG für UTM Zone 32N (Deutschland)
                            
                            # Umwandlung der XYZ-Datei in TIFF mit EPSG:25832
                            gdal.Translate(tiff_file_path, xyz_file_path, format='GTiff', 
                                           outputSRS=proj_srs)
                            
                            print(f"Datei erfolgreich umgewandelt: {tiff_file_path}")

            # Lösche alle Dateien außer .tif
            for root, _, files in os.walk(extract_dir):
                for file in files:
                    if not file.endswith('.tif'):
                        os.remove(os.path.join(root, file))  # Lösche alle anderen Dateien
                        print(f"Deleted non-TIF file: {file}")

            # Entferne die ursprüngliche ZIP-Datei
            os.remove(file_path)
            print(f"Deleted ZIP file: {filename}")

            return extract_dir
        else:
            print(f"Download failed: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    return None


if __name__ == "__main__":
    # Überprüfe die Argumente aus dem Bash-Skript
    if len(sys.argv) != 4:
        print("Usage: python3 dgm_download.py <DOWNLOAD_PATH> <AREA_CODE> <PERIOD>")
        sys.exit(1)

    download_dir = sys.argv[1]
    area_code = sys.argv[2]
    period = sys.argv[3]

    download_and_extract_dgm(area_code, period, download_dir)
