import logging
import pandas as pd
import os
import streamlit as st

logger = logging.getLogger(__name__)

def load_user_data(user_name):
    """
    Lädt die Bildschirmzeit-Daten eines spezifischen Benutzers aus einer CSV-Datei.

    Args:
        user_name (str): Name des Benutzers (Michell, Henning oder Nils).

    Returns:
        tuple: (pd.DataFrame mit App-Details, pd.DataFrame mit Rohdaten)
    """
    # Mapping der Benutzernamen auf die entsprechenden Dateinamen im 'data' Ordner
    file_mapping = {
        "Michell": "michell.csv",
        "Henning": "henning.csv",
        "Nils": "nils.csv"
    }
    logger.info("Lade Daten für User '%s'", user_name)

    # Dynamische Pfadermittlung: Navigiert vom aktuellen Skript-Ordner zum Projekt-Root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    file_path = os.path.join(project_root, "data", file_mapping[user_name])

    # Überprüfung, ob die Datei existiert, um Laufzeitfehler zu vermeiden
    if not os.path.exists(file_path):
        logger.warning("CSV-Datei nicht gefunden: %s", file_path)
        return pd.DataFrame(), pd.DataFrame()

    # Laden der CSV-Datei mit automatischer Trennzeichen-Erkennung

    data = pd.read_csv(file_path, sep=None, engine='python')

    # Bereinigung der Spaltennamen (Entfernt Leerzeichen) und Vereinheitlichung
    data.columns = data.columns.str.strip()
    if 'person' in data.columns:
        data = data.rename(columns={'person': 'User'})

    # Konvertierung des Datumsspalte in echte Python-Datetime-Objekte
    data['date'] = pd.to_datetime(data['date'])

    # Transformation: Umwandlung vom Breit-Format (app1, app2...) in das Lang-Format (Tidying)
    rows = []
    for _, r in data.iterrows():
        for i in range(1, 6):
            app_n = r.get(f'app{i}_name')
            app_m = r.get(f'app{i}_minutes')

            # Nur hinzufügen, wenn ein App-Name hinterlegt ist (Validierung)
            if pd.notna(app_n):
                rows.append({
                    'date': r['date'],
                    'User': user_name,
                    'total_minutes': r['total_minutes'],
                    'App': app_n,
                    'Minutes': app_m
                })

    # Rückgabe des transformierten Detail-DataFrames und der bereinigten Rohdaten
    return pd.DataFrame(rows), data