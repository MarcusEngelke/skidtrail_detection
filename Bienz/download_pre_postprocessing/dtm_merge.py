# -*- coding: latin-1 -*-
# Description: This script collects all .tif files from given directories, merges them into a mosaic,
# and saves the result as a new .tif file in the target directory.
# Author: Marcus Engelke (2025)
import os
import subprocess

# Benutzer nach den ersten zwei Ordnern fragen
ordner_liste = []

while True:
    ordner = input("Bitte geben Sie den vollstandigen Pfad zum Gebiet ein (oder 'nein' zum Beenden): ").strip().strip('"')
    if ordner.lower() == "nein":
        break
    if os.path.isdir(ordner):
        ordner_liste.append(ordner)
    else:
        print("Pfad ist ungultig, bitte erneut eingeben.")

if len(ordner_liste) < 2:
    print("Mindestens zwei Gebiete sind erforderlich.")
    exit()

# Gemeinsamen Basis-Pfad ableiten
base_path = os.path.commonpath(ordner_liste)

# Benutzer nach dem gewünschten Zielordner-Namen fragen
output_ordner_name = input("Bitte geben Sie den Namen fur den Zielordner ein: ").strip()

# Zielordner erstellen
ziel_ordner = os.path.join(base_path, output_ordner_name)
os.makedirs(ziel_ordner, exist_ok=True)

# Relevante Dateiendungen (nur .tif Dateien)
endungen = ['.tif']

# Benutzer nach Präfix für die Ergebnisdateien fragen
datei_prefix = input("Bitte geben Sie das Prafix fur die Ergebnisdateien ein: ").strip()

# Alle TIFF-Dateien sammeln
dateien = []

for ordner in ordner_liste:
    for datei in os.listdir(ordner):
        if datei.endswith(tuple(endungen)):  # Hier werden alle .tif Dateien berücksichtigt
            dateien.append(os.path.join(ordner, datei))

# Überprüfen, ob genügend Dateien gefunden wurden
if len(dateien) < 2:
    print("Nicht genugend .tif-Dateien gefunden. Abbruch.")
    exit()

# Name der Ausgabedatei
output_file = os.path.join(ziel_ordner, f"{datei_prefix}_mosaik.tif")

# GDAL merge aufrufen
cmd = ["gdal_merge.py", "-o", output_file, "-of", "GTiff", "-co", "COMPRESS=LZW"] + dateien
subprocess.run(cmd)

print(f"Gespeichert: {output_file}")
print("Fertig!")
