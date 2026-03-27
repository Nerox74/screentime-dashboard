import streamlit as st
import plotly.express as px

def show_main_charts(df_orig, df_long, is_team):
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.subheader("Verlauf")
        c_data = df_orig.groupby(['date', 'User'])['total_minutes'].first().reset_index()
        fig1 = px.line(c_data, x='date', y='total_minutes', color='User' if is_team else None, markers=True)
        st.plotly_chart(fig1, use_container_width=True)
    with r1c2:
        st.subheader("App Verteilung")
        fig2 = px.pie(df_long, values='Minutes', names='App', hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)