import streamlit as st


def show_header():
    # CSS für das runde Icon und das kompakte Dropdown
    st.markdown("""
        <style>
        .profile-container {
            display: flex;
            align-items: center;
            gap: 10px; /* Abstand zwischen Icon und Dropdown */
        }
        .profile-icon {
            width: 40px;
            height: 40px;
            background-color: #e0e0e0;
            border-radius: 50%; /* Macht es kreisrund */
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            border: 1px solid #ccc;
        }
        /* Verkleinert den Abstand über dem Dropdown in Streamlit */
        div[data-testid="stSelectbox"] > div {
            margin-top: -5px;
        }
        </style>
    """, unsafe_allow_html=True)

    col_t, col_time, col_u = st.columns([2, 1.5, 1.2])

    with col_t:
        st.title("📱 Dashboard App")

    with col_time:
        time_filter = st.radio("Zeitraum", ["Tag", "Woche", "Monat"], horizontal=True, label_visibility="collapsed")

    with col_u:
        # Wir nutzen wieder Spalten, aber mit sehr engem Abstand
        icon_col, select_col = st.columns([0.3, 2])

        with icon_col:
            # Das runde Icon
            st.markdown('<div class="profile-icon">👤</div>', unsafe_allow_html=True)

        with select_col:
            user_options = ["Michi", "Henning", "Nils", "Alle zusammen"]
            selected_user = st.selectbox(
                "",
                options=user_options,
                index=3,
                label_visibility="collapsed"
            )

    return time_filter, selected_user