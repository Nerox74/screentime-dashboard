"""
KPI-Modul für das Bildschirmzeit-Dashboard.

Berechnet und visualisiert vier Hauptkennzahlen:
- Gesamtzeit der Bildschirmnutzung
- Durchschnittliche tägliche Nutzung
- Gesundheitsindex (0-100, basierend auf Richtwert)
- Top-App nach Nutzungsdauer

Alle KPIs werden als HTML-Boxen mit farbcodierten Vergleichswerten
(Vortag, Gesamtschnitt) dargestellt.
"""

import logging
import pandas as pd
import streamlit as st

# Richtwert für gesunde tägliche Bildschirmzeit in Minuten.
# Dient als Referenz für die Berechnung des Gesundheitsindex.
# Standard: 180 Minuten (3 Stunden) - bei Bedarf anpassbar.

HEALTHY_LIMIT_MINUTES = 180

logger = logging.getLogger(__name__)


def _fmt(minutes: float) -> str:
    """
    Formatiert eine Minutenangabe in lesbare Zeitangabe.

    Args:
        minutes: Anzahl Minuten als Zahl (Float oder Int).

    Returns:
        String im Format "Xh Ym" bei >= 60 Minuten,
        sonst "X min".

    Beispiele:
        >>> _fmt(45)      -> "45 min"
        >>> _fmt(125)     -> "2h 5m"
        >>> _fmt(60)      -> "1h 0m"
    """
    m = int(minutes)
    if m >= 60:
        return f"{m // 60}h {m % 60}m"
    return f"{m} min"


def _delta_html(pct: float | None) -> str:
    """
    Erzeugt HTML-Snippet für die Anzeige einer prozentualen Veränderung.

    Negative oder null Werte werden grün mit Pfeil nach unten dargestellt
    (positive Entwicklung = weniger Bildschirmzeit), positive Werte rot
    mit Pfeil nach oben.

    Args:
        pct: Prozentuale Änderung. None, wenn kein Vergleichswert vorhanden.

    Returns:
        HTML-String mit gefärbtem Pfeil und Prozentwert,
        oder neutralem Hinweis bei None.
    """
    if pct is None:
        return '<div class="delta-neutral">— kein Vergleich</div>'
    arrow = "↓" if pct <= 0 else "↑"
    css_class = "delta-green" if pct <= 0 else "delta-red"
    return f'<div class="{css_class}">{arrow} {abs(pct):.0f}% vs. Vortag</div>'


def _calc_yesterday_delta(
    df_filtered: pd.DataFrame, df_full_context: pd.DataFrame
) -> float | None:
    """
    Berechnet die prozentuale Änderung der Bildschirmzeit gegenüber dem Vortag.

    Verschiebt den Zeitraum des gefilterten DataFrames um einen Tag in die
    Vergangenheit und vergleicht die Summen. Funktioniert auch für mehrtägige
    Auswahlen (Vergleich Zeitraum vs. Vortag-Zeitraum).

    Args:
        df_filtered: Aktuell ausgewählter Zeitraum mit Spalten 'date', 'User',
                     'total_minutes'.
        df_full_context: Gesamter Datensatz für Vortagsvergleich.

    Returns:
        Prozentuale Veränderung als Float (negativ = Rückgang) oder None,
        wenn keine Daten oder kein Vortageswert verfügbar sind.
    """
    if df_filtered.empty or df_full_context.empty:
        return None
    try:
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
    except(KeyError, ValueError) as exc:
        logger.warning("Vortags-Delta konnte nicht berechnet werden: %s", exc)
        return None


def _calc_avg_delta(
    df_filtered: pd.DataFrame, df_full_context: pd.DataFrame
) -> float | None:
    """
    Berechnet die Abweichung des Tagesdurchschnitts vom Gesamtdurchschnitt.

    Vergleicht den durchschnittlichen Tageswert im gefilterten Zeitraum
    mit dem Durchschnitt über den gesamten Datensatz.

    Args:
        df_filtered: Gefilterter Zeitraum mit Spalten 'date', 'total_minutes'.
        df_full_context: Gesamtdatensatz als Vergleichsbasis.

    Returns:
        Prozentuale Abweichung als Float oder None bei fehlenden Daten.
    """
    if df_filtered.empty or df_full_context.empty:
        return None
    try:
        current_avg = df_filtered.groupby("date")["total_minutes"].sum().mean()
        overall_avg = df_full_context.groupby("date")["total_minutes"].sum().mean()
        if overall_avg == 0:
            return None
        return ((current_avg - overall_avg) / overall_avg) * 100
    except(KeyError, ValueError) as exc:
        logger.warning("Durchschnitts-Delta konnte nicht berechnet werden: %s", exc)
        return None


def _calc_health_index(
    today_minutes: float,
    df_full_context: pd.DataFrame,
    selected_date,
    limit: int = HEALTHY_LIMIT_MINUTES,
) -> tuple[int, str, str]:
    """
    Berechnet einen Gesundheitsindex von 0-100 basierend auf Bildschirmzeit.

    Der Index gewichtet zwei Faktoren:
    - 60% aktueller Tag (today_minutes vs. Richtwert)
    - 40% 7-Tage-Durchschnitt vor dem ausgewählten Datum

    Werte über dem 3-fachen Richtwert werden gekappt, um Ausreißer zu
    begrenzen. Ein Index von 100 bedeutet "sehr gut" (weit unter Richtwert),
    0 bedeutet "sehr schlecht" (massiv darüber).

    Args:
        today_minutes: Gesamtminuten des ausgewählten Tages.
        df_full_context: Gesamtdatensatz für den 7-Tage-Verlauf.
        selected_date: Aktuell ausgewähltes Datum (pd.Timestamp-kompatibel).
        limit: Richtwert in Minuten (Standard: HEALTHY_LIMIT_MINUTES).

    Returns:
        Tuple aus:
        - index (int): Score 0-100
        - label (str): "Gut", "Mäßig" oder "Schlecht"
        - css (str): CSS-Klassenname für die Einfärbung
    """

    ratio_today = today_minutes / limit if limit > 0 else 0
    score_today = min(ratio_today, 3.0) / 3.0

    score_7d = 0.0
    if not df_full_context.empty and selected_date is not None:
        try:
            sel = pd.Timestamp(selected_date)
            week_start = sel - pd.Timedelta(days=7)
            week_end = sel - pd.Timedelta(days=1)
            df_week = df_full_context[
                (df_full_context["date"] >= week_start)
                & (df_full_context["date"] <= week_end)
            ]
            if not df_week.empty:
                avg_7d = df_week.groupby("date")["total_minutes"].sum().mean()
                score_7d = min(avg_7d / limit, 3.0) / 3.0 if limit > 0 else 0
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("7-Tage-Score konnte nicht berechnet werden: %s", exc)
            score_7d = 0.0

                # Umkehrung: 100 - Belastung
    # Wenn score_today & score_7d = 0 sind (keine Nutzung), ergibt das 100 (Perfekt)
    index = round(100 - ((score_today * 0.6 + score_7d * 0.4) * 100))

    # Schwellenwerte umgekehrt:
    if index >= 67:
        label, css = "Gut", "delta-green"
    elif index >= 34:
        label, css = "Mäßig", "delta-orange"
    else:
        label, css = "Schlecht", "delta-red"  # Label angepasst von "Hoch" zu "Schlecht"

    return index, label, css


def _health_index_html(
    index: int,
    label: str,
    css: str,
    today_minutes: float,
    limit: int = HEALTHY_LIMIT_MINUTES,
) -> str:
    """
    Erzeugt HTML mit Fortschrittsbalken und Beschriftung für den Gesundheitsindex.

    Zeigt einen farblich passenden Balken (grün/orange/rot), dessen Breite
    dem Index entspricht, sowie eine Textzeile mit Status und Vergleich
    zum Richtwert.

    Args:
        index: Gesundheitsindex 0-100.
        label: Text-Label ("Gut" / "Mäßig" / "Schlecht").
        css: CSS-Klasse für die Farbgebung.
        today_minutes: Tatsächliche Minuten des Tages für Differenzanzeige.
        limit: Richtwert in Minuten.

    Returns:
        HTML-String mit Fortschrittsbalken und Statustext, oder
        Platzhalter bei fehlenden Daten.
    """

    if today_minutes <= 0:
        return '<div class="delta-neutral">— keine Daten</div>'

    # Die Farben bleiben an das 'css' Label gebunden, das wir oben korrekt zuweisen
    bar_colors = {
        "delta-green": "#00d488",
        "delta-orange": "#f0a500",
        "delta-red": "#ff4b4b",
    }
    bar_color = bar_colors.get(css, "#888")

    over = today_minutes - limit
    if over > 0:
        sub = f"+{_fmt(over)} über Richtwert ({_fmt(limit)})"
    else:
        sub = f"{_fmt(today_minutes)} von {_fmt(limit)} Richtwert"

    return (
        f'<div style="margin-top:6px;">'
        f'<div style="background:#333;border-radius:4px;height:6px;overflow:hidden;">'
        f'<div style="width:{index}%;height:100%;background:{bar_color};border-radius:4px;"></div>'
        f"</div>"
        f'<div class="{css}" style="margin-top:4px;">{label} ({index}/100) &mdash; {sub}</div>'
        f"</div>"
    )


def show_kpis(df_filtered, df_long, is_team, df_full_context, selected_date=None):
    """
    Rendert die vier KPI-Boxen im Streamlit-Dashboard.

    Stellt Gesamtzeit, Tagesdurchschnitt, Gesundheitsindex und Top-App
    in einer 4-spaltigen Anordnung dar. Alle Boxen sind dunkel gestaltet
    und enthalten farbcodierte Vergleichswerte.

    Args:
        df_filtered: DataFrame des aktuell gefilterten Zeitraums mit
                     Spalten 'date', 'User', 'total_minutes'.
        df_long: Long-Format DataFrame mit App-Nutzung
                 (Spalten 'App', 'Minutes') für die Top-App-Analyse.
        is_team: Bool, ob es sich um eine Team-Ansicht handelt
                 (aktuell nicht aktiv genutzt, für künftige Erweiterungen).
        df_full_context: Gesamter Datensatz als Vergleichsbasis für
                         Vortags- und Durchschnittsdeltas.
        selected_date: Optional, ausgewähltes Datum für die
                       7-Tage-Berechnung im Gesundheitsindex.

    Side Effects:
        Schreibt CSS und vier KPI-Boxen direkt in den Streamlit-Container.
    """
    st.markdown(
        """
        <style>
        .kpi-box {
            background-color: #1e1e1e;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #333;
            text-align: center;
            min-height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .kpi-title { color: #888; font-size: 0.8rem; text-transform: uppercase; }
        .kpi-main { color: white; font-size: 1.8rem; font-weight: bold; margin: 5px 0; }
        .delta-green  { color: #00d488; font-size: 0.85rem; }
        .delta-orange { color: #f0a500; font-size: 0.85rem; }
        .delta-red    { color: #ff4b4b; font-size: 0.85rem; }
        .delta-neutral{ color: #666;    font-size: 0.85rem; }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # ── Berechnungen ─────────────────────────────────────────────
    try:
        total_m = df_filtered.groupby(["date", "User"])["total_minutes"].first().sum()
        avg = (
            df_filtered.groupby("date")["total_minutes"].sum().mean()
            if not df_filtered.empty
            else 0
        )
    except (KeyError, ValueError) as exc:
        logger.error("KPI-Aggregation fehlgeschlagen: %s", exc, exc_info=True)
        st.error("KPIs konnten nicht berechnet werden.")
        return

    yesterday_pct = _calc_yesterday_delta(df_filtered, df_full_context)
    avg_pct = _calc_avg_delta(df_filtered, df_full_context)

    # Gesundheitsindex
    index, label, css = _calc_health_index(total_m, df_full_context, selected_date)

    # Top App
    if not df_long.empty:
        try:
            top_series = df_long.groupby("App")["Minutes"].sum()
            top_app = top_series.idxmax()
            top_app_min = int(top_series.max())
            top_app_sub = f"{_fmt(top_app_min)} erfasst"
            top_css = "delta-green"

        except (KeyError, ValueError) as exc:
            logger.warning("Top-App-Berechnung fehlgeschlagen: %s", exc)
            top_app, top_app_sub, top_css = "—", "Fehler bei Berechnung", "delta-neutral"
    else:
        top_app, top_app_sub, top_css = "—", "keine Daten", "delta-neutral"

    # ── Darstellung ──────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""<div class="kpi-box"><div class="kpi-title">Gesamtzeit</div><div class="kpi-main">{_fmt(total_m)}</div>{_delta_html(yesterday_pct)}</div>""",
            unsafe_allow_html=True,
        )

    with c2:
        avg_delta_html = (
            f'<div class="{"delta-green" if avg_pct <= 0 else "delta-red"}">{"↓" if avg_pct <= 0 else "↑"} {abs(avg_pct):.0f}% vs. Gesamtschnitt</div>'
            if avg_pct is not None
            else '<div class="delta-neutral">— kein Vergleich</div>'
        )
        st.markdown(
            f"""<div class="kpi-box"><div class="kpi-title">Ø Täglich</div><div class="kpi-main">{_fmt(avg)}</div>{avg_delta_html}</div>""",
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""<div class="kpi-box"><div class="kpi-title">Gesundheitsindex</div><div class="kpi-main">{index} / 100</div>{_health_index_html(index, label, css, total_m)}</div>""",
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""<div class="kpi-box"><div class="kpi-title">Top App</div><div class="kpi-main" style="font-size:1.2rem;">{top_app}</div><div class="{top_css}">{top_app_sub}</div></div>""",
            unsafe_allow_html=True,
        )
