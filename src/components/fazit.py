import pandas as pd
import streamlit as st

# Wochentage auf Deutsch (Index 0 = Montag)
WEEKDAYS_DE = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]


def _fmt_minutes(minutes: float) -> str:
    """Formatiert Minuten als 'Xh Ym' oder 'Y min'."""
    if pd.isna(minutes) or minutes is None:
        return "—"
    m = int(round(minutes))
    if m >= 60:
        h = m // 60
        rest = m % 60
        if rest == 0:
            return f"{h}h"
        return f"{h}h {rest}m"
    return f"{m} min"


def _fmt_date(d) -> str:
    """Formatiert ein Datum im deutschen Format (z. B. '30.03.2026')."""
    if d is None or pd.isna(d):
        return "—"
    return pd.Timestamp(d).strftime("%d.%m.%Y")


def _fmt_weekday(d) -> str:
    """Gibt den deutschen Wochentag zurück."""
    if d is None or pd.isna(d):
        return ""
    return WEEKDAYS_DE[pd.Timestamp(d).weekday()]


def show_fazit(df_orig, df_long, is_team, selected_user="Michell"):
    """
    Zeigt ein Fazit-Feld unten rechts im Dashboard.

    - Einzelansicht: Persönliche Zusammenfassung (bester/schlechtester Tag,
      Gesamtzeit, Top-App, Wochentag-Muster, Streak unter Richtwert).
    - Team-Ansicht: Vergleich zwischen den Nutzern (wer war am wenigsten /
      am meisten am Handy, wer hat den besten Schnitt, etc.).
    """

    # ── Styling für die Fazit-Karte ─────────────────────────────
    st.markdown(
        """
        <style>
        .fazit-card {
            background-color: #1e1e1e;
            border-radius: 15px;
            padding: 22px 24px;
            border: 1px solid #333;
            margin-bottom: 20px;
        }
        .fazit-title {
            color: #888;
            font-size: 0.85rem;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 14px;
            letter-spacing: 1px;
        }
        .fazit-item {
            color: #ddd;
            font-size: 0.92rem;
            padding: 8px 0;
            border-bottom: 1px solid #2a2a2a;
            line-height: 1.45;
        }
        .fazit-item:last-child {
            border-bottom: none;
        }
        .fazit-icon {
            display: inline-block;
            width: 22px;
            margin-right: 6px;
        }
        .fazit-highlight {
            color: #00d488;
            font-weight: bold;
        }
        .fazit-warn {
            color: #ff4b4b;
            font-weight: bold;
        }
        .fazit-neutral {
            color: #f0a500;
            font-weight: bold;
        }
        .fazit-empty {
            color: #666;
            text-align: center;
            padding: 20px 0;
            font-style: italic;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="fazit-card">', unsafe_allow_html=True)
    st.markdown('<div class="fazit-title">📋 Dein Fazit</div>', unsafe_allow_html=True)

    if df_orig is None or df_orig.empty:
        st.markdown(
            '<div class="fazit-empty">Keine Daten für ein Fazit verfügbar.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if is_team:
        _render_team_fazit(df_orig, df_long)
    else:
        _render_user_fazit(df_orig, df_long, selected_user)

    st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# EINZELANSICHT: Fazit für eine Person
# ──────────────────────────────────────────────────────────────
def _render_user_fazit(df_orig, df_long, user_name):
    items = []

    # Pro-Tag-Aggregation (falls mehrere Einträge pro Tag existieren, nimm den ersten)
    daily = df_orig.groupby("date")["total_minutes"].first().sort_index()

    if daily.empty:
        items.append(
            ("ℹ️", "Für den gewählten Zeitraum liegen keine Daten vor.", "neutral")
        )
        _render_items(items)
        return

    # ── 1) Gesamtzeit im Zeitraum ───────────────────────────────
    total = daily.sum()
    days_count = len(daily)
    items.append(
        (
            "⏱️",
            f"Im gewählten Zeitraum hast du insgesamt "
            f"<span class='fazit-highlight'>{_fmt_minutes(total)}</span> "
            f"am Handy verbracht (über {days_count} "
            f"{'Tag' if days_count == 1 else 'Tage'}).",
            None,
        )
    )

    # ── 2) Bester Tag (wenigste Zeit) ───────────────────────────
    best_date = daily.idxmin()
    best_val = daily.min()
    items.append(
        (
            "🏆",
            f"Dein bester Tag war <span class='fazit-highlight'>"
            f"{_fmt_weekday(best_date)}, der {_fmt_date(best_date)}</span> "
            f"mit nur {_fmt_minutes(best_val)}.",
            None,
        )
    )

    # ── 3) Schlechtester Tag (meiste Zeit) ──────────────────────
    if len(daily) > 1:
        worst_date = daily.idxmax()
        worst_val = daily.max()
        items.append(
            (
                "⚠️",
                f"Am meisten Zeit hast du am <span class='fazit-warn'>"
                f"{_fmt_weekday(worst_date)}, dem {_fmt_date(worst_date)}</span> "
                f"verbracht – ganze {_fmt_minutes(worst_val)}.",
                None,
            )
        )

    # ── 4) Durchschnitt pro Tag ─────────────────────────────────
    avg = daily.mean()
    items.append(
        (
            "📊",
            f"Im Schnitt warst du <span class='fazit-neutral'>"
            f"{_fmt_minutes(avg)}</span> pro Tag am Handy.",
            None,
        )
    )

    # ── 5) Wochentags-Muster (welcher Wochentag im Schnitt am meisten?) ──
    if len(daily) >= 3:
        weekday_avg = daily.groupby(daily.index.weekday).mean()
        if not weekday_avg.empty:
            top_wd_idx = int(weekday_avg.idxmax())
            top_wd_val = weekday_avg.max()
            items.append(
                (
                    "📅",
                    f"Dein nutzungsstärkster Wochentag ist im Schnitt der "
                    f"<span class='fazit-warn'>{WEEKDAYS_DE[top_wd_idx]}</span> "
                    f"mit Ø {_fmt_minutes(top_wd_val)}.",
                    None,
                )
            )

    # ── 6) Top-App im Zeitraum ──────────────────────────────────
    if df_long is not None and not df_long.empty:
        app_totals = (
            df_long.groupby("App")["Minutes"].sum().sort_values(ascending=False)
        )
        if not app_totals.empty:
            top_app = app_totals.index[0]
            top_app_min = app_totals.iloc[0]
            share = (
                (top_app_min / app_totals.sum()) * 100 if app_totals.sum() > 0 else 0
            )
            items.append(
                (
                    "📱",
                    f"Deine meistgenutzte App war <span class='fazit-highlight'>"
                    f"{top_app}</span> mit {_fmt_minutes(top_app_min)} "
                    f"({share:.0f}% deiner erfassten App-Zeit).",
                    None,
                )
            )

    # ── 7) Tage unter dem Richtwert (3h = 180 min) ──────────────
    LIMIT = 180
    under_limit = (daily < LIMIT).sum()
    if days_count > 0:
        pct = (under_limit / days_count) * 100
        if pct >= 70:
            tone = "highlight"
            msg = (
                f"Stark! An <span class='fazit-highlight'>{under_limit} von {days_count} Tagen "
                f"({pct:.0f}%)</span> bist du unter dem Richtwert von 3 h geblieben."
            )
        elif pct >= 40:
            tone = "neutral"
            msg = (
                f"An <span class='fazit-neutral'>{under_limit} von {days_count} Tagen "
                f"({pct:.0f}%)</span> warst du unter dem Richtwert von 3 h – da geht noch was."
            )
        else:
            tone = "warn"
            msg = (
                f"Nur an <span class='fazit-warn'>{under_limit} von {days_count} Tagen "
                f"({pct:.0f}%)</span> bist du unter dem Richtwert von 3 h geblieben."
            )
        items.append(("🎯", msg, tone))

    _render_items(items)


# ──────────────────────────────────────────────────────────────
# TEAM-ANSICHT: Fazit für 'Alle'
# ──────────────────────────────────────────────────────────────
def _render_team_fazit(df_orig, df_long):
    items = []

    if "User" not in df_orig.columns:
        items.append(
            ("ℹ️", "Keine Nutzerinformation in den Daten gefunden.", "neutral")
        )
        _render_items(items)
        return

    # Pro Nutzer und Tag aggregieren
    per_user_day = (
        df_orig.groupby(["User", "date"])["total_minutes"].first().reset_index()
    )

    if per_user_day.empty:
        items.append(("ℹ️", "Keine Daten im Zeitraum vorhanden.", "neutral"))
        _render_items(items)
        return

    # ── 1) Wer hatte den absolut niedrigsten Tag? ───────────────
    min_row = per_user_day.loc[per_user_day["total_minutes"].idxmin()]
    items.append(
        (
            "🏆",
            f"<span class='fazit-highlight'>{min_row['User']}</span> hatte am "
            f"{_fmt_weekday(min_row['date'])}, dem {_fmt_date(min_row['date'])} "
            f"die wenigste Bildschirmzeit – nur "
            f"<span class='fazit-highlight'>{_fmt_minutes(min_row['total_minutes'])}</span>.",
            None,
        )
    )

    # ── 2) Wer hatte den absolut höchsten Tag? ──────────────────
    max_row = per_user_day.loc[per_user_day["total_minutes"].idxmax()]
    items.append(
        (
            "⚠️",
            f"Den Spitzenwert hält <span class='fazit-warn'>{max_row['User']}</span> "
            f"mit {_fmt_minutes(max_row['total_minutes'])} am "
            f"{_fmt_weekday(max_row['date'])}, dem {_fmt_date(max_row['date'])}.",
            None,
        )
    )

    # ── 3) Wer hat den besten Schnitt? ──────────────────────────
    user_avg = per_user_day.groupby("User")["total_minutes"].mean().sort_values()
    if len(user_avg) >= 1:
        best_user = user_avg.index[0]
        best_avg = user_avg.iloc[0]
        items.append(
            (
                "📊",
                f"Den niedrigsten Tagesschnitt hat <span class='fazit-highlight'>"
                f"{best_user}</span> mit Ø {_fmt_minutes(best_avg)} pro Tag.",
                None,
            )
        )

    # ── 4) Wer hat den höchsten Schnitt? ────────────────────────
    if len(user_avg) >= 2:
        worst_user = user_avg.index[-1]
        worst_avg = user_avg.iloc[-1]
        diff = worst_avg - user_avg.iloc[0]
        items.append(
            (
                "📈",
                f"<span class='fazit-warn'>{worst_user}</span> liegt im Schnitt vorn mit "
                f"Ø {_fmt_minutes(worst_avg)} pro Tag – das sind "
                f"{_fmt_minutes(diff)} mehr als {user_avg.index[0]}.",
                None,
            )
        )

    # ── 5) Gesamtzeit aller Nutzer im Zeitraum ──────────────────
    total_all = per_user_day["total_minutes"].sum()
    user_total = (
        per_user_day.groupby("User")["total_minutes"].sum().sort_values(ascending=False)
    )
    if not user_total.empty:
        top_user = user_total.index[0]
        top_user_total = user_total.iloc[0]
        items.append(
            (
                "⏱️",
                f"Zusammen kommt das Team auf <span class='fazit-neutral'>"
                f"{_fmt_minutes(total_all)}</span> Bildschirmzeit – davon entfallen "
                f"{_fmt_minutes(top_user_total)} auf {top_user}.",
                None,
            )
        )

    # ── 6) Top-App im Team ──────────────────────────────────────
    if df_long is not None and not df_long.empty and "User" in df_long.columns:
        # Top-App pro Nutzer
        app_per_user = df_long.groupby(["User", "App"])["Minutes"].sum().reset_index()
        if not app_per_user.empty:
            # Globale Top-App
            global_top = (
                df_long.groupby("App")["Minutes"].sum().sort_values(ascending=False)
            )
            if not global_top.empty:
                items.append(
                    (
                        "📱",
                        f"Die im Team meistgenutzte App ist "
                        f"<span class='fazit-highlight'>{global_top.index[0]}</span> "
                        f"mit insgesamt {_fmt_minutes(global_top.iloc[0])}.",
                        None,
                    )
                )

    # ── 7) Tage unter dem Richtwert pro Person ──────────────────
    LIMIT = 180
    under_per_user = (
        per_user_day[per_user_day["total_minutes"] < LIMIT].groupby("User").size()
    )
    days_per_user = per_user_day.groupby("User").size()
    if not days_per_user.empty:
        # Anteil unter Limit pro User
        ratio = (under_per_user / days_per_user).fillna(0).sort_values(ascending=False)
        if not ratio.empty:
            disciplined = ratio.index[0]
            disciplined_pct = ratio.iloc[0] * 100
            items.append(
                (
                    "🎯",
                    f"Am diszipliniertesten ist <span class='fazit-highlight'>"
                    f"{disciplined}</span> – an {disciplined_pct:.0f}% der Tage unter dem "
                    f"Richtwert von 3 h.",
                    None,
                )
            )

    _render_items(items)


# ──────────────────────────────────────────────────────────────
# Hilfsfunktion: Items rendern
# ──────────────────────────────────────────────────────────────
def _render_items(items):
    for icon, text, _tone in items:
        st.markdown(
            f'<div class="fazit-item">'
            f'<span class="fazit-icon">{icon}</span>{text}'
            f"</div>",
            unsafe_allow_html=True,
        )
