import streamlit as st


def show_kpis(df_orig, df_long, is_team):
    # 1. DATEN VORBEREITEN
    available_dates = sorted(df_orig['date'].unique(), reverse=True)

    # Platzhalter für die Deltas
    delta_time = None
    delta_avg = None
    delta_members = None

    if len(available_dates) >= 2:
        today = available_dates[0]
        yesterday = available_dates[1]

        # Berechnung Gesamtzeit Delta
        sum_today = df_orig[df_orig['date'] == today]['total_minutes'].sum()
        sum_yesterday = df_orig[df_orig['date'] == yesterday]['total_minutes'].sum()
        diff_time = int(sum_today - sum_yesterday)
        delta_time = f"{diff_time} min" if diff_time < 0 else f"+{diff_time} min"

        # Berechnung Durchschnitt pro Tag Delta (Beispiel: heute vs gestern)
        # Hier vergleichen wir den heutigen Wert mit dem Gesamtdurchschnitt
        avg_total = df_orig['total_minutes'].mean()
        diff_avg = int(sum_today - avg_total)
        delta_avg = f"{diff_avg} min" if diff_avg < 0 else f"+{diff_avg} min"

    # 2. WERTE BERECHNEN
    total_m = df_orig.groupby(['date', 'User'])['total_minutes'].first().sum()
    avg_m = round(df_orig.groupby('date')['total_minutes'].sum().mean(), 0)

    # 3. ANZEIGE IN SPALTEN
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.metric(
            label="Gesamtzeit",
            value=f"{int(total_m // 60)}h {int(total_m % 60)}m",
            delta=delta_time,
            delta_color="inverse"  # Rot wenn mehr Zeit, Grün wenn weniger
        )

    with k2:
        st.metric(
            label="Ø pro Tag",
            value=f"{int(avg_m)} min",
            delta=delta_avg,
            delta_color="inverse"
        )

    with k3:
        # Bei Mitgliedern zeigen wir z.B. an, ob jemand neues dazu kam
        member_count = 3 if is_team else 1
        st.metric(
            label="Mitglieder" if is_team else "Status",
            value=member_count,
            delta="Stabil" if is_team else "Aktiv",
            delta_color="normal"
        )

    with k4:
        top_app = df_long.groupby('App')['Minutes'].sum().idxmax()
        # Bei der Top App gibt es meist kein numerisches Delta,
        # wir lassen es clean oder schreiben die Minuten dazu
        top_app_mins = int(df_long[df_long['App'] == top_app]['Minutes'].sum())
        st.metric(
            label="Top App",
            value=top_app,
            delta=f"{top_app_mins} min gesamt"
        )