import logging

import pandas as pd
import streamlit as st

# Durch aufruf in Entry.py weiß Python schon, wie geloggt werden soll
logger = logging.getLogger(__name__)


def _fmt(minutes: float) -> str:
    m = int(minutes)
    if m >= 60:
        return f"{m // 60}h {m % 60}m"
    return f"{m} min"


def _delta_html(pct: float | None) -> str:
    """Gibt einen farbigen Delta-String zurück, oder einen neutralen Fallback."""
    if pct is None:
        return '<div class="delta-neutral">— kein Vergleich</div>'
    arrow = "↓" if pct <= 0 else "↑"
    css_class = "delta-green" if pct <= 0 else "delta-red"
    return f'<div class="{css_class}">{arrow} {abs(pct):.0f}% vs. Vortag</div>'


def _calc_yesterday_delta(
    df_filtered: pd.DataFrame, df_full_context: pd.DataFrame
) -> float | None:
    """
    Vergleicht die Gesamtzeit im gefilterten Zeitraum mit dem gleichen Zeitraum
    einen Tag früher (verschoben um 1 Tag).
    Gibt die prozentuale Änderung zurück, oder None wenn kein Vortag vorhanden.
    """
    if df_filtered.empty or df_full_context.empty:
        return None

    min_date = df_filtered["date"].min()
    max_date = df_filtered["date"].max()

    prev_min = min_date - pd.Timedelta(days=1)
    prev_max = max_date - pd.Timedelta(days=1)

    prev = df_full_context[
        (df_full_context["date"] >= prev_min) & (df_full_context["date"] <= prev_max)
    ]

    if prev.empty:
        return None

    current_total = df_filtered.groupby(["date", "User"])["total_minutes"].first().sum()
    prev_total = prev.groupby(["date", "User"])["total_minutes"].first().sum()

    if prev_total == 0:
        return None

    return ((current_total - prev_total) / prev_total) * 100


def _calc_avg_delta(
    df_filtered: pd.DataFrame, df_full_context: pd.DataFrame
) -> float | None:
    """
    Vergleicht den Tagesdurchschnitt im gefilterten Zeitraum
    mit dem Gesamtdurchschnitt über alle verfügbaren Daten.
    """
    if df_filtered.empty or df_full_context.empty:
        return None

    current_avg = df_filtered.groupby("date")["total_minutes"].sum().mean()
    overall_avg = df_full_context.groupby("date")["total_minutes"].sum().mean()

    if overall_avg == 0:
        return None

    return ((current_avg - overall_avg) / overall_avg) * 100


def show_kpis(df_filtered, df_long, is_team, df_full_context):
    st.markdown(
        """
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
        .delta-neutral { color: #666; font-size: 0.85rem; }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # ── Berechnungen ──────────────────────────────────────────────
    total_m = df_filtered.groupby(["date", "User"])["total_minutes"].first().sum()
    avg = (
        df_filtered.groupby("date")["total_minutes"].sum().mean()
        if not df_filtered.empty
        else 0
    )

    yesterday_pct = _calc_yesterday_delta(df_filtered, df_full_context)
    avg_pct = _calc_avg_delta(df_filtered, df_full_context)

    # KPI 3: Anzahl aktiver User im gefilterten Zeitraum
    active_users = df_filtered["User"].nunique() if not df_filtered.empty else 0
    total_users = df_full_context["User"].nunique() if not df_full_context.empty else 0
    members_sub = (
        f"{active_users} von {total_users} aktiv"
        if total_users > 0
        else "— keine Daten"
    )
    members_css = "delta-green" if active_users == total_users else "delta-red"

    # KPI 4: Top App + wie viel Minuten
    if not df_long.empty:
        top_series = df_long.groupby("App")["Minutes"].sum()
        top_app = top_series.idxmax()
        top_app_min = int(top_series.max())
        top_app_sub = f"{_fmt(top_app_min)} erfasst"
        top_css = "delta-green"
    else:
        top_app, top_app_sub, top_css = "—", "keine Daten", "delta-neutral"

    # ── Darstellung ───────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""<div class="kpi-box">
            <div class="kpi-title">Gesamtzeit</div>
            <div class="kpi-main">{_fmt(total_m)}</div>
            {_delta_html(yesterday_pct)}
        </div>""",
            unsafe_allow_html=True,
        )

    with c2:
        avg_delta_html = (
            f'<div class="{"delta-green" if avg_pct <= 0 else "delta-red"}">{"↓" if avg_pct <= 0 else "↑"} {abs(avg_pct):.0f}% vs. Gesamtschnitt</div>'
            if avg_pct is not None
            else '<div class="delta-neutral">— kein Vergleich</div>'
        )
        st.markdown(
            f"""<div class="kpi-box">
            <div class="kpi-title">Ø Täglich</div>
            <div class="kpi-main">{_fmt(avg)}</div>
            {avg_delta_html}
        </div>""",
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""<div class="kpi-box">
            <div class="kpi-title">Mitglieder</div>
            <div class="kpi-main">{active_users}</div>
            <div class="{members_css}">{members_sub}</div>
        </div>""",
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""<div class="kpi-box">
            <div class="kpi-title">Top App</div>
            <div class="kpi-main" style="font-size: 1.2rem;">{top_app}</div>
            <div class="{top_css}">{top_app_sub}</div>
        </div>""",
            unsafe_allow_html=True,
        )
