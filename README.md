# screentime-dashboard


Ein Dashboard zur Visualisierung und Analyse von Bildschirmzeiten. Dieses Projekt hilft dabei, Nutzungsgewohnheiten zu verstehen, indem es Daten aus der Bildschirmzeit des Handys aufbereitet und grafisch darstellt.

Für die Erfassung der Bildschirmzeit gibt es eine extra App, bei der man die gesamte Bildschirmzeit und die Top 5 Apps tracken kann. Durch das speichern wird eine zum Benutzer zugehörige CSV Datei mit den Daten aktualisiert. 

Das Dashboard erfasst durch ein Reload die Daten und zeigt mehrere Matriken an, wie das Nutzungsverhalten im Vergleich zum Vortag oder auch Statistische Grafiken um einen Überblick zu geben. 

## Abhängigkeiten installieren
pip install -r requirements.txt

### Ausführung

Um die Bildschirmzeit zu tracken: 
https://screentime-dashboard-ly3f7pzpuf9a47puvxwc8v.streamlit.app/

Um das Dashboard lokal auszuführen, folge diesen Schritten:

streamlit run src/app.py



