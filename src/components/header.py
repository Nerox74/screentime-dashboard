import streamlit as st


def show_header():
    # CSS für das kompakte Design
    st.markdown("""
        <style>
        /* Container für Icon + Dropdown */
        .profile-wrapper {
            display: flex;
            align-items: center;
            justify-content: flex-end; /* Rechtsbündig */
            gap: 5px;
        }

        /* Das runde Icon */
        .round-avatar {
            width: 35px;
            height: 35px;
            background-color: #f0f2f6;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            border: 1px solid #ddd;
        }

        /* Macht das Streamlit-Dropdown extrem schmal */
        div[data-testid="stSelectbox"] {
            width: 130px !important; /* Hier stellst du die Breite ein */
        }

        /* Entfernt unnötige Abstände um das Dropdown */
        div[data-testid="stSelectbox"] > div {
            border: none;
            background-color: transparent;
        }
        </style>
    """, unsafe_allow_html=True)

    col_t, col_time, col_u = st.columns([2, 1.5, 1])

    with col_t:
        st.title("📱 Dashboard")

    with col_time:
        time_filter = st.radio("Zeitraum", ["Tag", "Woche", "Monat"], horizontal=True, label_visibility="collapsed")

    with col_u:
        # Alles in ein Div packen für Flexbox-Layout
        st.markdown('<div class="profile-wrapper">', unsafe_allow_html=True)

        # Wir nutzen Unter-Spalten, um Icon und Dropdown nebeneinander zu zwingen
        c1, c2 = st.columns([0.4, 1.6])

        with c1:
            st.markdown('<div class="round-avatar">👤</div>', unsafe_allow_html=True)

        with c2:
            user_options = ["Michi", "Henning", "Nils", "Alle"]
            selected_user = st.selectbox(
                "",
                options=user_options,
                index=3,
                label_visibility="collapsed"
            )

        st.markdown('</div>', unsafe_allow_html=True)

    return time_filter, selected_user