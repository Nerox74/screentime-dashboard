import streamlit as st


def show_kpis(df_filtered, df_long, is_team, df_full_context):
    st.markdown("""
        <style>
        .kpi-box {
            background-color: #1e1e1e;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #333;
            text-align: center;
        }
        .kpi-title { color: #888; font-size: 0.8rem; text-transform: uppercase; }
        .kpi-main { color: white; font-size: 1.8rem; font-weight: bold; margin: 5px 0; }
        .delta-green { color: #00d488; font-size: 0.85rem; }
        .delta-red { color: #ff4b4b; font-size: 0.85rem; }
        </style>
    """, unsafe_allow_html=True)

    # Berechnung für Gesamtzeit
    total_m = df_filtered.groupby(['date', 'User'])['total_minutes'].first().sum()

    # Delta-Berechnung (Beispielhaft für 12% weniger)
    # Hier könnte man deine -pi + winkel Formel für andere Berechnungen nutzen,
    # aber für die Zeit nutzen wir die Prozentänderung.

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""<div class="kpi-box">
            <div class="kpi-title">Gesamtzeit</div>
            <div class="kpi-main">{int(total_m // 60)}h {int(total_m % 60)}m</div>
            <div class="delta-green">↓ 12% vs. gestern</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        avg = round(df_filtered.groupby('date')['total_minutes'].sum().mean(), 0)
        st.markdown(f"""<div class="kpi-box">
            <div class="kpi-title">Ø Täglich</div>
            <div class="kpi-main">{int(avg)} min</div>
            <div class="delta-red">↑ 5% vs. Schnitt</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="kpi-box">
            <div class="kpi-title">Mitglieder</div>
            <div class="kpi-main">3</div>
            <div class="delta-green">Alle online</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        top_app = df_long.groupby('App')['Minutes'].sum().idxmax() if not df_long.empty else "-"
        st.markdown(f"""<div class="kpi-box">
            <div class="kpi-title">Top App</div>
            <div class="kpi-main" style="font-size: 1.2rem;">{top_app}</div>
            <div class="delta-green">Meiste Zeit</div>
        </div>""", unsafe_allow_html=True)