"""
Dieses Modul stellt eine Streamlit-Webanwendung zur Verfügung, mit der Benutzer
ihre tägliche Bildschirmzeit sowie die Nutzungsdauer ihrer Top-5-Apps erfassen können.
Die Daten werden als CSV-Dateien in einem angebundenen GitHub-Repository gespeichert.
"""

import base64
import io
import logging
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from github import Github, GithubException

from logging_setup import setup_logging

from logging_setup import setup_logging

# ── Konfiguration ────────────────────────────────────────────────
# Liste der verfügbaren Personen für das Dropdown-Menü
PERSONS = ["Henning", "Michell", "Nils"]

# Liste bekannter Apps zur Autovervollständigung und Normalisierung
KNOWN_APPS = sorted(
    [
        "Amazon",
        "Apple Music",
        "BeReal",
        "Chrome",
        "Clash of Clans",
        "Discord",
        "Disney+",
        "Duolingo",
        "Facebook",
        "Gmail",
        "Google Maps",
        "HBO Max",
        "Instagram",
        "LinkedIn",
        "Maps",
        "Netflix",
        "Pinterest",
        "Reddit",
        "Safari",
        "Shazam",
        "Signal",
        "Snapchat",
        "Spotify",
        "Telegram",
        "TikTok",
        "Tinder",
        "Twitch",
        "Twitter",
        "WhatsApp",
        "YouTube",
    ]
)

# Definiertes Schema für die CSV-Dateien
CSV_COLUMNS = [
    "date",
    "person",
    "total_minutes",
    "app1_name",
    "app1_minutes",
    "app2_name",
    "app2_minutes",
    "app3_name",
    "app3_minutes",
    "app4_name",
    "app4_minutes",
    "app5_name",
    "app5_minutes",
]

# ── Setup des Loggers ─────────────────────────────────────────────

setup_logging("projekt.log")
logger = logging.getLogger(__name__)
logging.info("Die App wurde gestartet")
# ── GitHub-Verbindung ─────────────────────────────────────────────


def get_repo():
    """
    Stellt eine Verbindung zum GitHub-Repository her, das in den Streamlit-Secrets definiert ist.

    Returns:
        github.Repository.Repository: Das authentifizierte GitHub-Repository-Objekt.
    """
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["GITHUB_REPO"]
    g = Github(token)
    return g.get_repo(repo_name)


def load_csv_from_github(person: str) -> pd.DataFrame:
    """
    Lädt die CSV-Datei mit den Bildschirmzeit-Daten einer bestimmten Person aus GitHub.

    Args:
        person (str): Der Name der Person, deren Daten geladen werden sollen.

    Returns:
        pd.DataFrame: Ein DataFrame mit den historischen Einträgen der Person.
                      Gibt einen leeren DataFrame mit den definierten Spalten zurück,
                      falls die Datei nicht existiert oder ein Fehler auftritt.
    """
    repo = get_repo()
    # Der Dateipfad wird basierend auf dem Namen der Person in Kleinbuchstaben generiert
    path = f"data/{person.lower()}.csv"
    try:
        file = repo.get_contents(path)
        # GitHub liefert den Dateiinhalt base64-kodiert zurück, daher muss er dekodiert werden
        content = base64.b64decode(file.content).decode("utf-8")
        df = pd.read_csv(io.StringIO(content))

        # Datum in ein einheitliches Datetime-Format umwandeln und die Uhrzeit abschneiden (normalize)
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()

        # Alte Spaltennamen (Tippfehler ohne "s") zur Abwärtskompatibilität korrigieren
        df = df.rename(
            columns={
                "app4_minute": "app4_minutes",
                "app5_minute": "app5_minutes",
            }
        )

        # Fehlende App4/App5-Spalten ergänzen (falls es alte Einträge mit nur 3 Apps gibt)
        for col, default in [
            ("app4_name", ""),
            ("app4_minutes", 0),
            ("app5_name", ""),
            ("app5_minutes", 0),
        ]:
            if col not in df.columns:
                df[col] = default

        return df
    except GithubException:
        # Falls die Datei nicht existiert (z.B. erster Aufruf für diese Person),
        # wird ein leerer DataFrame mit der korrekten Struktur zurückgegeben.
        return pd.DataFrame(columns=CSV_COLUMNS)


def save_csv_to_github(person: str, df: pd.DataFrame) -> None:
    """
    Speichert einen DataFrame als CSV-Datei im GitHub-Repository ab.

    Args:
        person (str): Der Name der Person, für die die Daten gespeichert werden.
        df (pd.DataFrame): Der DataFrame mit den aktualisierten Daten.

    Returns:
        None
    """
    repo = get_repo()
    path = f"data/{person.lower()}.csv"

    # Eine Kopie anlegen, um Warnungen beim Verändern der Daten zu vermeiden
    df = df.copy()
    # Das Datum für die CSV in einen einfachen String umwandeln
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    csv_content = df.to_csv(index=False)

    try:
        # Versuchen, die bestehende Datei zu finden und zu aktualisieren
        existing_file = repo.get_contents(path)
        repo.update_file(
            path=path,
            message=f"data: add entry for {person} on {date.today().isoformat()}",
            content=csv_content,
            sha=existing_file.sha,
        )
    except GithubException:
        # Wenn die Datei noch nicht existiert, wird sie neu angelegt
        repo.create_file(
            path=path,
            message=f"data: create {person.lower()}.csv",
            content=csv_content,
        )


# ── Hilfsfunktionen ──────────────────────────────────────────────


def normalize_app_name(name: str) -> str:
    """
    Normalisiert einen eingegebenen App-Namen, indem Leerzeichen entfernt werden
    und er mit bekannten Apps (KNOWN_APPS) abgeglichen wird (Groß-/Kleinschreibung ignorierend).

    Args:
        name (str): Der vom Benutzer eingegebene (rohe) App-Name.

    Returns:
        str: Der korrigierte oder standardisierte App-Name.
    """
    name = name.strip()
    if not name:
        return name

    # Prüfen, ob die App (unabhängig von Groß-/Kleinschreibung) in der Liste bekannt ist
    for known in KNOWN_APPS:
        if name.lower() == known.lower():
            return known

    # Falls unbekannt, zumindest den ersten Buchstaben groß schreiben
    return name[0].upper() + name[1:] if name else name


def validate_entry(
    person: str,
    entry_date: date,
    total_minutes: int,
    apps: list,
    existing_df: pd.DataFrame,
) -> list:
    """
    Validiert die Eingaben des Benutzers, bevor sie gespeichert werden.
    Prüft auf Logikfehler wie Doppelbelegungen, negative Zeiten oder falsche Sortierung.

    Args:
        person (str): Name der Person.
        entry_date (date): Das Datum des einzutragenden Tages.
        total_minutes (int): Die gesamte Bildschirmzeit in Minuten.
        apps (list): Eine Liste von Tuples mit (App-Name, Minuten) für die Top-5-Apps.
        existing_df (pd.DataFrame): DataFrame der bisherigen Einträge.

    Returns:
        list: Eine Liste von Strings mit Fehlermeldungen. Ist die Liste leer, ist der Eintrag valide.
    """
    errors = []

    # Prüfen, ob für das gewählte Datum bereits ein Eintrag existiert
    if not existing_df.empty:
        already = existing_df[existing_df["date"].dt.date == entry_date]
        if not already.empty:
            errors.append(
                f"Für den {entry_date.strftime('%d.%m.%Y')} existiert bereits ein Eintrag. "
                "Lösche ihn zuerst weiter unten."
            )

    # Validierung der Gesamtzeit
    if total_minutes <= 0:
        errors.append("Gesamtzeit muss größer als 0 Minuten sein.")
    if total_minutes > 1440:
        errors.append("Gesamtzeit kann nicht mehr als 1440 Minuten (24 Std.) betragen.")

    # Validierung der einzelnen Apps
    for i, (app_name, app_min) in enumerate(apps, 1):
        if not app_name:
            errors.append(f"App {i}: Name darf nicht leer sein.")
        if app_min < 0:
            errors.append(f"App {i}: Minuten dürfen nicht negativ sein.")
        # Eine einzelne App darf nicht mehr Zeit in Anspruch nehmen als die Gesamtzeit
        if total_minutes > 0 and app_min > total_minutes:
            errors.append(
                f"App {i} ({app_min} min) übersteigt die Gesamtzeit ({total_minutes} min)."
            )

    # Prüfen, ob die Summe der Top 5 die Gesamtzeit überschreitet
    app_sum = sum(m for _, m in apps)
    if total_minutes > 0 and app_sum > total_minutes:
        errors.append(
            f"Summe der Top-5-Apps ({app_sum} min) übersteigt "
            f"die Gesamtzeit ({total_minutes} min)."
        )

    # Prüfen, ob die Apps korrekt absteigend nach Minuten sortiert wurden
    mins = [m for _, m in apps]
    if any(mins[i] < mins[i + 1] for i in range(len(mins) - 1)):
        errors.append(
            "Apps müssen nach Minuten absteigend sortiert sein "
            "(App 1 = meiste Minuten, App 5 = wenigste)."
        )

    # Prüfen, ob eine App mehrfach eingetragen wurde (Duplikate)
    names = [n.lower() for n, _ in apps if n]
    if len(names) != len(set(names)):
        errors.append("Jede App darf nur einmal eingetragen werden.")

    return errors


def append_entry(
    existing_df: pd.DataFrame,
    person: str,
    entry_date: date,
    total_minutes: int,
    apps: list,
) -> pd.DataFrame:
    """
    Fügt die validierten Daten als neue Zeile an den existierenden DataFrame an.

    Args:
        existing_df (pd.DataFrame): Der bisherige DataFrame.
        person (str): Name der Person.
        entry_date (date): Datum des Eintrags.
        total_minutes (int): Gesamte Bildschirmzeit in Minuten.
        apps (list): Liste von Tuples (App-Name, Minuten) der 5 Apps.

    Returns:
        pd.DataFrame: Ein neuer DataFrame, der den neuen Eintrag beinhaltet.
    """
    new_row = {
        "date": entry_date.strftime("%Y-%m-%d"),
        "person": person,
        "total_minutes": total_minutes,
        "app1_name": apps[0][0],
        "app1_minutes": apps[0][1],
        "app2_name": apps[1][0],
        "app2_minutes": apps[1][1],
        "app3_name": apps[2][0],
        "app3_minutes": apps[2][1],
        "app4_name": apps[3][0],
        "app4_minutes": apps[3][1],
        "app5_name": apps[4][0],
        "app5_minutes": apps[4][1],
    }
    new_row_df = pd.DataFrame([new_row])

    # Falls das bestehende DataFrame noch leer war, wird einfach die neue Zeile zurückgegeben
    if existing_df.empty:
        return new_row_df

    return pd.concat([existing_df, new_row_df], ignore_index=True)


def fmt_minutes(m: int) -> str:
    """
    Formatiert eine Minutenanzahl in ein lesbareres Format (z.B. '1h 30min').

    Args:
        m (int): Die Anzahl der Minuten.

    Returns:
        str: Der formatierte String (z.B. "2h 15min" oder "45 min").
    """
    return f"{m // 60}h {m % 60}min" if m >= 60 else f"{m} min"


# ── Streamlit UI ─────────────────────────────────────────────────

# Grundkonfiguration der Streamlit-Seite (Titel, Icon, Layout)
st.set_page_config(
    page_title="Bildschirmzeit — Eingabe",
    page_icon="📱",
    layout="centered",
)

st.title("📱 Bildschirmzeit eintragen")
st.caption("Trage hier täglich deine Handy-Nutzungszeit ein.")

# ── 1. Person ─────────────────────────────────────────────────────
st.subheader("1 · Wer bist du?")
# Dropdown zur Auswahl der Person
person = st.selectbox("Person", PERSONS, label_visibility="collapsed")

# Lade die bisherigen Daten der ausgewählten Person, während ein Ladeindikator angezeigt wird
with st.spinner("Daten werden geladen..."):
    existing_df = load_csv_from_github(person)

# Prüfen, ob für heute bereits ein Eintrag vorliegt, um den User darauf hinzuweisen
already_today = (
    not existing_df.empty and (existing_df["date"].dt.date == date.today()).any()
)
if already_today:
    st.info("Du hast heute bereits eingetragen — scrolle nach unten zum Korrigieren.")

st.divider()

# ── 2. Datum ──────────────────────────────────────────────────────
st.subheader("2 · Datum")
# Kalender-Widget zur Datumsauswahl (max_value verhindert Einträge in der Zukunft)
entry_date = st.date_input(
    "Datum",
    value=date.today(),
    max_value=date.today(),
    help="Du kannst jeden beliebigen Tag in der Vergangenheit eintragen.",
    label_visibility="collapsed",
)

# Warnung anzeigen, falls für das neu ausgewählte Datum schon ein Eintrag existiert
if not existing_df.empty:
    already = existing_df[existing_df["date"].dt.date == entry_date]
    if not already.empty:
        total_ex = int(already["total_minutes"].iloc[0])
        st.warning(
            f"Für den {entry_date.strftime('%d.%m.%Y')} existiert bereits ein Eintrag "
            f"({fmt_minutes(total_ex)}). Lösche ihn zuerst (ganz unten), "
            "bevor du neu einträgst."
        )

st.divider()

# ── 3. Gesamtzeit ─────────────────────────────────────────────────
st.subheader("3 · Gesamte Bildschirmzeit")
st.caption(
    "Den Wert findest du unter: "
    "Einstellungen → Bildschirmzeit (iOS) oder Digitales Wohlbefinden (Android)"
)

# Zwei nebeneinander liegende Spalten für Stunden und Minuten
col_h, col_m = st.columns(2)
with col_h:
    hours_input = st.number_input("Stunden", min_value=0, max_value=23, value=1, step=1)
with col_m:
    mins_input = st.number_input("Minuten", min_value=0, max_value=59, value=30, step=1)

# Umrechnung in Gesamtminuten
total_minutes = hours_input * 60 + mins_input

if total_minutes > 0:
    st.caption(f"= **{total_minutes} Minuten** gesamt")

st.divider()

# ── 4. Top-5-Apps ─────────────────────────────────────────────────
st.subheader("4 · Top 5 Apps")
st.caption(
    "Trage die fünf meistgenutzten Apps ein — App 1 hat die meisten Minuten, App 5 die wenigsten."
)

apps = []
# Schleife zur Erzeugung der Eingabefelder für exakt 5 Apps
for i in range(1, 6):
    st.markdown(f"**App {i}**")
    # Layout-Spalten: 3/5 für den Namen, 1/5 für Stunden, 1/5 für Minuten
    col_name, col_min_h, col_min_m = st.columns([3, 1, 1])

    with col_name:
        # Dropdown mit bekannten Apps plus Optionen für Freitext
        options = ["— App wählen —"] + KNOWN_APPS + ["Andere App..."]
        choice = st.selectbox(
            f"App {i} Name", options, key=f"sel_{i}", label_visibility="collapsed"
        )

        # Wenn "Andere App..." gewählt wird, erscheint ein Freitextfeld
        if choice == "Andere App...":
            raw = st.text_input(
                f"App {i} eingeben",
                key=f"custom_{i}",
                placeholder="z.B. Duolingo",
                label_visibility="collapsed",
            )
            app_name = normalize_app_name(raw)
        elif choice == "— App wählen —":
            app_name = ""
        else:
            app_name = choice

        # Hinweistext zeigen, falls die Normalisierung den Namen verändert hat
        if app_name and choice == "Andere App..." and app_name != raw.strip():
            st.caption(f"Wird gespeichert als: {app_name}")

    # Eingabefelder für die Zeit der jeweiligen App
    with col_min_h:
        st.caption("Std.")
        app_h = st.number_input(
            "h", 0, 23, 0, key=f"app{i}_h", label_visibility="collapsed"
        )
    with col_min_m:
        st.caption("Min.")
        app_m = st.number_input(
            "m", 0, 59, 0, key=f"app{i}_m", label_visibility="collapsed"
        )

    app_minutes = app_h * 60 + app_m
    apps.append((app_name, app_minutes))

    if app_minutes > 0:
        st.caption(f"= {app_minutes} Minuten")

# Anzeige eines Fortschrittsbalkens, der visualisiert,
# wie viel der Gesamtzeit durch die Top 5 Apps erklärt wird
if total_minutes > 0:
    app_sum = sum(m for _, m in apps)
    pct = min(app_sum / total_minutes, 1.0)
    unaccounted = total_minutes - app_sum
    st.progress(
        pct,
        text=f"Top-5 erfasst: {app_sum} min | Sonstige: {max(0, unaccounted)} min",
    )

st.divider()

# ── 5. Speichern ──────────────────────────────────────────────────
st.subheader("5 · Speichern")

# Speicher-Button lösen die Validierung und ggf. den Schreibvorgang aus
if st.button("Eintrag speichern", type="primary", use_container_width=True):
    # Validierung der Formulareingaben
    errors = validate_entry(person, entry_date, total_minutes, apps, existing_df)

    if errors:
        # Fehlermeldungen ausgeben, wenn Validierung fehlschlägt
        for err in errors:
            st.error(f"• {err}")
    else:
        # Bei Erfolg DataFrame aktualisieren und zu GitHub pushen
        with st.spinner("Wird in GitHub gespeichert..."):
            updated_df = append_entry(
                existing_df, person, entry_date, total_minutes, apps
            )
            save_csv_to_github(person, updated_df)

        # Erfolgsmeldung und visuelles Feedback (Ballons)
        st.success(
            f"Gespeichert! {person} · {entry_date.strftime('%d.%m.%Y')} · "
            f"{fmt_minutes(total_minutes)} · "
            f"{apps[0][0]} ({apps[0][1]} min), "
            f"{apps[1][0]} ({apps[1][1]} min), "
            f"{apps[2][0]} ({apps[2][1]} min), "
            f"{apps[3][0]} ({apps[3][1]} min), "
            f"{apps[4][0]} ({apps[4][1]} min)"
        )
        st.balloons()
        # Neuladen der Seite, um die Formulare zurückzusetzen und Daten neu zu fetchen
        st.rerun()

st.divider()

# ── 6. Einträge ansehen & löschen ────────────────────────────────
# Ein ausklappbarer Bereich (Expander), um bestehende Einträge einzusehen
with st.expander(f"Einträge von {person} ansehen & korrigieren"):
    fresh_df = load_csv_from_github(person)

    if fresh_df.empty:
        st.info("Noch keine Einträge vorhanden.")
    else:
        # DataFrame aufbereiten, damit er für den Benutzer schön formatiert aussieht
        display = fresh_df.sort_values("date", ascending=False).copy()
        display["date"] = display["date"].dt.strftime("%d.%m.%Y")
        display["gesamt"] = display["total_minutes"].apply(fmt_minutes)
        display = display[
            [
                "date",
                "gesamt",
                "app1_name",
                "app1_minutes",
                "app2_name",
                "app2_minutes",
                "app3_name",
                "app3_minutes",
                "app4_name",
                "app4_minutes",
                "app5_name",
                "app5_minutes",
            ]
        ]

        # Benutzerfreundliche Spaltennamen vergeben
        display.columns = [
            "Datum",
            "Gesamt",
            "App 1",
            "Min 1",
            "App 2",
            "Min 2",
            "App 3",
            "Min 3",
            "App 4",
            "Min 4",
            "App 5",
            "Min 5",
        ]
        # Die Tabelle in Streamlit anzeigen
        st.dataframe(display, use_container_width=True, hide_index=True)

        st.markdown("**Eintrag löschen** (um ihn neu einzutragen)")
        # Liste aller Datumsangaben erstellen, an denen etwas eingetragen wurde
        dates_available = sorted(fresh_df["date"].dt.date.unique(), reverse=True)

        # Lösch-Logik
        if dates_available:
            date_to_delete = st.selectbox(
                "Datum auswählen",
                options=dates_available,
                format_func=lambda d: d.strftime("%d.%m.%Y"),
                key="del_date",
            )

            # Löschen auslösen, wenn der Button geklickt wird
            if st.button("Eintrag löschen", type="secondary", key="del_btn"):
                with st.spinner("Wird gelöscht..."):
                    # Alle Einträge filtern, die NICHT das zu löschende Datum haben
                    updated = fresh_df[
                        fresh_df["date"].dt.date != date_to_delete
                    ].copy()
                    # Das aktualisierte (reduzierte) DataFrame auf GitHub speichern
                    save_csv_to_github(person, updated)
                st.success(
                    f"Eintrag vom {date_to_delete.strftime('%d.%m.%Y')} gelöscht."
                )
                st.rerun()
