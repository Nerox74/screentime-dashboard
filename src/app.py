import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. SETUP & DESIGN
st.set_page_config(page_title="Screen Time Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    div[data-testid="stMetricValue"] { font-size: 32px; color: #1f77b4; }
    .stPlotlyChart { border-radius: 10px; background-color: white; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)


# 2. DATEN-FUNKTION
def load_user_data(user_name):
    file_mapping = {"Michi": "michell.csv", "Henning": "henning.csv", "Nils": "nils.csv"}
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    file_path = os.path.join(project_root, "data", file_mapping[user_name])

    if os.path.exists(file_path):
        data = pd.read_csv(file_path, sep=None, engine='python')
        data.columns = data.columns.str.strip()

        # Falls Spalte 'person' heißt, zu 'User' machen
        if 'person' in data.columns:
            data = data.rename(columns={'person': 'User'})

        data['date'] = pd.to_datetime(data['date'])

        # Umwandlung für Apps (Langformat)
        rows = []
        for _, r in data.iterrows():
            for i in range(1, 4):
                app_n = r.get(f'app{i}_name')
                app_m = r.get(f'app{i}_minutes')
                if pd.notna(app_n):
                    rows.append({
                        'date': r['date'], 'User': user_name,
                        'total_minutes': r['total_minutes'],
                        'App': app_n, 'Minutes': app_m
                    })
        return pd.DataFrame(rows), data
    return pd.DataFrame(), pd.DataFrame()


# 3. HEADER
col_t, col_s, col_u = st.columns([2, 1, 1])
with col_t:
    st.title("📱 Dashboard App")
with col_u:
    user_options = ["👤 Michi", "👤 Henning", "👤 Nils", "👥 Alle zusammen"]
    selected_option = st.selectbox("", options=user_options, index=3, label_visibility="collapsed")

st.markdown("---")

# 4. DATEN LADEN & VARIABLEN DEFINIEREN
if "Alle zusammen" in selected_option:
    all_l, all_o = [], []
    for name in ["Michi", "Henning", "Nils"]:
        l, o = load_user_data(name)
        if not l.empty:
            all_l.append(l)
            all_o.append(o)
    df_long = pd.concat(all_l, ignore_index=True) if all_l else pd.DataFrame()
    df_orig = pd.concat(all_o, ignore_index=True) if all_o else pd.DataFrame()
    is_team = True
else:
    u_name = selected_option.split(" ")[1]
    df_long, df_orig = load_user_data(u_name)
    is_team = False

# 5. DASHBOARD ANZEIGEN (nur wenn Daten da sind)
if not df_orig.empty:
    # --- DELTA LOGIK ---
    available_dates = sorted(df_orig['date'].unique(), reverse=True)
    delta_val = None

    if len(available_dates) >= 2:
        today = available_dates[0]
        yesterday = available_dates[1]

        # Summe über alle User an diesen Tagen
        sum_today = df_orig[df_orig['date'] == today]['total_minutes'].sum()
        sum_yesterday = df_orig[df_orig['date'] == yesterday]['total_minutes'].sum()

        diff = int(sum_today - sum_yesterday)
        delta_val = f"{diff} min" if diff < 0 else f"+{diff} min"

    # KPI REIHE
    k1, k2, k3, k4 = st.columns(4)

    total_m = df_orig.groupby(['date', 'User'])['total_minutes'].first().sum()
    avg_m = round(df_orig.groupby('date')['total_minutes'].sum().mean(), 0)

    with k1:
        st.metric("Gesamtzeit", f"{int(total_m // 60)}h {int(total_m % 60)}m", delta=delta_val, delta_color="inverse")
    with k2:
        st.metric("Ø pro Tag", f"{int(avg_m)} min")
    with k3:
        st.metric("Mitglieder" if is_team else "Status", "3" if is_team else "Aktiv")
    with k4:
        top_app = df_long.groupby('App')['Minutes'].sum().idxmax()
        st.metric("Top App", top_app)

    st.write("")

    # 6. CHARTS
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.subheader("Täglicher Verlauf")
        c_data = df_orig.groupby(['date', 'User'])['total_minutes'].first().reset_index()
        fig1 = px.line(c_data, x='date', y='total_minutes', color='User' if is_team else None, markers=True)
        st.plotly_chart(fig1, use_container_width=True)
    with r1c2:
        st.subheader("App Verteilung")
        fig2 = px.pie(df_long, values='Minutes', names='App', hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.subheader("Vergleich: Apps")
        fig3 = px.bar(df_long, x='App', y='Minutes', color='User', barmode='group')
        st.plotly_chart(fig3, use_container_width=True)
    with r2c2:
        st.subheader("Ranking")
        rank = df_orig.groupby('User')['total_minutes'].sum().sort_values(ascending=False).reset_index()
        st.dataframe(rank, use_container_width=True, hide_index=True)
else:
    st.info("Suche CSV-Dateien im Ordner 'data'...")