"""Riesentour suchen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 11 der Reihe „Tourenbildung“: Bringt es bei gleichem Budget mehr, die Reihenfolge (Riesentour) zu suchen und mit dem Split zu bewerten, als die Routen direkt zu suchen? Die Demo zeigt eine Kreuzung von Hand,
vier genetische Verfahren im Lauf (Folge + Split und Routen, mit und ohne Lokalsuche), die Lokalsuche Zug für Zug, das Rückschreiben der Routen in die Folge (Lamarck oder Baldwin) und vorberechnete Bänder bis 100 Kunden.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import rsk_constants as C
from rsk_evaluation import (
    Settings,
    analyse,
    band_rows,
    band_stats,
    crossover_view,
    de,
    gap_percent,
    instances_word,
    ls_steps,
    order_text,
    pct,
    reference,
    routes_text,
    routes_word,
    run_kind,
    signed_pct,
    verdict_bands,
    verdict_cross,
    verdict_lamarck,
    verdict_ls,
    verdict_runs,
)
from rsk_layout import dunkles_design, kopf_css
from rsk_pdf_export import build_pdf
from rsk_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from rsk_visualization import build_band_curves, build_curves, build_map

st.set_page_config(page_title="Riesentour suchen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _run(settings, kind, children, mut):
    return run_kind(settings, kind, children, mut)


@st.cache_data(show_spinner=False)
def _cross(settings, seed_a, seed_b, cut):
    return crossover_view(settings, seed_a, seed_b, cut)


@st.cache_data(show_spinner=False)
def _ls(settings, start):
    return ls_steps(settings, start)


@st.cache_data(show_spinner=False)
def _band_stats(n):
    return band_stats(band_rows(n))


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in rsk_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧬 Riesentour suchen")
st.markdown(
    """
**Bringt es mehr, die Reihenfolge zu suchen?** Eine **Riesentour** ist eine Reihenfolge aller Kunden; der **Split** (Stücke 1 bis 3) zerlegt sie optimal in Routen und bewertet sie damit. Ein genetischer Algorithmus kann
diese Folgen kreuzen und mutieren (**Prins**) oder die **Routen direkt** als Chromosom tragen. Die Demo stellt beide bei **gleicher Zahl von Kindern** nebeneinander, jeweils ohne und mit **Lokalsuche**, und zeigt, wann die Folge
mit Split vorn liegt und wann nicht.

Weiter unten: **🔬 Eine Kreuzung von Hand**, **🔬 Vier Verfahren im Lauf**, **🔬 Was die Lokalsuche tut**, **🔬 Rückschreiben: Lamarck oder Baldwin**, **🔬 Wie schlagen sich die Verfahren?**, **🚧 Wo die Annahmen enden**,
der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So arbeiten die vier Verfahren", expanded=True):
    st.markdown(
        """
1. **Folge + Split:** Ein Chromosom ist eine Permutation aller Kunden; seine Kosten sind die des optimalen Splits. **Ordnungskreuzung (OX):** ein Teilstück des einen Elters bleibt an seinen Plätzen, der Rest wird in der Reihenfolge des anderen aufgefüllt.
2. **Routen:** Ein Chromosom ist eine Liste von Routen. Kreuzung: die Hälfte der Routen des einen Elters, dazu die Routen des anderen ohne die schon verteilten Kunden. Mutation: ein Kunde an die beste zulässige Stelle.
3. **Lokalsuche:** Jedes Kind wird danach lokal verbessert (2-opt in der Route, Verschieben und Tauschen zu den nächsten Nachbarn). Bei der Folge werden die verbesserten Routen wieder zu einer Folge zusammengesetzt (**Lamarck**); bei **Baldwin** zählt nur die Bewertung.
4. **Gleiches Budget:** Population 30, ein Kind je Schritt ersetzt das schlechteste Mitglied; verglichen wird nach gleicher Zahl von Kindern. Die Referenz ist das exakte Optimum (bis 12 Kunden) beziehungsweise PyVRP.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    family = st.selectbox("Art der Karte", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="„Handinstanz“: die Instanz der Stücke 1 bis 4 (6 Kunden, Kapazität 7). „Kleine Karte“: ganze Koordinaten 0 bis 16, Nachfragen 1 bis 4. Die beiden anderen: Karte 0 bis 100, Nachfragen 1 bis 10; „In Gruppen“: drei Häufungen von Kunden.")
    hand = int(family) == C.HAND_FAMILY
    if hand:
        st.caption("Bei der Handinstanz gelten Kunden, Depot, Zielroutenzahl und Auslastung nicht; der Seed legt nur den Zufall der Läufe fest.")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help=f"Bis n = {C.EXACT_MAX} rechnet die App das exakte Optimum, darüber ist die Referenz die beste Lösung der Seite. Bei der Handinstanz gilt n = 6.")
    depot = st.selectbox("Lage des Depots", list(range(len(C.DEPOTS))), key="depot_select", format_func=lambda i: C.DEPOTS[i])
    routes = st.slider("Zielroutenzahl", *bounds("routes_slider"), key="routes_slider", help="Legt zusammen mit der Auslastung die Kapazität fest.")
    fill = st.slider("Auslastung (%)", *bounds("fill_slider"), step=C.FILL_STEP, key="fill_slider", help="Kapazität = aufgerundet Gesamtnachfrage geteilt durch (Zielroutenzahl mal Auslastung).")
    seed = st.number_input("Zufalls-Seed der Instanz und der Läufe", *bounds("seed_input"), key="seed_input", step=1, help="Der Seed legt die Instanz fest (außer bei der Handinstanz) und den Zufall der genetischen Läufe.")
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"n_slider": int(n), "family_select": int(family), "depot_select": int(depot), "routes_slider": int(routes), "fill_slider": int(fill), "seed_input": int(seed)})

settings = Settings(int(n), int(family), int(depot), int(routes), int(fill), int(seed))
a = _analysis(settings)
inst = a.inst

# Läufe: die Regler stehen in Experiment 2; ihre Werte aus dem letzten Lauf der Seite (beim ersten Aufruf die Voreinstellung)
ss = st.session_state
b_plain = int(ss.get("budget_plain", C.LIVE_BUDGET_PLAIN[2]))
b_ls = int(ss.get("budget_ls", C.LIVE_BUDGET_LS[2]))
m_plain = float(ss.get("mut_plain", C.MUT_PLAIN))
m_ls = float(ss.get("mut_ls", C.MUT_LS))
results = {k: _run(settings, k, b_ls if C.HAS_LS[k] else b_plain, m_ls if C.HAS_LS[k] else m_plain) for k in C.KINDS}
ref_cost, ref_label = reference(a, results)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: vier Verfahren gegen die Referenz")
m1, m2, m3, m4 = st.columns(4)
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2). Die Differenz aus den angezeigten, gerundeten Werten, damit Zahl und Delta zusammenpassen.
m1.metric("Referenz" + (" (exakt)" if a.exact is not None else " (beste Lösung der Seite)"), de(ref_cost), delta="Referenz", delta_color="off")
for col, key, name in ((m2, "SL", C.KIND_NAMES["SL"]), (m3, "RL", C.KIND_NAMES["RL"]), (m4, "S", C.KIND_NAMES["S"])):
    col.metric(name, de(results[key].cost), delta=f"{round(results[key].cost, 2) - round(ref_cost, 2):+.2f} gegen Referenz".replace(".", ","), delta_color="inverse")
base = ", ".join(f"{nm} {de(v[0])}" for nm, v in (("Einfügen nach Split", a.baselines["es"]), ("Savings λ = 1", a.baselines["sav"]), ("bestes von 9 λ", a.baselines["best9"])))
st.caption(f"{inst.n} Kunden, Kapazität {inst.capacity}, Gesamtnachfrage {sum(inst.demand)}. Die Konstruktionen als Maßstab: {base}. Budget: {b_plain} Kinder ohne, {b_ls} Kinder mit Lokalsuche.")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, a, results), file_name="riesentour-suchen.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Bringt die Folge mit Split bei gleichem Budget mehr?")
kind, text = verdict_runs(a, results)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Eine Kreuzung von Hand")
st.caption("Zwei Eltern-Folgen (aus Seeds gemischt) und die Ordnungskreuzung: das Teilstück zwischen den Schnittplätzen bleibt von Elter A, der Rest wird in der Reihenfolge von Elter B aufgefüllt. Der Split bewertet alle drei Folgen. "
           "Mit den Voreinstellungen ist es das Handbeispiel: ein Kind, das besser ist als beide Eltern.")
x1, x2, x3 = st.columns(3)
with x1:
    seed_a = int(st.number_input("Seed Elter A", 0, 10 ** 6, C.PARENT_SEEDS[0], key="parent_a", step=1))
with x2:
    seed_b = int(st.number_input("Seed Elter B", 0, 10 ** 6, C.PARENT_SEEDS[1], key="parent_b", step=1))
with x3:
    lo, hi = st.slider("Schnittplätze von A (von bis)", 1, inst.n, (min(3, inst.n), min(4, inst.n)), key=f"cut_{inst.n}")
cross = _cross(settings, seed_a, seed_b, (int(lo) - 1, int(hi) - 1))
cols = st.columns(3)
for col, key, title in zip(cols, ("a", "b", "child"), ("Elter A", "Elter B", "Kind")):
    with col:
        v = cross[key]
        st.markdown(f"**{title}:** {order_text(v['order'])}  \nSplit **{de(v['cost'])}** ({routes_word(len(v['routes']))}): {routes_text(v['routes'])}")
        st.plotly_chart(build_map(inst, v["routes"], legend=False), width="stretch", key=f"map_cross_{key}")
kind, text = verdict_cross(cross)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Vier Verfahren im Lauf")
st.caption("Dieselbe Instanz, derselbe Seed, vier Läufe mit festem Kinderbudget. Die Linien zeigen die beste Gesamtlänge nach der Zahl der Kinder (logarithmische Achse); gestrichelt die Referenz und die Konstruktionen. "
           "Ein Kind ist eine Bewertung (bei der Lokalsuche inklusive der Verbesserung), keine Sekunde: die Verfahren brauchen sehr verschieden lange je Kind.")
r1, r2, r3, r4 = st.columns(4)
with r1:
    st.slider("Kinder ohne Lokalsuche", C.LIVE_BUDGET_PLAIN[0], C.LIVE_BUDGET_PLAIN[1], C.LIVE_BUDGET_PLAIN[2], step=250, key="budget_plain")
with r2:
    st.slider("Kinder mit Lokalsuche", C.LIVE_BUDGET_LS[0], C.LIVE_BUDGET_LS[1], C.LIVE_BUDGET_LS[2], step=100, key="budget_ls")
with r3:
    st.slider("Mutation ohne Lokalsuche", 0.0, 1.0, C.MUT_PLAIN, step=0.1, key="mut_plain", help="Wahrscheinlichkeit, dass ein Kind mutiert wird. Für die einfachen Fassungen zählt sie viel (siehe README).")
with r4:
    st.slider("Mutation mit Lokalsuche", 0.0, 1.0, C.MUT_LS, step=0.1, key="mut_ls")
st.plotly_chart(build_curves(results, ref_cost, {"Einfügen": a.baselines["es"], "bestes von 9 λ": a.baselines["best9"]}), width="stretch", key="curves")
table = ["| Verfahren | Beste Gesamtlänge | Abstand zur Referenz | Routen | Kinder | Zeit (Hinweis) |", "|---|---|---|---|---|---|"]
for k, r in results.items():
    table.append(f"| **{C.KIND_NAMES[k]}** | {de(r.cost)} | {signed_pct(gap_percent(r.cost, ref_cost))} | {len(r.routes)} | {r.children} | {de(r.seconds, 1)} s |")
st.markdown("\n".join(table))
st.caption(f"Referenz: {ref_label}. Die Zeiten sind Messungen dieser Sitzung in Python und nicht festgeschrieben.")

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Was die Lokalsuche tut")
st.caption("Ein Ausgangsplan wird Zug für Zug verbessert: 2-opt kehrt ein Stück einer Route um, Verschieben setzt einen Kunden an eine bessere Stelle (auch in eine andere Route), Tauschen vertauscht zwei Kunden aus verschiedenen Routen. "
           "Die Karte zeigt den Plan nach dem gewählten Zug.")
start = st.radio("Ausgangsplan", ["random", "es", "sav"], key="ls_start", horizontal=True, format_func=lambda k: {"random": "Zufällige Folge + Split", "es": "Einfügen nach Split", "sav": "Savings λ = 1"}[k])
info = _ls(settings, start)
steps = info["steps"]
if steps:
    step = st.slider("Zug", 0, len(steps), len(steps), key=f"ls_step_{start}_{len(steps)}", help="0: der Ausgangsplan.")
else:
    step = 0
cur_routes = info["start"] if step == 0 else steps[step - 1]["routes"]
cur_cost = info["start_cost"] if step == 0 else steps[step - 1]["cost"]
l1, l2 = st.columns([1, 1])
with l1:
    st.markdown(f"**Nach {step} von {len(steps)} Zügen: {de(cur_cost)}** ({routes_word(len(cur_routes))})")
    st.plotly_chart(build_map(inst, cur_routes), width="stretch", key="map_ls")
with l2:
    rows = ["| Zug | Art | Kunden | Gewinn | Kosten danach |", "|---|---|---|---|---|"]
    for i, stp in enumerate(steps, start=1):
        mark = "**" if i == step else ""
        rows.append(f"| {mark}{i}{mark} | {stp['kind']} | {' '.join(str(c) for c in stp['customers'])} | {de(stp['gain'])} | {de(stp['cost'])} |")
    st.markdown("\n".join(rows) if steps else "Kein verbessernder Zug.")
kind, text = verdict_ls(info)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Rückschreiben: Lamarck oder Baldwin")
st.caption("Nach der Lokalsuche kann man die verbesserten Routen in die Folge zurückschreiben (Lamarck) oder das Chromosom unverändert lassen und die Lokalsuche nur für die Bewertung nutzen (Baldwin). Beide Läufe: dieselbe Instanz, derselbe Seed, dasselbe Budget.")
lam = {"SL": results["SL"], "SB": _run(settings, "SB", b_ls, m_ls)}
st.plotly_chart(build_curves(lam, ref_cost), width="stretch", key="curves_lamarck")
kind, text = verdict_lamarck(lam)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 5 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wie schlagen sich die Verfahren?")
st.caption("Feste Instanzen, vorberechnet (generate_precomputed.py): die Instanzen der Stücke 4 und 5, vier Zellen (Karte zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke), **ein Lauf je Instanz**; bis 12 Kunden gegen das exakte Optimum, darüber gegen die Referenz PyVRP "
           "(5 Sekunden, ein Seed). Verglichen wird nach gleicher Zahl von Kindern.")
band_n = int(st.radio("Kunden n", list(C.BAND_SIZES), index=1, horizontal=True, key="band_n"))
stats = _band_stats(band_n)
if stats:
    st.caption(f"{instances_word(stats['count'])}. Budget: {C.BAND_BUDGET[band_n][0]} Kinder ohne, {C.BAND_BUDGET[band_n][1]} Kinder mit Lokalsuche. Die Linien zeigen den Median des Abstands zur Referenz (negativ: besser als die Referenz).")
    st.plotly_chart(build_band_curves(stats), width="stretch", key="band_curves")
    ref_name = "Optimum" if band_n <= C.EXACT_MAX else "Referenz"
    table = [f"| Verfahren | Ende: Median | Mittel | Maximum | unter der {ref_name} | Kinder je Sekunde (Hinweis) |", "|---|---|---|---|---|---|"]
    for k in C.ALL_KINDS:
        if k in stats["final"]:
            f = stats["final"][k]
            table.append(f"| **{C.KIND_NAMES[k]}** | {signed_pct(f['median'])} | {signed_pct(f['mean'])} | {signed_pct(f['max'])} | {stats['under'][k]} von {stats['count']} | {de(stats['rate'][k], 0)} |")
    st.markdown("\n".join(table))
    bl = stats["baselines"]
    st.caption("Maßstäbe der Konstruktion (Median / Mittel): " + "; ".join(f"{nm} {pct(bl[k]['median'])} / {pct(bl[k]['mean'])}" for k, nm in (("es", "Einfügen nach Split"), ("sav", "Savings λ = 1"), ("best9", "bestes von 9 λ"))) + ".")
    pr = stats["paired"]
    pairs = ["| Vergleich | billiger / gleich / teurer |", "|---|---|"]
    for key, label in (("S_R_final", "Folge + Split gegen Routen (Ende des Budgets)"), ("SL_RL_final", "Folge + Split + Lokalsuche gegen Routen + Lokalsuche (Ende)"), ("S_R_1000", "Folge + Split gegen Routen nach 1000 Kindern"),
                       ("SL_RL_1000", "mit Lokalsuche, Folge gegen Routen nach 1000 Kindern"), ("SL_S_1000", "Folge: mit gegen ohne Lokalsuche nach 1000 Kindern"), ("RL_R_1000", "Routen: mit gegen ohne Lokalsuche nach 1000 Kindern"),
                       ("SL_SB_final", "Lamarck gegen Baldwin (Ende)")):
        v = pr.get(key)
        if v:
            pairs.append(f"| {label} | {v['cheaper']} / {v['equal']} / {v['more']} |")
    st.markdown("\n".join(pairs))
kind, text = verdict_bands(stats)
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Einfache Operatoren, ein Lauf je Instanz** | Kodierung und Operatoren lassen sich nicht trennen; mit anderen Kreuzungen und Mutationen kann die Rangfolge der einfachen Fassungen anders ausfallen. Ein Lauf hat Zufall | Mehrere Läufe je Instanz (nicht gebaut) |
| **Kein HGS** | Es fehlen Strafen für unzulässige Pläne, Diversitätsmanagement und SWAP*; der Stand der Technik liegt dort, wo PyVRP liegt | PyVRP (Referenz), Stück 15 |
| **Nur Kapazität, keine Zeitfenster** | Mit Fenstern ändert sich die Dekodierung (Stück 8), die Kodierungsfrage bleibt | Stücke 8 und 9 |
| **Zeit in Python** | Die Kinder je Sekunde sind eine Messung dieser Maschine; das Budget ist deshalb die Kinderzahl | – |
| **Referenz PyVRP ab 25 Kunden** | Eine gute Lösung, keine bewiesene Untergrenze; Lösungen mit Lokalsuche liegen teils darunter | – |
| **Keine Flottengrenze** | Die Zahl der Routen ist frei (Stück 3 behandelt die Grenze) | Stück 3 |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Ein Depot $0$, Kunden $1, \dots, n$ mit Nachfragen $q_i$, Kapazität $Q$, euklidische Entfernungen $d_{ij}$. Eine Riesentour $\sigma$ ist eine Permutation der Kunden; $\operatorname{Split}(\sigma)$ ist die Länge des kürzesten Wegs im
Hilfsgraphen mit den Bögen $(i, j)$, falls $\sum_{k=i+1}^{j} q_{\sigma_k} \le Q$, und den Kosten der Route $\sigma_{i+1}, \dots, \sigma_j$ (Stück 1).

**Dominanz.** Zu jedem zulässigen Plan gibt es eine Riesentour, deren Split ihn (oder einen nicht längeren) liefert; das Minimum von $\operatorname{Split}$ über alle Permutationen ist das Optimum. Die Suche über Folgen ist also vollständig.

**Ordnungskreuzung.** Für Eltern $p, p'$ und den Schnitt $[a, b]$: das Kind $c$ hat $c_k = p_k$ für $a \le k \le b$, und die übrigen Plätze werden mit den Kunden außerhalb von $p_{a..b}$ in der Reihenfolge von $p'$ gefüllt.

**Steady State.** Population $\mathcal P$ mit $|\mathcal P| = 30$; je Schritt zwei Eltern durch Turnier (zwei Zufallsmitglieder, das bessere gewinnt), ein Kind (Kreuzung, mit Wahrscheinlichkeit $\mu$ mutiert, bei Lokalsuche verbessert); es ersetzt das schlechteste Mitglied, wenn seine Kosten kleiner sind und
sich von den Kosten jedes Mitglieds unterscheiden.

**Lokalsuche.** 2-opt: ersetze die Kanten $(a, b), (c, d)$ einer Route durch $(a, c), (b, d)$, wenn $d_{ac} + d_{bd} < d_{ab} + d_{cd}$. Verschieben: setze $u$ zwischen $v$ und seinen Nachbarn (in der Route), wenn der Umweg kleiner ist als der Gewinn
beim Herausnehmen und die Kapazität der Zielroute reicht. Tauschen: vertausche $u$ und $v$ aus verschiedenen Routen bei kleinerer Summe der Umwege und eingehaltener Kapazität. Nachbarn: die 8 nächsten Kunden. Erste Verbesserung.

**Lamarck und Baldwin.** Lamarck: das Chromosom wird durch die Folge der verbesserten Routen ersetzt; Baldwin: das Chromosom bleibt, nur die Kosten sind die der verbesserten Routen.

**Literatur.** Folge + Split + Lokalsuche: Prins (2004); Hybrid Genetic Search: Vidal, Crainic, Gendreau und Prins (2013), Vidal (2022); Referenzlöser: PyVRP (Wouda, Lan, Kool). Alle wurden nur als Titel oder Abstract gesehen; die Demo übernimmt keine Zahl daraus.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
