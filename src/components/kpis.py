import streamlit as st
import pandas as pd


def show_kpis(df_filtered, df_long, is_team, df_full_context):
    # 1. VERGLEICHSWERT FINDEN (Delta-Logik)
    # Wir schauen in den kompletten Daten (df_full_context), was vor dem aktuellen Zeitraum war
    available_dates = sorted(df_filtered['date'].unique(), reverse=True)

    delta_time_pct = None
    delta_color_time = "inverse"

    if not df_filtered.empty and not df_full_context.empty:
        # Aktueller Wert
        current_sum = df_filtered.groupby(['date', 'User'])['total_minutes'].first().sum()

        # Den Tag direkt vor dem ältesten Datum im Filter finden
        oldest_date_in_filter = available_dates[-1]
        previous_data = df_full_context[df_full_context['date'] < oldest_date_in_filter]

        if not previous_data.empty:
            last_available_date = previous_data['date'].max()
            previous_sum = previous_data[previous_data['date'] == last_available_date].groupby(['date', 'User'])[
                'total_minutes'].first().sum()

            if previous_sum > 0:
                diff_pct = ((current_sum - previous_sum) / previous_sum) * 100
                if diff_pct == 0:
                    delta_time_pct = "0.0%"
                    delta_color_time = "off"
                else:
                    delta_time_pct = f"{diff_pct:+.1f}%"
                    delta_color_time = "inverse"
        else:
            # Wenn es absolut keinen Vortag gibt
            delta_time_pct = "0.0%"
            delta_color_time = "off"

    # 2. HAUPTWERTE BERECHNEN
    total_m = df_filtered.groupby(['date', 'User'])['total_minutes'].first().sum()
    avg_m = round(df_filtered.groupby('date')['total_minutes'].sum().mean(), 0)

    # 3. ANZEIGE
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.metric(
            label="Gesamtzeit",
            value=f"{int(total_m // 60)}h {int(total_m % 60)}m",
            delta=delta_time_pct,
            delta_color=delta_color_time
        )

    with k2:
        st.metric(
            label="Ø pro Tag",
            value=f"{int(avg_m)} min",
            delta=f"Basis: {len(available_dates)} Tag(e)",
            delta_color="normal"
        )

    with k3:
        member_count = len(df_filtered['User'].unique())
        st.metric(
            label="Mitglieder" if is_team else "Status",
            value=member_count,
            delta="Aktiv",
            delta_color="normal"
        )

    with k4:
        if not df_long.empty:
            top_app = df_long.groupby('App')['Minutes'].sum().idxmax()
            top_app_time = df_long.groupby('App')['Minutes'].sum().max()
            st.metric(label="Top App", value=top_app, delta=f"{int(top_app_time)} min")
        else:
            st.metric(label="Top App", value="-")