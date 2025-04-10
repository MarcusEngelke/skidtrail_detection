# -*- coding: latin-1 -*-
# This script calculates the percentage of polyline features that lie within a given polygon.
# It clips the polyline shapefiles in the specified folder with the provided polygon shapefile and calculates the length of clipped features
# compared to the original length. The result is output as a percentage for each polyline shapefile.
# Author: Marcus Engelke (2025)

import geopandas as gpd
import os

# Eingabe von Ordnerpfad und Polygon-Datei
folder_path = input("Bitte den Pfad zum Ordner mit den Shapefiles eingeben: ").strip().replace('"', '').replace("'", '')
polygon_path = input("Bitte den Pfad zum Polygon-Shapefile eingeben: ").strip().replace('"', '').replace("'", '')

# Laden des Polygons
polygon = gpd.read_file(polygon_path)

# Gehe alle Shapefiles im angegebenen Ordner durch
for filename in os.listdir(folder_path):
    if filename.endswith('_diss.shp'):
        file_path = os.path.join(folder_path, filename)
        
        # Laden der Polylinien
        lines = gpd.read_file(file_path)
        
        # Clippe die Polylinien mit dem Polygon
        clipped_lines = gpd.clip(lines, polygon)
        
        # Berechne die Länge der ursprünglichen und der geclippten Linien
        original_length = lines.geometry.length.sum()
        clipped_length = clipped_lines.geometry.length.sum()
        
        # Berechne den Prozentsatz der Linien innerhalb des Polygons
        if original_length > 0:
            percentage_within = (clipped_length / original_length) * 100
        else:
            percentage_within = 0
        
        # Ausgabe des Ergebnisses
        print(f"{filename} innerhalb von {os.path.basename(polygon_path)}: {percentage_within:.2f}%")



