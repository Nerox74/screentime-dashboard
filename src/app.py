import streamlit as st
import pandas as pd
from datetime import timedelta
from data_loader import load_user_data
from components.header import show_header
from components.kpis import show_kpis
from components.charts import show_main_charts

st.set_page_config(layout="wide")

# --- SCHRITT 1: DATEN VORAB LADEN (Wichtig für den Kalender) ---
# Wir laden kurz die Daten von Michi, um zu wissen, welche Tage verfügbar sind
_, df_temp = load_user_data("Michi")
available_dates = df_temp['date'] if not df_temp.empty else pd.Series()

# --- SCHRITT 2: HEADER AUFRUFEN ---
# Jetzt übergeben wir die 'available_dates', damit die Fehlermeldung verschwindet
time_filter, selected_option, picked_date = show_header(available_dates)
st.markdown("---")

# --- SCHRITT 3: DATEN LADEN ---
if selected_option == "Alle":
    all_l, all_o = [], []
    for name in ["Michi", "Henning", "Nils"]:
        l, o = load_user_data(name)
        if not l.empty:
            all_l.append(l); all_o.append(o)
    df_long = pd.concat(all_l, ignore_index=True) if all_l else pd.DataFrame()
    df_orig = pd.concat(all_o, ignore_index=True) if all_o else pd.DataFrame()
    is_team = True
else:
    # WICHTIG: Kein .split(" ")[1] mehr!
    # selected_option ist jetzt direkt "Nils", "Michi" oder "Henning"
    u_name = selected_option
    df_long, df_orig = load_user_data(u_name)
    is_team = False

# --- SCHRITT 4: ZEITFILTER ANWENDEN ---
if not df_orig.empty and picked_date:
    picked_date = pd.to_datetime(picked_date)
    if time_filter == "Tag":
        df_orig = df_orig[df_orig['date'] == picked_date]
        df_long = df_long[df_long['date'] == picked_date]
    elif time_filter == "Woche":
        start_date = picked_date - timedelta(days=7)
        df_orig = df_orig[(df_orig['date'] > start_date) & (df_orig['date'] <= picked_date)]
        df_long = df_long[(df_long['date'] > start_date) & (df_long['date'] <= picked_date)]
    elif time_filter == "Monat":
        start_date = picked_date - timedelta(days=30)
        df_orig = df_orig[(df_orig['date'] > start_date) & (df_orig['date'] <= picked_date)]
        df_long = df_long[(df_long['date'] > start_date) & (df_long['date'] <= picked_date)]

# --- SCHRITT 5: ANZEIGE ---
if not df_orig.empty:
    show_kpis(df_orig, df_long, is_team)
    st.write("")
    show_main_charts(df_orig, df_long, is_team)
else:
    st.info("Keine Daten für diesen Zeitraum/Nutzer gefunden.")