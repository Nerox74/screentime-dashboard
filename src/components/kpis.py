import streamlit as st
import pandas as pd

# Richtwert gesunde Bildschirmzeit pro Tag in Minuten (anpassbar)
HEALTHY_LIMIT_MINUTES = 120


def _fmt(minutes: float) -> str:
    m = int(minutes)
    if m >= 60:
        return f"{m // 60}h {m % 60}m"
    return f"{m} min"


def _delta_html(pct: float | None) -> str:
    if pct is None:
        return '<div class="delta-neutral">— kein Vergleich</div>'
    arrow = "↓" if pct <= 0 else "↑"
    css_class = "delta-green" if pct <= 0 else "delta-red"
    return f'<div class="{css_class}">{arrow} {abs(pct):.0f}% vs. Vortag</div>'


def _calc_yesterday_delta(df_filtered: pd.DataFrame, df_full_context: pd.DataFrame) -> float | None:
    if df_filtered.empty or df_full_context.empty:
        return None
    min_date = df_filtered['date'].min()
    max_date = df_filtered['date'].max()
    prev_min = min_date - pd.Timedelta(days=1)
    prev_max = max_date - pd.Timedelta(days=1)
    prev = df_full_context[
        (df_full_context['date'] >= prev_min) &
        (df_full_context['date'] <= prev_max)
    ]
    if prev.empty:
        return None
    current_total = df_filtered.groupby(['date', 'User'])['total_minutes'].first().sum()
    prev_total = prev.groupby(['date', 'User'])['total_minutes'].first().sum()
    if prev_total == 0:
        return None
    return ((current_total - prev_total) / prev_total) * 100


def _calc_avg_delta(df_filtered: pd.DataFrame, df_full_context: pd.DataFrame) -> float | None:
    if df_filtered.empty or df_full_context.empty:
        return None
    current_avg = df_filtered.groupby('date')['total_minutes'].sum().mean()
    overall_avg = df_full_context.groupby('date')['total_minutes'].sum().mean()
    if overall_avg == 0:
        return None
    return ((current_avg - overall_avg) / overall_avg) * 100


def _calc_health_index(
    today_minutes: float,
    df_full_context: pd.DataFrame,
    selected_date,
    limit: int = HEALTHY_LIMIT_MINUTES,
) -> tuple[int, str, str]:
    """
    Gesundheitsindex 0–100.
      0   = sehr gut  (weit unter Richtwert, auch historisch niedrig)
      100 = sehr schlecht (massiv über Richtwert, auch historisch hoch)

    Berechnung:
      score_today = min(today / limit, 3.0) / 3.0          → Gewicht 60 %
      score_7d    = min(avg_7d / limit, 3.0) / 3.0         → Gewicht 40 %
      index       = round((score_today * 0.6 + score_7d * 0.4) * 100)

    Der 7-Tage-Schnitt dämpft den Index:
      Wer 6 Tage zu viel hatte, bleibt auch bei einem guten Tag hoch.
      Wer 6 Tage wenig hatte, profitiert davon trotz einem schlechten Tag.
    """
    ratio_today = today_minutes / limit if limit > 0 else 0
    score_today = min(ratio_today, 3.0) / 3.0

    score_7d = 0.0
    if not df_full_context.empty and selected_date is not None:
        try:
            sel = pd.Timestamp(selected_date)
            week_start = sel - pd.Timedelta(days=7)
            week_end   = sel - pd.Timedelta(days=1)
            df_week = df_full_context[
                (df_full_context['date'] >= week_start) &
                (df_full_context['date'] <= week_end)
            ]
            if not df_week.empty:
                avg_7d = df_week.groupby('date')['total_minutes'].sum().mean()
                score_7d = min(avg_7d / limit, 3.0) / 3.0 if limit > 0 else 0
        except Exception:
            pass

    index = round((score_today * 0.6 + score_7d * 0.4) * 100)

    if index <= 33:
        label, css = "Gut", "delta-green"
    elif index <= 66:
        label, css = "Mäßig", "delta-orange"
    else:
        label, css = "Hoch", "delta-red"

    return index, label, css


def _health_index_html(index: int, label: str, css: str, today_minutes: float, limit: int = HEALTHY_LIMIT_MINUTES) -> str:
    if today_minutes <= 0:
        return '<div class="delta-neutral">— keine Daten</div>'

    bar_colors = {"delta-green": "#00d488", "delta-orange": "#f0a500", "delta-red": "#ff4b4b"}
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
        f'</div>'
        f'<div class="{css}" style="margin-top:4px;">{label} &mdash; {sub}</div>'
        f'</div>'
    )


def show_kpis(df_filtered, df_long, is_team, df_full_context, selected_date=None):
    st.markdown("""
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
    """, unsafe_allow_html=True)

    # ── Berechnungen ─────────────────────────────────────────────
    total_m = df_filtered.groupby(['date', 'User'])['total_minutes'].first().sum()
    avg = df_filtered.groupby('date')['total_minutes'].sum().mean() if not df_filtered.empty else 0

    yesterday_pct = _calc_yesterday_delta(df_filtered, df_full_context)
    avg_pct = _calc_avg_delta(df_filtered, df_full_context)

    # Gesundheitsindex
    index, label, css = _calc_health_index(total_m, df_full_context, selected_date)

    # Top App
    if not df_long.empty:
        top_series = df_long.groupby('App')['Minutes'].sum()
        top_app = top_series.idxmax()
        top_app_min = int(top_series.max())
        top_app_sub = f"{_fmt(top_app_min)} erfasst"
        top_css = "delta-green"
    else:
        top_app, top_app_sub, top_css = "—", "keine Daten", "delta-neutral"

    # ── Darstellung ──────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""<div class="kpi-box"><div class="kpi-title">Gesamtzeit</div><div class="kpi-main">{_fmt(total_m)}</div>{_delta_html(yesterday_pct)}</div>""", unsafe_allow_html=True)

    with c2:
        avg_delta_html = (
            f'<div class="{"delta-green" if avg_pct <= 0 else "delta-red"}">{"↓" if avg_pct <= 0 else "↑"} {abs(avg_pct):.0f}% vs. Gesamtschnitt</div>'
            if avg_pct is not None else '<div class="delta-neutral">— kein Vergleich</div>'
        )
        st.markdown(f"""<div class="kpi-box"><div class="kpi-title">Ø Täglich</div><div class="kpi-main">{_fmt(avg)}</div>{avg_delta_html}</div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="kpi-box"><div class="kpi-title">Gesundheitsindex</div><div class="kpi-main">{index} / 100</div>{_health_index_html(index, label, css, total_m)}</div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""<div class="kpi-box"><div class="kpi-title">Top App</div><div class="kpi-main" style="font-size:1.2rem;">{top_app}</div><div class="{top_css}">{top_app_sub}</div></div>""", unsafe_allow_html=True)