import logging

import pandas as pd
import streamlit as st

# Durch aufruf in Entry.py weiß Python schon, wie geloggt werden soll
logger = logging.getLogger(__name__)


def show_header(available_dates):
    # CSS für das kompakte Design
    st.markdown(
        """
        <style>
        .profile-wrapper { display: flex; align-items: center; justify-content: flex-end; gap: 5px; }
        .round-avatar { width: 35px; height: 35px; background-color: #f0f2f6; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 1px solid #ddd; }
        div[data-testid="stSelectbox"] { width: 130px !important; }
        </style>
    """,
        unsafe_allow_html=True,
    )

    col_t, col_time, col_date, col_u = st.columns([2, 1, 1, 1])

    with col_t:
        st.title("📱 Dashboard")

    with col_time:
        # Hier wird 'time_filter' definiert!
        time_filter = st.radio(
            "Zeitraum",
            ["Tag", "Woche", "Monat"],
            horizontal=True,
            label_visibility="collapsed",
        )

    with col_date:
        if not available_dates.empty:
            min_d = available_dates.min()
            max_d = available_dates.max()
            selected_date = st.date_input(
                "Datum",
                value=max_d,
                min_value=min_d,
                max_value=max_d,
                label_visibility="collapsed",
            )
        else:
            selected_date = pd.Timestamp.now()

    with col_u:
        st.markdown('<div class="profile-wrapper">', unsafe_allow_html=True)
        c1, c2 = st.columns([0.4, 1.6])
        with c1:
            st.markdown('<div class="round-avatar">👤</div>', unsafe_allow_html=True)
        with c2:
            user_options = ["Michell", "Henning", "Nils", "Alle"]
            selected_user = st.selectbox(
                "",
                options=user_options,
                index=0,  # Standardmäßig Michell
                label_visibility="collapsed",
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # Jetzt sind alle drei Variablen (time_filter, selected_user, selected_date) bekannt
    return time_filter, selected_user, pd.to_datetime(selected_date)
