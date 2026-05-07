import calendar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ──────────────────────────────────────────────────────────────
# Zentrale Farb-Map für Apps (wird in Balken UND Torte genutzt)
# ──────────────────────────────────────────────────────────────
def get_app_color_map(df_long):
    """
    Erstellt ein konsistentes Farb-Mapping für alle Apps,
    damit Balken- und Kreisdiagramm dieselben Farben verwenden.
    """
    if df_long.empty:
        return {}
    apps_sorted = (
        df_long.groupby("App")["Minutes"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    palette = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel
    return {app: palette[i % len(palette)] for i, app in enumerate(apps_sorted)}


def style_plotly_layout(fig):
    """Einheitlicher Look für alle Plotly Charts – verhindert Überlaufen."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#eee",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, title="", fixedrange=True),
        yaxis=dict(showgrid=False, title="", fixedrange=True),
        dragmode=False,
        autosize=True,
    )


def show_main_charts(
    df_orig, df_long, is_team, picked_date=None, selected_user="Michell"
):
    st.markdown(
        """
        <style>
        .chart-card {
            background-color: #1e1e1e;
            border-radius: 15px;
            padding: 20px;
            border: 1px solid #333;
            margin-bottom: 20px;
            overflow: hidden;
            box-sizing: border-box;
        }
        .chart-title {
            color: #888;
            font-size: 0.85rem;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 16px;
            letter-spacing: 1px;
        }

        /* ── Kalender-Heatmap ── */
        .cal-wrapper { width: 100%; overflow: hidden; }
        .cal-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 3px;
            width: 100%;
            box-sizing: border-box;
        }
        .cal-header {
            text-align: center;
            color: #666;
            font-size: 0.6rem;
            font-weight: bold;
            padding: 2px 0;
        }
        .cal-day {
            aspect-ratio: 1;
            border-radius: 4px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-size: 0.6rem;
            font-weight: bold;
            color: white;
            border: 1px solid rgba(255,255,255,0.08);
            cursor: default;
            transition: transform 0.1s;
            min-width: 0;
        }
        .cal-day:hover { transform: scale(1.12); }
        .cal-day-num { font-size: 0.62rem; line-height: 1; }
        .cal-day-icon { font-size: 0.5rem; line-height: 1; margin-top: 1px; }
        .cal-empty { aspect-ratio: 1; }
        .cal-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 6px 10px;
            justify-content: center;
            margin-top: 8px;
            font-size: 0.65rem;
            color: #888;
        }
        .cal-legend-dot {
            width: 9px;
            height: 9px;
            border-radius: 2px;
            display: inline-block;
            margin-right: 3px;
            vertical-align: middle;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    if is_team:
        show_team_view(df_orig)
        return

    from components.fazit import show_fazit

    # Gemeinsame Farb-Map für beide Charts
    color_map = get_app_color_map(df_long)

    # ── Reihe 1: Top Apps + Torte ──
    col1, col2 = st.columns([1.6, 1])

    with col1:
        st.markdown(
            '<div class="chart-card"><div class="chart-title">📊 Top Apps heute</div>',
            unsafe_allow_html=True,
        )
        if not df_long.empty:
            top_apps = (
                df_long.groupby("App")["Minutes"]
                .sum()
                .sort_values(ascending=True)
                .tail(5)
            )
            icon_map = {
                "Instagram": "📸",
                "WhatsApp": "💬",
                "TikTok": "🎵",
                "YouTube": "📺",
                "Safari": "🌐",
                "Netflix": "🎬",
            }
            labels = [f"{icon_map.get(app, '📱')} {app}" for app in top_apps.index]
            bar_colors = [color_map.get(app, "#00d488") for app in top_apps.index]

            fig = px.bar(
                y=labels, x=top_apps.values, orientation="h", text=top_apps.values
            )
            fig.update_traces(
                marker_color=bar_colors,
                textposition="outside",
                cliponaxis=False,
                texttemplate="%{x} min",
            )
            style_plotly_layout(fig)
            fig.update_layout(
                margin=dict(l=10, r=60, t=10, b=10),
                uniformtext_minsize=8,
                uniformtext_mode="hide",
            )
            st.plotly_chart(
                fig, use_container_width=True, config={"displayModeBar": False}
            )
        else:
            st.markdown(
                '<p style="color:#555; text-align:center; margin-top:40px;">Keine Daten</p>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            '<div class="chart-card"><div class="chart-title">🥧 Verteilung</div>',
            unsafe_allow_html=True,
        )
        if not df_long.empty:
            fig_pie = px.pie(
                df_long,
                values="Minutes",
                names="App",
                hole=0.5,
                color="App",
                color_discrete_map=color_map,
            )
            fig_pie.update_traces(
                textinfo="none", marker=dict(line=dict(color="#1e1e1e", width=2))
            )
            style_plotly_layout(fig_pie)
            fig_pie.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.45,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11),
                ),
                margin=dict(l=10, r=10, t=10, b=60),
            )
            st.plotly_chart(
                fig_pie, use_container_width=True, config={"displayModeBar": False}
            )
        else:
            st.markdown(
                '<p style="color:#555; text-align:center; margin-top:40px;">Keine Daten</p>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Reihe 2: Kalender-Heatmap + Fazit ──
    col3, col4 = st.columns([1, 2])

    with col3:
        st.markdown(
            '<div class="chart-card"><div class="chart-title">📅 Monats-Heatmap</div>',
            unsafe_allow_html=True,
        )
        show_calendar_heatmap(df_orig, picked_date)
        st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        show_fazit(df_orig, df_long, is_team=False, selected_user=selected_user)


def show_calendar_heatmap(df_orig, picked_date=None):
    """
    Zeigt eine Kalender-Heatmap für den im Header gewählten Monat.
      Grün:  < 3h   (< 180 min)
      Orange: 3h–5h (180–300 min)
      Rot:   > 5h   (> 300 min)
    """
    LIMIT_GREEN = 180  # 3h
    LIMIT_ORANGE = 300  # 5h

    today = pd.Timestamp.now().date()

    if picked_date is not None:
        ref = pd.Timestamp(picked_date).date()
    else:
        ref = today
    year, month = ref.year, ref.month

    actual_data: dict = {}
    if not df_orig.empty:
        monthly = df_orig[
            (df_orig["date"].dt.year == year) & (df_orig["date"].dt.month == month)
        ]
        if not monthly.empty:
            actual_data = (
                monthly.groupby(monthly["date"].dt.date)["total_minutes"]
                .first()
                .to_dict()
            )

    month_name = calendar.month_name[month]
    first_weekday, num_days = calendar.monthrange(year, month)
    day_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    html = f'<div class="cal-wrapper">'
    html += f'<p style="text-align:center; color:#aaa; font-size:0.9rem; margin-bottom:10px;">{month_name} {year}</p>'
    html += '<div class="cal-grid">'

    for dn in day_names:
        html += f'<div class="cal-header">{dn}</div>'

    for _ in range(first_weekday):
        html += '<div class="cal-empty"></div>'

    for day in range(1, num_days + 1):
        d = pd.Timestamp(year, month, day).date()
        val = actual_data.get(d, None)

        if d > today:
            bg = "#2a2a2a"
            icon = ""
            border = "1px solid #3a3a3a"
            tooltip = f"{d}: –"
        elif val is None:
            bg = "#333"
            icon = "·"
            border = "1px solid #444"
            tooltip = f"{d}: kein Eintrag"
        elif val < LIMIT_GREEN:
            bg = "#00d488"
            icon = "✔"
            border = "1px solid rgba(0,212,136,0.4)"
            h = int(val // 60)
            m = int(val % 60)
            tooltip = f"{d}: {h}h {m}m ✔"
        elif val <= LIMIT_ORANGE:
            bg = "#f0a500"
            icon = "⚠"
            border = "1px solid rgba(240,165,0,0.4)"
            h = int(val // 60)
            m = int(val % 60)
            tooltip = f"{d}: {h}h {m}m ⚠"
        else:
            bg = "#ff4b4b"
            icon = "✘"
            border = "1px solid rgba(255,75,75,0.4)"
            h = int(val // 60)
            m = int(val % 60)
            tooltip = f"{d}: {h}h {m}m ✘"

        today_style = (
            "outline: 2px solid #fff; outline-offset: -2px;" if d == today else ""
        )

        html += (
            f'<div class="cal-day" style="background-color:{bg}; border:{border}; {today_style}" title="{tooltip}">'
            f'<span class="cal-day-num">{day}</span>'
            f'<span class="cal-day-icon">{icon}</span>'
            f"</div>"
        )

    html += "</div>"  # cal-grid

    html += """
    <div class="cal-legend">
        <span><span class="cal-legend-dot" style="background:#00d488;"></span> Unter 3h</span>
        <span><span class="cal-legend-dot" style="background:#f0a500;"></span> 3h – 5h</span>
        <span><span class="cal-legend-dot" style="background:#ff4b4b;"></span> Über 5h</span>
        <span><span class="cal-legend-dot" style="background:#333;"></span> Kein Eintrag</span>
        <span><span class="cal-legend-dot" style="background:#2a2a2a; border:1px solid #444;"></span> Zukunft</span>
    </div>
    """
    html += "</div>"  # cal-wrapper

    st.markdown(html, unsafe_allow_html=True)


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
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)
