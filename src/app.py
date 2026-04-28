import logging
from datetime import timedelta

import pandas as pd
import streamlit as st
from components.charts import show_main_charts
from components.header import show_header
from components.kpis import show_kpis

# Importe der eigenen Module
from data_loader import load_user_data

st.set_page_config(layout="wide", page_title="Screentime Dashboard")

# Durch aufruf in Entry.py weiß Python schon, wie geloggt werden soll
logger = logging.getLogger(__name__)


# --- SCHRITT 1: DATEN FÜR DEN KALENDER VORAB LADEN ---
# Wir nutzen Michell als Referenz, um verfügbare Tage im Kalender anzuzeigen
_, df_temp = load_user_data("Michell")
available_dates = df_temp["date"] if not df_temp.empty else pd.Series()

# --- SCHRITT 2: HEADER AUFRUFEN ---
# Erst hier werden die Variablen 'time_filter', 'selected_option' und 'picked_date' definiert
time_filter, selected_option, picked_date = show_header(available_dates)
st.markdown("---")

# --- SCHRITT 3: DATEN BASIEREND AUF DER AUSWAHL LADEN ---
# Jetzt ist 'selected_option' bekannt und wir können sie prüfen
if selected_option == "Alle":
    all_l, all_o = [], []
    # Wichtig: Die Namen müssen exakt wie im file_mapping in data_loader.py sein
    for name in ["Michell", "Henning", "Nils"]:
        l, o = load_user_data(name)
        if not l.empty:
            all_l.append(l)
            all_o.append(o)

    if all_l:
        df_long = pd.concat(all_l, ignore_index=True)
        df_orig = pd.concat(all_o, ignore_index=True)
    else:
        df_long, df_orig = pd.DataFrame(), pd.DataFrame()
    is_team = True
else:
    # Einzelansicht laden
    df_long, df_orig = load_user_data(selected_option)
    is_team = False

# Kopie für den KPI-Vergleich (Vortag), bevor wir den Zeitfilter anwenden
df_full_context = df_orig.copy() if not df_orig.empty else pd.DataFrame()

# --- SCHRITT 4: ZEITFILTER ANWENDEN ---
if not df_orig.empty and picked_date:
    picked_date = pd.to_datetime(picked_date)
    if time_filter == "Tag":
        df_orig = df_orig[df_orig["date"] == picked_date]
        df_long = df_long[df_long["date"] == picked_date]
    elif time_filter == "Woche":
        start_date = picked_date - timedelta(days=7)
        df_orig = df_orig[
            (df_orig["date"] > start_date) & (df_orig["date"] <= picked_date)
        ]
        df_long = df_long[
            (df_long["date"] > start_date) & (df_long["date"] <= picked_date)
        ]
    elif time_filter == "Monat":
        start_date = picked_date - timedelta(days=30)
        df_orig = df_orig[
            (df_orig["date"] > start_date) & (df_orig["date"] <= picked_date)
        ]
        df_long = df_long[
            (df_long["date"] > start_date) & (df_long["date"] <= picked_date)
        ]

# --- SCHRITT 5: ANZEIGE ---
if not df_orig.empty:
    # Übergabe der Daten und des Kontexts für die Deltas
    show_kpis(df_orig, df_long, is_team, df_full_context)
    st.write("")
    show_main_charts(df_orig, df_long, is_team)
else:
    st.info(f"Keine Daten für {selected_option} im gewählten Zeitraum gefunden.")
