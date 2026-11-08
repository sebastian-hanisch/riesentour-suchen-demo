# Riesentour suchen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-riesentour-suchen-demo.streamlit.app/)** -->

Elftes Stück der **Tourenbildung**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Verfahren: **Riesentour und Split**, ein Verfahren mit wachsendem Beispiel). Stück 1 ([riesentour-split-demo](https://github.com/sebastian-hanisch/riesentour-split-demo)) zeigt, dass eine Reihenfolge aller Kunden genügt, weil der **Split** sie optimal in Routen zerlegt; Stück 2 ([riesentouren-erzeugen-demo](https://github.com/sebastian-hanisch/riesentouren-erzeugen-demo)) baut solche Reihenfolgen, Stück 3 ([split-gegen-fuellen-demo](https://github.com/sebastian-hanisch/split-gegen-fuellen-demo)) vergleicht den Split mit „Füllen bis voll“, Stück 4 ([savings-gegen-split-demo](https://github.com/sebastian-hanisch/savings-gegen-split-demo)) und Stück 5 ([savings-varianten-demo](https://github.com/sebastian-hanisch/savings-varianten-demo)) legen Routen zusammen, Stück 6 ([sweep-cluster-first-demo](https://github.com/sebastian-hanisch/sweep-cluster-first-demo)) bildet erst Gruppen, Stück 8 ([zeitfenster-split-demo](https://github.com/sebastian-hanisch/zeitfenster-split-demo)) und Stück 9 ([solomon-klassen-demo](https://github.com/sebastian-hanisch/solomon-klassen-demo)) führen Zeitfenster ein. Dieses Stück **sucht die Reihenfolge**: ein genetischer Algorithmus über Riesentouren, dessen Kinder der Split bewertet (Prins), gegen einen, der die **Routen direkt** als Chromosom trägt, jeweils mit und ohne Lokalsuche. (Stück 7 ist ein optionales Stück und wurde nicht gebaut.)

## Kernfrage

Bringt die Sequenzkodierung bei gleichem Budget mehr? Die Demo zeigt eine Ordnungskreuzung von Hand, vier genetische Verfahren im Lauf (Folge + Split, Routen, je mit und ohne Lokalsuche, bei gleicher Zahl von Kindern), die Lokalsuche Zug für Zug, das Rückschreiben der verbesserten Routen in die Folge (Lamarck gegen Baldwin) und vorberechnete Bänder über feste Instanzen, live bis 25 Kunden, in den Bändern bis 100 Kunden gegen das exakte Optimum beziehungsweise PyVRP.

## Modell

Wie in den Stücken 1 bis 6: ein Depot, n Kunden mit ganzzahliger Nachfrage, gleiche Fahrzeuge der Kapazität Q (ohne Flottengrenze), euklidische Entfernungen, keine Zeitfenster; die Kapazität folgt aus der Auslastung. **Chromosomen:** eine Permutation aller Kunden (Riesentour), bewertet durch den optimalen **Split** (kürzester Weg im Hilfsgraphen), oder eine Liste von **Routen**. **Operatoren:** Folge: **Ordnungskreuzung (OX)**, Tausch- und Einfüge-Mutation; Routen: die Hälfte der Routen des einen Elters plus die Routen des anderen ohne die verteilten Kunden, Mutation „ein Kunde an die beste zulässige Stelle“. **Population:** 30, steady state (ein Kind je Schritt ersetzt das schlechteste Mitglied, wenn es sich in den Kosten von allen unterscheidet und besser ist), Turnierauswahl. **Lokalsuche:** 2-opt in der Route, Verschieben und Tauschen zu den 8 nächsten Nachbarn, erste Verbesserung; bei der Folge werden die verbesserten Routen wieder zu einer Folge zusammengesetzt (**Lamarck**), bei **Baldwin** bleibt das Chromosom und nur die Bewertung nutzt die Lokalsuche. **Budget:** die Zahl der **Kinder** (Bewertungen). **Referenz:** das exakte Optimum (Held–Karp) bis 12 Kunden, PyVRP 0.14.1 (5 Sekunden, ein Seed) darüber. Formeln stehen im 📐-Expander der App.

## Methodik

- **Kern** (`rsk_algorithm.py`, `rsk_scenario.py`, `rsk_construct.py`, `rsk_savings.py`): aus den Stücken 1 bis 6 kopiert, umbenannt und gekürzt (Split, exakter Löser, Instanzen, Einfügen nach Split, Savings als Maßstab).
- **Suche** (`rsk_search.py`): neu: Ordnungskreuzung, Routenkreuzung, Mutationen, Lokalsuche mit Zugspur, steady-state-Lauf mit Spur nach festen Kinderzahlen, Lamarck und Baldwin; alles bitgleich bei gleichem Seed.
- **Fünf Experimente:** eine Kreuzung von Hand (Handinstanz); vier Verfahren im Lauf; was die Lokalsuche tut (Zug für Zug); Lamarck oder Baldwin; Bänder über feste Instanzen.
- **Bänder** (`rsk_bands.json`, erzeugt von `generate_precomputed.py`): die Instanzen und Referenzen der Stücke 4 und 5 (die ersten 5, 4, 4 und 2 Instanzen jeder von vier Zellen: Karte zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke): n = 12 (20 Instanzen, exaktes Optimum), 25 und 50 (je 16), 100 (8; Referenz PyVRP); **ein Lauf je Instanz** (Seed gleich Instanzseed); Budget 16 000 Kinder ohne, 2 000 mit Lokalsuche (1 000 bei 100 Kunden); Spur nach 250, 500, 1000, 2000, 4000, 8000, 16000 Kindern; dazu die Maßstäbe der Konstruktion (Einfügen nach Split, Savings λ = 1, bestes von 9 λ) aus denselben Bändern.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an festen Seeds (Median über die Instanzen des Abstands zur Referenz in Prozent, vorzeichenbehaftet; „gepaart“ = Folge billiger / gleich / teurer als Routen beziehungsweise mit gegen ohne Lokalsuche), nachgerechnet in `tests/test_claims.py` und `tests/test_bands.py`. Verglichen wird nach **gleicher Zahl von Kindern**, nicht nach Zeit; ein Lauf je Instanz. Ab 25 Kunden ist die Referenz PyVRP (keine bewiesene Untergrenze; Fassungen mit Lokalsuche liegen in einzelnen Instanzen darunter).

| n (Instanzen) | Konstruktion: Einfügen nach Split / Savings / bestes von 9 λ | Folge + Split (16 000 Kinder) | Routen (16 000) | Folge + Split + Lokalsuche (2 000; bei 100: 1 000) | Routen + Lokalsuche |
|---|---|---|---|---|---|
| 12 (20) | 2,5 / 1,3 / 0,6 | 0,0 | 0,0 | 0,0 | 0,0 |
| 25 (16) | 4,0 / 2,9 / 1,5 | 1,2 | 5,3 | 0,0 | 0,0 |
| 50 (16) | 8,4 / 6,9 / 4,0 | 24,0 | 11,6 | 0,0 | 0,1 |
| 100 (8) | 11,5 / 8,4 / 5,9 | 97,5 | 27,6 | 1,7 | 7,4 |

- **Mit Lokalsuche liegt die Folge am Ende des Budgets vorn oder gleichauf (bei n = 12 und 25 ist „gleichauf“ ein Gleichstand der Endkosten).** Folge + Split + Lokalsuche gegen Routen + Lokalsuche am Ende des Budgets (billiger / gleich / teurer): n = 12: 0 / 20 / 0; n = 25: 1 / 15 / 0; n = 50: **9 / 7 / 0**; n = 100: **8 / 0 / 0** (1,7 gegen 7,4 %). Nach 1000 Kindern: n = 25: 2 / 14 / 0, n = 50: 9 / 6 / 1, n = 100: 8 / 0 / 0.
- **Ohne Lokalsuche kippt es mit der Größe und dem Verlauf.** Folge gegen Routen nach 1000 Kindern: n = 12: 6 / 4 / 10, n = 25: **1 / 0 / 15**, n = 50: 1 / 0 / 15, n = 100: 0 / 0 / 8 (n = 50: 104,5 gegen 60,2 %); am Ende des Budgets (16 000 Kinder): n = 12: 9 / 11 / 0, n = 25: **12 / 0 / 4** (1,2 gegen 5,3 %), n = 50: 3 / 0 / 13 (24,0 gegen 11,6 %), n = 100: 0 / 0 / 8 (97,5 gegen 27,6 %). Die Routenfassung kommt ab etwa 1000 Kindern pro Kind früher voran (n ≥ 25; bei n = 50 liegt nach 250 Kindern noch die Folge in 12 von 16 Instanzen vorn), stagniert bei n = 25 (5,3 % nach 8 000 und 16 000 Kindern) und n = 50 früh, die Folge braucht mehr Kinder, überholt sie bei n = 25 und holt innerhalb von 16 000 Kindern bei n = 50 und 100 nicht auf (die Folge verbessert sich dort noch bei jeder Verdopplung).
- **Die Lokalsuche entscheidet.** Mit gegen ohne Lokalsuche nach 1000 Kindern (billiger / gleich / teurer), Folge: n = 12: 13 / 7 / 0, n = 25: 16 / 0 / 0, n = 50: 16 / 0 / 0, n = 100: 8 / 0 / 0; Routen: 9 / 11 / 0, 16 / 0 / 0, 16 / 0 / 0, 8 / 0 / 0. Schon nach 250 Kindern liegen die Fassungen mit Lokalsuche bei n = 25 bei 0,0 %, bei n = 50 bei 0,1 % (Folge) und 0,8 % (Routen); ohne Lokalsuche bei 50,8 / 48,2 % (n = 25) und 152,0 / 150,2 % (n = 50).
- **Lamarck gegen Baldwin** (Folge + Split + Lokalsuche, Rückschreiben gegen nicht Rückschreiben, am Ende des Budgets, billiger / gleich / teurer): n = 12: 0 / 20 / 0; n = 25: 1 / 15 / 0; n = 50: **14 / 2 / 0** (0,0 gegen 1,1 %); n = 100: **7 / 0 / 1** (1,7 gegen 4,4 %).
- **Unter der Referenz.** Fassungen mit Lokalsuche liegen in der Zahl der Instanzen unter der PyVRP-Lösung (Folge + Lokalsuche / Routen + Lokalsuche / Baldwin): n = 25: 6 / 6 / 6 von 16; n = 50: 6 / 4 / 2 von 16; n = 100: 1 / 0 / 0 von 8; die Folge ohne Lokalsuche in 1 von 16 (n = 25). Die Referenz ist also keine Untergrenze.
- **Handbeispiel** (Handinstanz aus Stück 1 bis 4, Kapazität 7, Optimum 44,3623 mit den Routen (1 4) und (2 6 3 5)): Elter A = (3 5 2 6 4 1) mit Split 48,7306, Elter B = (1 6 4 3 5 2) mit Split 58,8797. Die **Ordnungskreuzung** mit dem Schnitt der Plätze 3 bis 4 von A behält (2 6) an diesen Plätzen und füllt den Rest in der Reihenfolge von B ohne 2 und 6: (1 4 2 6 3 5). Sein Split ist **44,3623, das Optimum** mit (1 4) und (2 6 3 5): ein Kind besser als beide Eltern, die 9,8 und 32,7 % über dem Optimum liegen. Von den 21 möglichen Schnitten liefert nur dieser ein Kind, das beide Eltern schlägt, 6 liefern ein Kind so gut wie der bessere Elter.

## Ehrliche Grenzen

- Die Aussagen gelten für die gemessenen Größen (12, 25, 50, 100 Kunden), drei Zielrouten, 90 % Auslastung, die zwei Kartenarten der Bänder und diese **einfachen** genetischen Verfahren; sie sind keine Aussagen über HGS oder andere Operatoren.
- **Ein Lauf je Instanz:** jede einzelne Zahl hat Zufall; bei 100 Kunden sind es nur 8 Instanzen.
- Die Mutationswahrscheinlichkeit ist auf eigenen Instanzen abgestimmt; mit 0,3 statt 1,0 war die Routenfassung ohne Lokalsuche bei 50 Kunden im Median und im Mittel deutlich schlechter (Median 23,2 gegen 11,6 %), je Instanz aber gemischt (in 9 von 16 Instanzen schlechter, in 7 von 16 besser). Das Ergebnis „Folge gegen Routen“ ohne Lokalsuche hängt an dieser Stellschraube und an der einfachen Routenkreuzung.
- Ab 25 Kunden ist die Referenz PyVRP (5 Sekunden, ein Seed), eine gute Lösung und keine bewiesene Untergrenze.
- Das Budget ist die Zahl der Kinder; ein Kind mit Lokalsuche und der Split je Kind kosten sehr verschieden viel Zeit. Wer nach Zeit vergleicht, kommt zu anderen Rangfolgen für die Fassungen ohne Lokalsuche (die Folge braucht je Kind mehr Rechenzeit, die Routenfassung weniger).
- „Gleichauf“ heißt hier: die Mediane liegen weniger als einen Prozentpunkt auseinander.
- Die Fall-Demo [vrp_demo](https://sebastianhanisch-vrp-demo.streamlit.app/) rechnet ebenfalls einen genetischen Algorithmus mit Split; ihre Zahlen werden nicht übernommen. [memetic-demo](https://sebastianhanisch-memetic-demo.streamlit.app/) zeigt dieselbe Idee auf einer Rundreise. Keine Zahl aus der Literatur wird übernommen.
- Die Diagramme wurden im Browser angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft.

### Annahmen, Grenzen und bekannte Probleme (Text wie in der App)

**Annahmen**
- Ein Depot, beliebig viele gleiche Fahrzeuge (die Flottengrenze fehlt), euklidische und symmetrische Entfernungen, keine Zeitfenster; jeder Kunde wird genau einmal von einem Fahrzeug bedient, seine Nachfrage ist nicht teilbar.
- Alles ist simuliert: Karten aus Zufallszahlen, kein Straßennetz, keine echten Aufträge.
- Die vier genetischen Verfahren sind **einfach gehalten**: Population 30, steady state, Turnierauswahl, Ordnungskreuzung (Folge) beziehungsweise Routenkreuzung (Routen), Tausch-/Einfüge-Mutation beziehungsweise „bester zulässiger Platz“, Lokalsuche mit 2-opt, Verschieben und Tauschen zu den 8 nächsten Nachbarn. Es ist **kein Hybrid Genetic Search**: Strafen für unzulässige Pläne, Diversitätsmanagement und SWAP* fehlen.
- Die Mutationswahrscheinlichkeit ist auf eigenen Instanzen abgestimmt (nicht auf denen der Auswertung): 1,0 ohne Lokalsuche, 0,3 mit Lokalsuche. Das Ergebnis „Folge gegen Routen“ ohne Lokalsuche hängt an dieser Stellschraube und an den einfachen Operatoren.
- Das Budget ist die Zahl der **Kinder** (Bewertungen), nicht die Zeit: ein Kind mit Lokalsuche und ein Kind ohne kosten sehr verschieden. Die Zeiten und Kinder je Sekunde sind Messungen in Python unter Windows und werden nicht festgeschrieben.

**Grenzen**
- Live rechnet die App bis zu 25 Kunden; das exakte Optimum steht bis 12 Kunden, darüber ist die Referenz die beste Lösung der Seite (Maßstäbe und Läufe), ausdrücklich keine Untergrenze. Die Bänder gelten für 12 Kunden (20 Instanzen, exaktes Optimum) und für 25, 50 und 100 Kunden (16, 16 und 8 Instanzen, Referenz PyVRP, nicht bewiesen optimal) bei drei Zielrouten und 90 % Auslastung; **ein Lauf je Instanz**.
- Die Referenz PyVRP 0.14.1 (5 Sekunden, ein Seed) ist eine gute Lösung, keine Untergrenze: Fassungen mit Lokalsuche liegen in einzelnen Instanzen darunter. Die Referenzen stehen in `rsk_bands.json` (Instanzen und Referenzen aus den Bändern der Stücke 4 und 5); die Tests rechnen PyVRP nicht.
- Die Aussage „Folge + Split schlägt Routen“ gilt nur mit Lokalsuche und mit der Größe; ohne Lokalsuche liegt die Routenfassung bei 50 und 100 Kunden pro Kind vorn.
- Zeitfenster, Flottengrenze und HGS-Bausteine sind nicht gebaut (Stücke 8, 9 und 15 der Reihe).

**Bekannte Probleme und Unsicherheiten**
- Ein Lauf je Instanz: die Bänder zählen über viele Instanzen, jede einzelne Zahl hat Zufall; bei 100 Kunden sind es nur 8 Instanzen.
- Bei gleichen Kosten entscheiden feste Regeln (kleinster Startknoten im Split, kleinste Stelle beim Einfügen, erste Verbesserung in der Lokalsuche); andere Regeln ergeben andere, gleich gute Pläne.
- Die Routenfassung stagniert bei den einfachen Operatoren bei n = 25 und 50 früh (keine Verbesserung mehr nach einigen tausend Kindern, bei n = 100 verbessert sie sich noch); die Vermutung, mit anderen Kreuzungen wäre sie besser, ist nicht gemessen.
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft.

## Befunde und Korrekturen gegenüber dem Plan

- **Kinderzahl statt Zeit:** Die Planung maß mit Zeitgrenzen (5, 10, 20, 40 Sekunden); der Bau rechnet mit der Zahl der Kinder als Budget und misst neu. Dadurch ändern sich Zahlen und eine Aussage: Ohne Lokalsuche liegt die Folge bei n = 50 nach 20 Sekunden fast gleichauf mit den Routen (12,9 gegen 11,6 %), nach 16 000 Kindern aber 24,0 gegen 11,6 %, weil die Folge je Kind länger rechnet; bei n = 100 war Lamarck gegen Baldwin nach 40 Sekunden 8 / 0 / 0, nach 1000 Kindern 7 / 0 / 1.
- **Phase-0-Läufe reproduziert:** 66 Kontrollwerte der Planung (beste Kosten nach 250, 500, 1000 Kindern für sieben Instanzgruppen und Fassungen) kommen aus dem neuen Kern identisch heraus.
- **Endlosschleife der Anfangspopulation:** Die Planung verlangte in der Anfangspopulation lauter verschiedene Kosten; bei kleinen Instanzen mit Lokalsuche (12 Kunden) landen alle zufälligen Folgen im selben Optimum, die Suche nach dreißig verschiedenen Werten endete nie. Der Kern lässt nach dem Zwanzigfachen der Populationsgröße Versuche gleiche Kosten zu (Test: n = 2 und 3, Population 30).
- **Referenzen:** Die Referenzen und Maßstäbe stammen aus `svv_bands.json` der savings-varianten-demo; die Bänder dieser Demo enthalten sie als Kopie, die Tests rechnen PyVRP nicht.
- **Port:** 9459 laut Plan.

## Verifikation

- **Handwerte:** die Handinstanz (Split der Eltern 48,7306 und 58,8797 und des Kindes 44,3623 mit Routen), Ordnungskreuzung an einer Folge von 5 Kunden und am Handbeispiel, Routenkreuzung, 2-opt an einem Quadrat (Gewinn und Route nach dem ersten Zug), Verschieben, „Füllen bis voll“, Prüfer (`tests/test_search_hand.py`).
- **Orakel:** Split gegen die Aufzählung aller Zerlegungen (n = 8) mit eigener Länge; Dominanz (Minimum über alle Folgen gleich dem exakten Optimum, n = 7); jede Fassung liefert vollständige, kapazitätsgerechte Pläne mit gemessener Länge gleich der Bewertung und nie unter dem Optimum; jede Fassung findet das Optimum der Handinstanz; Lokalsuche nie schlechter, zulässig und idempotent, jeder Zug verbessert; Läufe bitgleich bei gleichem Seed; Spur monoton (`tests/test_oracle_search.py`).
- **Eigenschaften:** OX liefert eine Permutation und übernimmt das Teilstück; die Routenkreuzung deckt jeden Kunden genau einmal ab; Umnummerieren ändert das Optimum nicht; ein größeres Budget ist nie schlechter und teilt die ersten Kinder; Lamarck und Baldwin bewerten gleich (`tests/test_properties.py`).
- **Randfälle:** n = 1, 2, 3 (Population größer als die Zahl der Folgen), Kinderzahl 0, Kapazität für alle, Nachfrage gleich Kapazität, ein Quadrat (`tests/test_edge_cases.py`).
- **Verdikte:** jede Verzweigung und jede Zahl im Text (`tests/test_verdicts.py`).
- **Zahlen der README und der Preset-Hilfen:** `tests/test_claims.py`; die vorberechneten Bänder auf Aufbau und gegen eine frische Rechnung einer Stichprobe (`tests/test_bands.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Kreuzung, Läufe, Lokalsuche, Bänder, PDF (`tests/test_app.py`, `tests/test_experiments.py`), Footer, Layout, Laufzeit-Importe.

## Tests

168 Tests. Laufzeit lokal rund dreieinhalb Minuten (gemessen: 211 Sekunden).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `generate_precomputed.py` | erzeugt `rsk_bands.json` aus den Instanzen und Referenzen von Stück 5 (Teile lassen sich parallel rechnen) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `rsk_algorithm.py` | Kern aus Stück 1: Split, Hilfsgraph, exakter Löser, Held–Karp |
| `rsk_bands.json` | vorberechnete Bänder (60 Instanzzeilen, je fünf Läufe) |
| `rsk_constants.py` | Regler-Grenzen, Verfahren, Budgets, Bänder, Farben, Presets, Annahmentext |
| `rsk_construct.py` | Einfügen nach Split (Maßstab) |
| `rsk_evaluation.py` | Analyse, Kreuzungsansicht, Lokalsuche-Spur, Bänder, Kennzahlen, Verdikt-Logik |
| `rsk_layout.py` | Fester Kopf und Tabellenregel (Stylesheet) |
| `rsk_pdf_export.py` | PDF-Export des Ergebnisses |
| `rsk_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `rsk_savings.py` | Savings (aus Stück 4, Maßstab) |
| `rsk_scenario.py` | Instanzen (aus Stück 1, mit Auslastung als Parameter) |
| `rsk_search.py` | genetische Suche: Operatoren, Lokalsuche, Läufe mit Spur |
| `rsk_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handinstanz, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, Bänder, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Hybrid Genetic Search:** Strafen für unzulässige Pläne, Diversitätsmanagement, SWAP* und die Auswahl nach Rang und Diversität sind nicht nachgebaut; PyVRP bleibt die Referenz (Stück 15 vergleicht den Stand der Technik).
- **Mehrere Läufe je Instanz** und eine Abstimmung aller Parameter: nur die Mutationswahrscheinlichkeit ist abgestimmt, ein Lauf je Instanz.
- **Zeitfenster und Flottengrenze:** Stücke 8, 9 und 3.
- **Asymmetrische Entfernungen und verschiedene Fahrzeugtypen:** nur symmetrische Entfernungen und gleiche Fahrzeuge.
- **Instanzen über 25 Kunden live:** größere Instanzen stehen nur in den vorberechneten Bändern.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
