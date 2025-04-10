# -*- coding: latin-1 -*-
# This script calculates the total length of polylines that lie within given Areas of Interest (AoIs).
# It reads two shapefiles: one containing the polylines and one containing the AoIs, clips the polylines based on the AoIs,
# and outputs the length of the overlapping portions for each AoI.
# Author: Marcus Engelke (2025)

import geopandas as gpd
from shapely.geometry import MultiLineString

# Interaktive Eingabe der Shapefile-Pfade
polylines_shapefile = input("Gib den Pfad zum Shapefile mit den Polylinien ein: ").replace(" ", "").replace('"', '').replace("'", '')
aoi_shapefile = input("Gib den Pfad zum Shapefile mit den AoIs ein: ").replace(" ", "").replace('"', '').replace("'", '')

# Lade die Polylinien- und AoI-Shapefiles
polylines = gpd.read_file(polylines_shapefile)
aoi = gpd.read_file(aoi_shapefile)

# Stelle sicher, dass beide Shapefiles dasselbe Koordinatensystem haben
if polylines.crs != aoi.crs:
    polylines = polylines.to_crs(aoi.crs)

# Ausgabe der Geometrie-Informationen
print(f"Polylinien CRS: {polylines.crs}")
print(f"AoI CRS: {aoi.crs}")

# Durchlaufe jedes AoI und clippe die Polylinien für jedes AoI
for _, aoi_row in aoi.iterrows():
    aoi_geom = aoi_row.geometry
    total_length = 0  # Gesamtlänge der Polylinien im aktuellen AoI

    # Überprüfe jede Polylinie
    for _, polyline_row in polylines.iterrows():
        polyline_geom = polyline_row.geometry
        # Schneide die Polylinie mit dem AoI-Geometrie (clippe den Teil der Linie im AoI)
        if polyline_geom.intersects(aoi_geom):  # Wenn eine Überlappung existiert
            clipped_geom = polyline_geom.intersection(aoi_geom)  # Die tatsächliche Überlappung
            if isinstance(clipped_geom, MultiLineString):
                total_length += sum([line.length for line in clipped_geom])  # Summe der Längen der einzelnen Linien
            else:
                total_length += clipped_geom.length  # Einzelne Linie
    # Ausgabe der Ergebnisse für das aktuelle AoI
    print(f"AoI_ID {aoi_row['AoI']}: {total_length}")