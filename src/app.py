import streamlit as st
import pandas as pd
from datetime import timedelta
from data_loader import load_user_data
from components.header import show_header
from components.kpis import show_kpis
from components.charts import show_main_charts

# Design
st.set_page_config(page_title="Screen Time Dashboard", layout="wide")

# 1. Header & Auswahl
time_filter, selected_option = show_header()
st.markdown("---")

# 2. Daten laden
if "Alle zusammen" in selected_option:
    all_l, all_o = [], []
    for name in ["Michi", "Henning", "Nils"]:
        l, o = load_user_data(name)
        if not l.empty:
            all_l.append(l); all_o.append(o)
    df_long = pd.concat(all_l, ignore_index=True)
    df_orig = pd.concat(all_o, ignore_index=True)
    is_team = True
else:
    u_name = selected_option.split(" ")[1]
    df_long, df_orig = load_user_data(u_name)
    is_team = False

# 3. Zeitfilter anwenden
if not df_orig.empty:
    latest_date = df_orig['date'].max()
    if time_filter == "Tag":
        df_orig = df_orig[df_orig['date'] == latest_date]
        df_long = df_long[df_long['date'] == latest_date]
    elif time_filter == "Woche":
        df_orig = df_orig[df_orig['date'] > (latest_date - timedelta(days=7))]
        df_long = df_long[df_long['date'] > (latest_date - timedelta(days=7))]

# 4. Komponenten anzeigen
if not df_orig.empty:
    show_kpis(df_orig, df_long, is_team)
    st.write("")
    show_main_charts(df_orig, df_long, is_team)
else:
    st.info("Warte auf Daten...")