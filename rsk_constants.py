"""Konstanten: Regler-Grenzen, Verfahren, Budgets, Bänder, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 25, 6
SEED_MAX, DEFAULT_SEED = 999999, 0
ROUTES_MIN, ROUTES_MAX, DEFAULT_ROUTES = 2, 4, 3
FILL_MIN, FILL_MAX, FILL_STEP, DEFAULT_FILL = 60, 100, 2, 90   # Auslastung in Prozent: Kapazität = aufgerundet Gesamtnachfrage / (Zielroutenzahl · Auslastung)
CLUSTERS, CLUSTER_SIGMA = 3, 7.0              # Familie „In Gruppen“
FAMILIES = ("Kleine Karte (ganze Zahlen)", "Zufällig verteilt (0 bis 100)", "In Gruppen (0 bis 100)", "Handinstanz (n = 6)")
FAMILY_KEYS = ("small", "random", "clustered")   # Familie 3 (Handinstanz) hat keinen Generator
HAND_FAMILY = 3
DEFAULT_FAMILY = HAND_FAMILY
DEPOTS = ("In der Mitte", "In der Ecke")
DEFAULT_DEPOT = 0
EXACT_MAX = 12                                # bis zu dieser Größe rechnet die App das exakte Optimum
TOL = 1e-9                                    # Gleichstände und Gleichheit von Kosten: absolut
TIE = 1e-12                                   # Beim Einfügen zählt ein Kandidat nur als besser, wenn er um mehr als TIE besser ist
GAP_WARN = 5.0                                # Abstand in Prozent, ab dem das Verdikt warnt
LEVEL_PP = 1.0                                # „gleichauf“: Unterschied der Mediane unter einem Prozentpunkt

# Handinstanz aus den Stücken 1 bis 4 (Depot (0,0), Kapazität 7, Optimum 44,3623 mit den Routen (1 4) und (2 6 3 5))
HAND_XY = ((0.0, 0.0), (6.0, -6.0), (-2.0, 5.0), (-4.0, -4.0), (0.0, -7.0), (-1.0, -1.0), (-6.0, 3.0))
HAND_DEMAND = (3, 2, 2, 4, 2, 1)
HAND_CAPACITY = 7
HAND_PARENTS = ((3, 5, 2, 6, 4, 1), (1, 6, 4, 3, 5, 2))        # Eltern des Handbeispiels; die Voreinstellung der App findet sie über die Seeds PARENT_SEEDS
PARENT_SEEDS = (31, 873)                      # Seeds, deren zufällige Mischung der Kunden 1 bis 6 die Handbeispiel-Eltern ergibt

# Verfahren: Schlüssel, Namen, Farben
KINDS = ("S", "R", "SL", "RL")                # Folge + Split, Routen, jeweils ohne und mit Lokalsuche
EXTRA_KINDS = ("SB",)                         # Folge + Split + Lokalsuche, aber Bewertung ohne Rückschreiben (Baldwin)
ALL_KINDS = KINDS + EXTRA_KINDS
KIND_NAMES = {
    "S": "Folge + Split",
    "R": "Routen",
    "SL": "Folge + Split + Lokalsuche",
    "RL": "Routen + Lokalsuche",
    "SB": "Folge + Split + Lokalsuche (Baldwin)",
}
KIND_COLORS = {"S": "#7fb3ad", "R": "#d8a13a", "SL": "#2F6B65", "RL": "#b5651d", "SB": "#7b5ea7"}
HAS_LS = {"S": False, "R": False, "SL": True, "RL": True, "SB": True}
POP_SIZE = 30
MUT_PLAIN, MUT_LS = 1.0, 0.3                  # Mutationswahrscheinlichkeit ohne und mit Lokalsuche (Abstimmung: Plan und README)
NEIGHBORS = 8                                 # Nachbarn je Kunde für Verschieben und Tauschen in der Lokalsuche
CHECKPOINTS = (250, 500, 1000, 2000, 4000, 8000, 16000)

# Budgets (Kinder) der Bänder je Größe: ohne Lokalsuche, mit Lokalsuche
BAND_SIZES = (12, 25, 50, 100)
BAND_BUDGET = {12: (16000, 2000), 25: (16000, 2000), 50: (16000, 2000), 100: (16000, 1000)}
BAND_PER_CELL = {12: 5, 25: 4, 50: 4, 100: 2}  # Instanzen je Zelle (vier Zellen: Karte zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke)
BAND_CELLS = ((1, 0), (2, 0), (1, 1), (2, 1))
BAND_ROUTES, BAND_FILL = 3, 90
BAND_FILE = "rsk_bands.json"
SOURCE_BANDS_FILE = "svv_bands.json"          # Quelle der Instanzen und Referenzen (savings-varianten-demo, Stück 5): exaktes Optimum bis 12 Kunden, PyVRP (5 s, ein Seed) darüber
LIVE_BUDGET_PLAIN, LIVE_BUDGET_LS = (500, 8000, 2000), (100, 2000, 500)     # Regler der App: (kleinster, größter, Voreinstellung)

ROUTE_COLORS = ("#2F6B65", "#c0504d", "#4c78a8", "#d8a13a", "#7b5ea7", "#8c564b", "#17becf", "#e377c2")
COLOR_REF = "#c0504d"

# Presets (die Zahlen in den Hilfetexten prüft tests/test_claims.py); das erste ist die Voreinstellung
PRESETS = {
    "Ein Kind besser als beide Eltern (Handinstanz)": {"n": 6, "family": 3, "depot": 0, "routes": 3, "fill": 90, "seed": 0},
    "Die Lokalsuche entscheidet (n = 25)": {"n": 25, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 300000},
    "Folge oder Routen: je nach Instanz (n = 25)": {"n": 25, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 300002},
    "Die Konstruktion liegt 15 % daneben (n = 12, exakt)": {"n": 12, "family": 1, "depot": 1, "routes": 3, "fill": 90, "seed": 300001},
    "Rückschreiben zählt (n = 25)": {"n": 25, "family": 2, "depot": 1, "routes": 3, "fill": 90, "seed": 300000},
}
PRESET_HELP = {
    "Ein Kind besser als beide Eltern (Handinstanz)": "Handinstanz aus den Stücken 1 bis 4: Elter A (3 5 2 6 4 1) kostet im Split 48,73, Elter B (1 6 4 3 5 2) 58,88. Die Ordnungskreuzung mit dem Schnitt der Plätze 3 bis 4 liefert (1 4 2 6 3 5), dessen Split 44,36 das Optimum ist; von 21 Schnitten liefert nur dieser ein Kind, das beide Eltern schlägt.",
    "Die Lokalsuche entscheidet (n = 25)": "Mit 2000 Kindern ohne und 500 mit Lokalsuche liegt Folge + Split 26,7 % und Routen 10,2 % über der besten Lösung 496,75, mit Lokalsuche liegen beide bei 0,0 %; Einfügen nach Split liegt 2,3 % darüber.",
    "Folge oder Routen: je nach Instanz (n = 25)": "Ohne Lokalsuche liegt hier Folge + Split 10,1 % (3 Routen) vor Routen 23,7 % (5 Routen) über der besten Lösung 531,43; bei der Instanz des Presets davor ist es umgekehrt. Mit Lokalsuche liegen beide bei 0,0 %.",
    "Die Konstruktion liegt 15 % daneben (n = 12, exakt)": "Das exakte Optimum 650,67; Einfügen nach Split kostet 749,98 (15,3 % darüber), Savings 701,75. Alle vier genetischen Fassungen finden das Optimum mit 2000 und 500 Kindern.",
    "Rückschreiben zählt (n = 25)": "Die beste Lösung 495,23 findet Folge + Split + Lokalsuche mit Rückschreiben (Lamarck); ohne Rückschreiben (Baldwin) 495,73 (0,1 % darüber). Ohne Lokalsuche liegen Folge + Split 9,5 % und Routen 5,4 % darüber.",
}

# Text des Expanders „Annahmen, Grenzen und bekannte Probleme“; derselbe Text steht in der README (tests/test_readme.py vergleicht beide)
ASSUMPTIONS_MARKDOWN = """**Annahmen**
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
- Die Routenfassung stagniert bei den einfachen Operatoren früh (keine Verbesserung mehr nach einigen tausend Kindern); mit anderen Kreuzungen wäre sie besser.
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft."""
