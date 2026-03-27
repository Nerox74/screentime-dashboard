import streamlit as st


def show_kpis(df_orig, df_long, is_team):
    available_dates = sorted(df_orig['date'].unique(), reverse=True)
    delta_val = None
    if len(available_dates) >= 2:
        today_sum = df_orig[df_orig['date'] == available_dates[0]]['total_minutes'].sum()
        yesterday_sum = df_orig[df_orig['date'] == available_dates[1]]['total_minutes'].sum()
        diff = int(today_sum - yesterday_sum)
        delta_val = f"{diff} min" if diff < 0 else f"+{diff} min"

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