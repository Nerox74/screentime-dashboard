import logging

import pandas as pd
import plotly.express as px
import streamlit as st

# Durch aufruf in Entry.py weiß Python schon, wie geloggt werden soll
logger = logging.getLogger(__name__)


def show_main_charts(df_orig, df_long, is_team):
    # CSS für absolute Stabilität und das dunkle Karten-Design
    st.markdown(
        """
        <style>
        .chart-card {
            background-color: #1e1e1e;
            border-radius: 15px;
            padding: 20px;
            border: 1px solid #333;
            margin-bottom: 20px;
            min-height: 400px; /* Gleicht die Höhe der Karten an */
        }
        .chart-title {
            color: #888;
            font-size: 0.85rem;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 20px;
            letter-spacing: 1px;
        }
        .heatmap-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            padding: 10px 0;
        }
        .day-box {
            width: 42px;
            height: 42px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            border: 1px solid rgba(255,255,255,0.1);
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    if is_team:
        show_team_view(df_orig)
    else:
        # --- EINZELANSICHT ---
        # Reihe 1: Top Apps (Links) und Torten-Chart (Rechts)
        col1, col2 = st.columns([1.6, 1])

        with col1:
            st.markdown(
                '<div class="chart-card"><div class="chart-title">📊 Top Apps heute</div>',
                unsafe_allow_html=True,
            )
            if not df_long.empty:
                # Top 5 Apps berechnen
                top_apps = (
                    df_long.groupby("App")["Minutes"]
                    .sum()
                    .sort_values(ascending=True)
                    .tail(5)
                )

                # Icons fest zuordnen
                icon_map = {
                    "Instagram": "📸",
                    "WhatsApp": "💬",
                    "TikTok": "🎵",
                    "YouTube": "📺",
                    "Safari": "🌐",
                    "Netflix": "🎬",
                }
                labels = [f"{icon_map.get(app, '📱')} {app}" for app in top_apps.index]

                fig = px.bar(
                    y=labels, x=top_apps.values, orientation="h", text=top_apps.values
                )
                fig.update_traces(
                    marker_color="#00d488", textposition="outside", cliponaxis=False
                )
                style_plotly_layout(fig)
                st.plotly_chart(
                    fig, use_container_width=True, config={"displayModeBar": False}
                )
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(
                '<div class="chart-card"><div class="chart-title">🥧 Verteilung</div>',
                unsafe_allow_html=True,
            )
            if not df_long.empty:
                fig_pie = px.pie(df_long, values="Minutes", names="App", hole=0.5)
                fig_pie.update_traces(
                    textinfo="none", marker=dict(line=dict(color="#1e1e1e", width=2))
                )
                style_plotly_layout(fig_pie)
                fig_pie.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.5,
                        xanchor="center",
                        x=0.5,
                    ),
                )
                st.plotly_chart(
                    fig_pie, use_container_width=True, config={"displayModeBar": False}
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # Reihe 2: Die Heatmap-Kästchen (Activity Streak)
        st.markdown(
            '<div class="chart-card" style="min-height: auto;"><div class="chart-title">🔥 Activity Streak & Health Limit</div>',
            unsafe_allow_html=True,
        )
        show_streak_heatmap(df_orig)
        st.markdown("</div>", unsafe_allow_html=True)


def show_streak_heatmap(df_orig):
    LIMIT = 180  # 3 Stunden Limit
    # Die letzten 21 Tage anzeigen
    dates = pd.date_range(end=pd.Timestamp.now().date(), periods=21).date
    actual_data = df_orig.groupby("date")["total_minutes"].first().to_dict()

    heatmap_html = '<div class="heatmap-container">'
    for d in dates:
        val = actual_data.get(pd.Timestamp(d), None)
        color = "#333"  # Grau wenn keine Daten
        icon = ""

        if val is not None:
            if val <= LIMIT:
                color = "#00d488"  # Grün (Gesund)
                icon = "✔"
            else:
                color = "#ff4b4b"  # Rot (Über Limit)
                icon = "✘"

        heatmap_html += f'<div class="day-box" style="background-color: {color};" title="{d}: {val if val else 0} min">{icon}</div>'

    st.markdown(heatmap_html + "</div>", unsafe_allow_html=True)
    st.markdown(
        f'<p style="text-align: center; color: #666; font-size: 0.8rem; margin-top: 10px;">Limit: {LIMIT} Min (3h) pro Tag</p>',
        unsafe_allow_html=True,
    )


def style_plotly_layout(fig):
    """Einheitlicher Look für alle Plotly Charts"""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#eee",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        xaxis_title="",
        yaxis_title="",
    )


# test
def show_team_view(df_orig):
    """Ansicht wenn 'Alle' ausgewählt ist"""
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-title">👥 Team Vergleich (Schnitt)</div>',
        unsafe_allow_html=True,
    )
    if not df_orig.empty:
        team_avg = df_orig.groupby("User")["total_minutes"].mean().reset_index()
        fig = px.bar(
            team_avg,
            x="User",
            y="total_minutes",
            color="User",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        style_plotly_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
