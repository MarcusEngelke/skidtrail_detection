# -*- coding: latin-1 -*-
# This script compares reference and prediction TIFFs for multiple Areas of Interest (AoIs),
# calculates evaluation metrics (e.g., confusion matrix, F1-score, Cohen's Kappa), and saves the results to a CSV file.
# Author: Marcus Engelke (2025)

import os
import rasterio
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, cohen_kappa_score

# Nutzer gibt Pfade zu den Verzeichnissen ein
ref_directory = input("Pfad zum Verzeichnis mit den Referenz-TIFFs angeben: ").strip().replace(" ", "").replace('"', '').replace("'", '')
pred_directory = input("Pfad zum Verzeichnis mit den Vorhersage-TIFFs angeben: ").strip().replace(" ", "").replace('"', '').replace("'", '')
# Benutzer gibt den Pfad zur CSV-Ausgabedatei ein
output_file = input("Pfad zur CSV-Ausgabedatei angeben (z. B. /home/user/metrics_output.csv): ").strip().replace(" ", "").replace('"', '').replace("'", '')

# Dateien im Verzeichnis suchen
ref_tif_files = [f for f in os.listdir(ref_directory) if f.endswith('.tif')]
pred_tif_files = [f for f in os.listdir(pred_directory) if f.endswith('.tif')]

# Paare von Referenz- und Vorhersage-TIFFs erstellen
aoi_pairs = {}

for ref_file in ref_tif_files:
    # Beispiel für die Namenskonvention: "Wohlrose_Tracks_ref_AoI1.tif"
    # "Wohlrose" extrahieren (alles vor "_Tracks")
    area_name = ref_file.split('_Tracks')[0]
    
    # "AoI1" extrahieren
    aoi_name = ref_file.split('_AoI')[1].split('.')[0]  # Z.B. "AoI1" extrahieren
    
    # Debugging-Ausgabe, um zu sehen, welche Datei wir gerade verarbeiten
    print(f"Uberprufe Referenz-Datei: {ref_file}")
    
    # Suche nach der passenden Vorhersage-Datei, die den gleichen "AoI"-Teil hat
    pred_file = next((f for f in pred_tif_files if f'AoI{aoi_name}' in f), None)
    
    if pred_file:
        print(f"Gefundenes Vorhersage-Paar: {pred_file}")  # Ausgabe für das Paar
        aoi_pairs[aoi_name] = {
            'area': area_name,
            'ref': os.path.join(ref_directory, ref_file),
            'pred': os.path.join(pred_directory, pred_file)
        }
    else:
        print(f"Kein passendes Vorhersage-Paar fur {aoi_name} gefunden.")

# Überprüfen, ob Paare gebildet wurden
if not aoi_pairs:
    print("Keine AoI-Paare gefunden.")
else:
    print(f"Gefundene AoI-Paare: {aoi_pairs}")

    # DataFrame erstellen, um die Metriken zu speichern
    metrics_list = []

    # Confusion Matrix für jedes Paar berechnen
    for aoi_name, paths in aoi_pairs.items():
        print(f"\nVerarbeite AoI: {aoi_name}, Gebietsname: {paths['area']}")
        
        # Zeitraum aus dem Vorhersage-Pfad extrahieren (z. B. 2020_2025)
        period = None
        for p in ['2020_2025', '2014_2019', '2010_2013']:
            if p in paths['pred']:
                period = p
                break
        
        # Falls kein Zeitraum gefunden wird, Warnung ausgeben
        if not period:
            print(f"Warnung: Kein Zeitraum im Pfad gefunden fur AoI {aoi_name}, Gebietsname: {paths['area']}")
        
        # TIFFs laden
        with rasterio.open(paths['ref']) as ref_src, rasterio.open(paths['pred']) as pred_src:
            ref_data = ref_src.read(1)  # Erstes Band laden
            pred_data = pred_src.read(1)

            # Prüfen, ob beide Raster die gleiche Form haben
            if ref_data.shape != pred_data.shape:
                raise ValueError(f"Fehler: Die Raster fur AoI {aoi_name} haben unterschiedliche Grossen!")

            # NoData-Werte ignorieren (255 wird nicht in die Berechnung einbezogen)
            mask = (ref_data != 255) & (pred_data != 255)
            ref_data = ref_data[mask]
            pred_data = pred_data[mask]

            # Confusion Matrix berechnen
            cm = confusion_matrix(ref_data.flatten(), pred_data.flatten(), labels=[0, 1])

        # Confusion Matrix ausgeben
        tn, fp, fn, tp = cm.ravel()
        print("\n====== CONFUSION MATRIX ======")
        print(f"True Negatives  (TN): {tn}")  # Kein Track, korrekt erkannt
        print(f"False Positives (FP): {fp}")  # Kein Track, aber fälschlich als Track erkannt
        print(f"False Negatives (FN): {fn}")  # Track vorhanden, aber nicht erkannt
        print(f"True Positives  (TP): {tp}")  # Track korrekt erkannt
        print("=================================")

        # Zusätzliche Metriken berechnen
        accuracy = (tp + tn) / (tn + fp + fn + tp)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # Kappa-Score berechnen
        kappa = cohen_kappa_score(ref_data, pred_data)
        
        # Zusätzliche Metriken berechnen
        accuracy = (tp + tn) / (tn + fp + fn + tp)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        kappa = cohen_kappa_score(ref_data, pred_data)

        print("\n====== METRIKEN ======")
        print(f"Accuracy  : {accuracy:.4f}")
        print(f"Precision : {precision:.4f}")
        print(f"Recall    : {recall:.4f}")
        print(f"F1-Score  : {f1_score:.4f}")
        print(f"Cohen's Kappa : {kappa:.4f}")
        print("======================")
        
        # Metriken speichern
        metrics_list.append({
            'Gebietsname': paths['area'],
            'AoI': aoi_name,
            'Zeitraum': period,
            'Accuracy': accuracy,
            'Precision': precision,
            'Recall': recall,
            'F1-Score': f1_score,
            "Cohen's Kappa": kappa
        })

    # Metriken in ein DataFrame umwandeln
    metrics_df = pd.DataFrame(metrics_list)
    
    if os.path.exists(output_file):
        # Wenn die Datei existiert, lade sie und hänge die neuen Daten an
        existing_df = pd.read_csv(output_file)
        combined_df = pd.concat([existing_df, metrics_df], ignore_index=True)
        combined_df.to_csv(output_file, index=False)
        print(f"\nMetriken wurden erfolgreich an die bestehende CSV-Datei angehangt: {output_file}")
    else:
        # Wenn die Datei nicht existiert, speichere die Daten als neue CSV-Datei
        metrics_df.to_csv(output_file, index=False)
        print(f"\nMetriken wurden erfolgreich in die neue CSV-Datei gespeichert: {output_file}")
