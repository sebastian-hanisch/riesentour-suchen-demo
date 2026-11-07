"""Kennzahlen, Verdikt-Logik und Bänder. Verdikte sind reine Funktionen (Art, Text): die App ruft st.<Art>(Text), die Tests prüfen jede Zahl im Text."""

import json
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import mean, median

import rsk_algorithm as A
import rsk_constants as C
import rsk_construct as K
import rsk_savings as S
import rsk_search as G
from rsk_scenario import Instance, make_instance


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    family: int = C.DEFAULT_FAMILY
    depot: int = C.DEFAULT_DEPOT
    routes: int = C.DEFAULT_ROUTES
    fill: int = C.DEFAULT_FILL
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True, eq=False)
class Analysis:
    settings: Settings
    inst: Instance
    exact: object                        # ExactResult (bis 12 Kunden) oder None
    baselines: dict                      # Schlüssel (es, sav, best9) -> (Kosten, Routen): Maßstäbe der Konstruktion


# ----------------------------------------------------------------------------------------------------------------------------------- Formate

def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    return f"{de(x, digits)} %"


def signed_pct(x: float, digits: int = 1) -> str:
    """Mit Vorzeichen (echtes Minus); -0,0 wird zu 0,0."""
    text = de(abs(x), digits)
    if float(text.replace(",", ".")) == 0.0:
        return f"{text} %"
    return f"{'+' if x > 0 else '−'}{text} %"


def routes_word(k: int) -> str:
    return f"{k} Route" if k == 1 else f"{k} Routen"


def instances_word(k: int) -> str:
    return f"{k} Instanz" if k == 1 else f"{k} Instanzen"


def gap_percent(cost: float, reference: float) -> float:
    """Abstand zur Referenz in Prozent der Referenz, vorzeichenbehaftet (eine Lösung kann eine nicht bewiesen optimale Referenz unterbieten); innerhalb der Toleranz 0."""
    if reference <= 0 or abs(cost - reference) <= C.TOL:
        return 0.0
    return 100.0 * (cost - reference) / reference


def order_text(order) -> str:
    return " ".join(str(c) for c in order)


def routes_text(routes) -> str:
    return " ‖ ".join("(" + order_text(r) + ")" for r in routes)


# ----------------------------------------------------------------------------------------------------------------------------------- Instanz und Maßstäbe

def hand_instance() -> Instance:
    return Instance(C.HAND_XY, C.HAND_DEMAND, C.HAND_CAPACITY)


def build_instance(s: Settings) -> Instance:
    if s.family == C.HAND_FAMILY:
        return hand_instance()
    return make_instance(s.n, s.family, s.depot, s.routes, s.seed, s.fill)


def analyse(s: Settings) -> Analysis:
    inst = build_instance(s)
    exact = A.exact_cvrp(inst) if inst.n <= C.EXACT_MAX else None
    es = K.insert_split_order(inst)
    es_plan = A.split(inst, es)
    sav = S.savings_routes(inst)
    plans9 = [S.savings_routes(inst, S.Params(lam=lam)) for lam in S.LAMS]
    b9 = min(plans9, key=lambda r: A.plan_length(inst, r))
    return Analysis(s, inst, exact, {"es": (es_plan.cost, es_plan.routes), "sav": (A.plan_length(inst, sav), sav), "best9": (A.plan_length(inst, b9), b9)})


def reference(a: Analysis, results: dict) -> tuple[float, str]:
    """Referenzkosten: bis 12 Kunden das exakte Optimum, darüber die beste Lösung dieser Seite (Maßstäbe und Läufe), ausdrücklich keine Untergrenze."""
    if a.exact is not None:
        return a.exact.cost, "exaktes Optimum"
    best = min([v[0] for v in a.baselines.values()] + [r.cost for r in results.values()])
    return best, "beste Lösung dieser Seite (keine Untergrenze)"


def run_kind(s: Settings, kind: str, children: int, mut: float | None) -> G.Result:
    inst = build_instance(s)
    return G.run(G.Prob(inst), kind, children, s.seed, mut)


# ----------------------------------------------------------------------------------------------------------------------------------- Kreuzung (Experiment 1)

def parent(inst: Instance, seed: int) -> tuple[int, ...]:
    """Eine Eltern-Folge aus einem Seed (zufällige Mischung der Kunden)."""
    order = list(range(1, inst.n + 1))
    random.Random(seed).shuffle(order)
    return tuple(order)


def crossover_view(s: Settings, seed_a: int, seed_b: int, cut: tuple[int, int]) -> dict:
    """Zwei Eltern, ihr Kind nach OX mit dem Schnitt `cut` (0-basiert, einschließlich) und der Split aller drei; dazu über alle Schnitte, wie oft das Kind beide Eltern schlägt."""
    inst = build_instance(s)
    P = G.Prob(inst)
    pa, pb = parent(inst, seed_a), parent(inst, seed_b)
    rng = random.Random(0)

    def ev(order):
        cost, routes = G.split(P, order)
        return {"order": tuple(order), "cost": cost, "routes": tuple(tuple(r) for r in routes)}

    out = {"a": ev(pa), "b": ev(pb), "child": ev(G.ox(rng, list(pa), list(pb), cut)), "cut": cut}
    n = inst.n
    better = total = equal = 0
    for i in range(n):
        for j in range(i, n):
            c = G.split(P, G.ox(rng, list(pa), list(pb), (i, j)))[0]
            total += 1
            if c < min(out["a"]["cost"], out["b"]["cost"]) - C.TOL:
                better += 1
            elif abs(c - min(out["a"]["cost"], out["b"]["cost"])) <= C.TOL:
                equal += 1
    out["cuts"] = {"total": total, "better": better, "equal": equal}
    return out


# ----------------------------------------------------------------------------------------------------------------------------------- Lokalsuche Schritt für Schritt (Experiment 3)

def start_plan(s: Settings, start: str):
    """Ausgangsplan der Lokalsuche: „es“ (Einfügen nach Split), „sav“ (Savings λ = 1) oder „random“ (zufällige Folge + Split, Seed der Instanz)."""
    inst = build_instance(s)
    if start == "es":
        return A.split(inst, K.insert_split_order(inst)).routes
    if start == "sav":
        return S.savings_routes(inst)
    order = list(range(1, inst.n + 1))
    random.Random(s.seed).shuffle(order)
    return A.split(inst, order).routes


def ls_steps(s: Settings, start: str) -> dict:
    inst = build_instance(s)
    P = G.Prob(inst)
    routes0 = [list(r) for r in start_plan(s, start)]
    trace: list = []
    final = G.local_search(P, routes0, trace=trace)
    return {"start": tuple(tuple(r) for r in routes0), "start_cost": G.plan_len(P, routes0), "steps": trace, "final": tuple(tuple(r) for r in final), "final_cost": G.plan_len(P, final)}


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

@lru_cache(maxsize=1)
def load_bands() -> dict:
    """Vorberechnete Bänder (generate_precomputed.py); {} wenn die Datei fehlt."""
    path = Path(__file__).with_name(C.BAND_FILE)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def band_rows(n: int) -> list[dict]:
    return [r for r in load_bands().get("rows", []) if r["n"] == n]


def budget_of(n: int, kind: str) -> int:
    return C.BAND_BUDGET[n][1 if C.HAS_LS[kind] else 0]


def run_at(row: dict, kind: str, children: int | None = None):
    """Beste Kosten des Laufs `kind` einer Zeile nach `children` Kindern (None: am Ende des Budgets); None, wenn dort keine Spur steht."""
    run = row["runs"][kind]
    if children is None:
        return run["cost"]
    for k, c in run["trace"]:
        if k == children:
            return c
    return None


def spread(values: list[float]) -> dict:
    return {"min": min(values), "median": median(values), "mean": mean(values), "max": max(values), "count": len(values)}


def paired(a: list[float], b: list[float]) -> dict:
    """Gepaarter Vergleich: a billiger / gleich / teurer als b."""
    cheaper = sum(x < y - C.TOL for x, y in zip(a, b))
    more = sum(x > y + C.TOL for x, y in zip(a, b))
    return {"count": len(a), "cheaper": cheaper, "equal": len(a) - cheaper - more, "more": more}


def band_stats(rows: list[dict]) -> dict:
    """Alle Kennzahlen einer Größe: Abstand der Verfahren zur Referenz nach festen Kinderzahlen und am Ende des Budgets, Maßstäbe, gepaarte Zählungen, Durchsatz."""
    if not rows:
        return {}
    n = rows[0]["n"]
    ref = [r["ref"] for r in rows]
    out = {"count": len(rows), "n": n, "baselines": {k: spread([gap_percent(r[k], r["ref"]) for r in rows]) for k in ("es", "sav", "best9")}, "final": {}, "at": {}, "under": {}, "rate": {}, "init": {}, "paired": {}}
    for kind in C.ALL_KINDS:
        if not all(kind in r["runs"] for r in rows):
            continue
        out["final"][kind] = spread([gap_percent(r["runs"][kind]["cost"], r["ref"]) for r in rows])
        out["under"][kind] = sum(r["runs"][kind]["cost"] < r["ref"] - 1e-9 for r in rows)
        out["rate"][kind] = median(r["runs"][kind]["children"] / max(r["runs"][kind]["seconds"], 1e-9) for r in rows)
        out["init"][kind] = median(r["runs"][kind]["init_seconds"] for r in rows)
        for k in C.CHECKPOINTS:
            vals = [run_at(r, kind, k) for r in rows]
            if all(v is not None for v in vals):
                out["at"].setdefault(kind, {})[k] = spread([gap_percent(v, ref_) for v, ref_ in zip(vals, ref)])

    def pair(ka, kb, at=None):
        a = [run_at(r, ka, at) for r in rows]
        b = [run_at(r, kb, at) for r in rows]
        return paired(a, b)
    out["paired"] = {
        "S_R_final": pair("S", "R"), "SL_RL_final": pair("SL", "RL"), "SL_S_1000": pair("SL", "S", 1000), "RL_R_1000": pair("RL", "R", 1000),
        "S_R_1000": pair("S", "R", 1000), "SL_RL_1000": pair("SL", "RL", 1000), "SL_SB_final": pair("SL", "SB") if all("SB" in r["runs"] for r in rows) else None,
    }
    return out


# ----------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_cross(view: dict) -> tuple[str, str]:
    """Verdikt zur Kreuzung: Kind gegen Eltern, und wie oft ein Schnitt ein besseres Kind liefert."""
    a, b, ch, cuts = view["a"], view["b"], view["child"], view["cuts"]
    best_parent = min(a["cost"], b["cost"])
    head = (f"Eltern A kostet {de(a['cost'])} ({routes_word(len(a['routes']))}), Eltern B {de(b['cost'])} ({routes_word(len(b['routes']))}); das Kind kostet {de(ch['cost'])} ({routes_word(len(ch['routes']))}). "
            f"Von {cuts['total']} Schnitten liefern {cuts['better']} ein Kind, das beide Eltern schlägt, {cuts['equal']} eines, das so gut ist wie der bessere Elter.")
    if ch["cost"] < best_parent - C.TOL:
        return "success", "Das Kind ist besser als beide Eltern. " + head
    if abs(ch["cost"] - best_parent) <= C.TOL:
        return "info", "Das Kind ist so gut wie der bessere Elter. " + head
    return "warning", "Das Kind ist schlechter als der bessere Elter. " + head


def verdict_runs(a: Analysis, results: dict) -> tuple[str, str]:
    """Verdikt zu den vier Läufen: Abstand zur Referenz, wer vorn liegt."""
    ref, label = reference(a, results)
    parts = [f"{C.KIND_NAMES[k]} {pct(gap_percent(r.cost, ref))}" for k, r in results.items()]
    best = min(results, key=lambda k: (results[k].cost, list(results).index(k)))
    text = f"Abstand zur Referenz ({label}, {de(ref)}) nach dem Budget: " + "; ".join(parts) + f". Am besten: {C.KIND_NAMES[best]} ({de(results[best].cost)})."
    if a.exact is None:
        text += " Ab 13 Kunden ist die Referenz keine Untergrenze: ein Wert unter null heißt nur, dass ein Lauf besser war als alle anderen Verfahren dieser Seite."
    return "info", text


def verdict_ls(info: dict) -> tuple[str, str]:
    """Verdikt zur Lokalsuche an einem Plan."""
    steps = info["steps"]
    kinds = {}
    for st in steps:
        kinds[st["kind"]] = kinds.get(st["kind"], 0) + 1
    if not steps:
        return "info", f"Die Lokalsuche findet in diesem Plan (Kosten {de(info['start_cost'])}) keinen verbessernden Zug."
    mix = ", ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
    over = gap_percent(info["start_cost"], info["final_cost"])
    return "success", (f"{len(steps)} Züge ({mix}) senken die Kosten von {de(info['start_cost'])} auf {de(info['final_cost'])}: der Ausgangsplan war {pct(over)} länger als das Ergebnis. "
                       f"Die Routenzahl ändert sich von {len(info['start'])} auf {len(info['final'])}.")


def verdict_lamarck(results: dict) -> tuple[str, str]:
    sl, sb = results["SL"], results["SB"]
    if sl.cost < sb.cost - C.TOL:
        word, kind = "Das Rückschreiben (Lamarck) liefert hier den besseren Plan", "success"
    elif abs(sl.cost - sb.cost) <= C.TOL:
        word, kind = "Beide Fassungen enden gleich", "info"
    else:
        word, kind = "Bei diesem Seed ist die Fassung ohne Rückschreiben (Baldwin) besser", "warning"
    return kind, f"{word}: Lamarck {de(sl.cost)} ({routes_word(len(sl.routes))}), Baldwin {de(sb.cost)} ({routes_word(len(sb.routes))}). Ein Lauf sagt wenig; die Bänder zählen über viele Instanzen."


def verdict_bands(stats: dict) -> tuple[str, str]:
    """Bänder einer Größe: Folge gegen Routen mit und ohne Lokalsuche."""
    if not stats:
        return "warning", "Für diese Größe liegen keine Bänder vor."
    n, cnt = stats["n"], stats["count"]
    f, p = stats["final"], stats["paired"]
    ref = "Optimum" if n <= C.EXACT_MAX else "Referenz (PyVRP)"
    b_plain, b_ls = C.BAND_BUDGET[n]
    text = (f"{n} Kunden, {instances_word(cnt)}, Abstand zum {ref} (Median): ohne Lokalsuche nach {b_plain} Kindern Folge + Split {pct(f['S']['median'])}, Routen {pct(f['R']['median'])}; "
            f"mit Lokalsuche nach {b_ls} Kindern Folge + Split {pct(f['SL']['median'])}, Routen {pct(f['RL']['median'])}. "
            f"Mit Lokalsuche Folge gegen Routen billiger / gleich / teurer: {p['SL_RL_final']['cheaper']} / {p['SL_RL_final']['equal']} / {p['SL_RL_final']['more']}.")
    if n > C.EXACT_MAX:
        text += " Die Referenz ist keine bewiesene Untergrenze."
    text += " Ein Lauf je Instanz."
    gap_ls = f["SL"]["median"] - f["RL"]["median"]
    kind = "success" if gap_ls < -C.LEVEL_PP else "info"
    return kind, text
