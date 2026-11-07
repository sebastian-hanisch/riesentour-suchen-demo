"""Genetische Suche über Riesentouren (Stück 11 der Linie Tourenbildung): vier Fassungen, dazu die Baldwin-Variante.

Zwei Kodierungen mal zwei Lokalsuchen:
  S   Folge (Riesentour) + Split:  Chromosom = Permutation aller Kunden, Bewertung = optimaler Split; Ordnungskreuzung (OX), Tausch- und Einfüge-Mutation
  SL  Folge + Split + Lokalsuche:  das Kind wird gesplittet, die Routen lokal verbessert (2-opt in der Route, Verschieben und Tauschen zu den nächsten Nachbarn, erste Verbesserung), die verbesserten Routen
                                   werden wieder zu einer Folge zusammengesetzt (Lamarck: das Chromosom wird überschrieben)
  SB  wie SL, aber das Chromosom bleibt die Folge des Kindes; nur die Bewertung nutzt die Lokalsuche (Baldwin)
  R   Routen direkt:               Chromosom = Liste von Routen; Kreuzung: die Hälfte der Routen von Elter A, dazu die Routen von Elter B ohne die schon verteilten Kunden; Mutation: ein Kunde an die
                                   beste zulässige Stelle; Bewertung = Summe der Routenlängen
  RL  Routen + dieselbe Lokalsuche

Alle: Population 30, steady state (ein Kind je Schritt ersetzt das schlechteste Mitglied, wenn es sich in den Kosten von allen unterscheidet und besser ist), Turnierauswahl (2), Kreuzung immer, Mutation mit
der Wahrscheinlichkeit `mut`. Anfangspopulation: zufällige Folgen (S, SL, SB) beziehungsweise zufällige Folgen, „Füllen bis voll“ nach der Last (R, RL); gleiche Kosten werden dort nur begrenzt oft verworfen
(20 mal die Populationsgröße), damit kleine Instanzen mit Lokalsuche nicht endlos nach verschiedenen Kosten suchen. Budget: Zahl der Kinder; die Spur hält die besten Kosten nach festen Kinderzahlen fest.
Alles ist bitgleich bei gleichem Seed (ein eigener Zufallszahlengenerator je Lauf)."""

import math
import random
import time
from dataclasses import dataclass

import rsk_constants as C
from rsk_scenario import Instance, distance_matrix

INF = math.inf


class Prob:
    """Instanz als Listen (schneller als numpy im inneren Schleifenwerk)."""

    def __init__(self, inst: Instance):
        self.inst = inst
        self.n = inst.n
        self.D = [list(map(float, row)) for row in distance_matrix(inst)]
        self.dem = [0] + list(inst.demand)
        self.Q = inst.capacity
        self.near = [[]] + [sorted((c for c in range(1, self.n + 1) if c != u), key=lambda c: (self.D[u][c], c))[:C.NEIGHBORS] for u in range(1, self.n + 1)]


def route_len(P: Prob, r) -> float:
    if not r:
        return 0.0
    D = P.D
    return D[0][r[0]] + sum(D[a][b] for a, b in zip(r, r[1:])) + D[r[-1]][0]


def plan_len(P: Prob, routes) -> float:
    return sum(route_len(P, r) for r in routes)


def split(P: Prob, order):
    """Optimaler Split (Prins): kürzester Weg im Hilfsgraphen. Rückgabe (Kosten, Routen). Gleichstand: der kleinste Startknoten des letzten Bogens gewinnt (nur Verbesserungen um mehr als 1e-12 zählen)."""
    n, D, dem, Q = P.n, P.D, P.dem, P.Q
    best = [INF] * (n + 1)
    pred = [0] * (n + 1)
    best[0] = 0.0
    for i in range(n):
        bi = best[i]
        load, inner = 0, 0.0
        for j in range(i, n):
            c = order[j]
            load += dem[c]
            if load > Q:
                break
            inner = D[0][c] if j == i else inner + D[order[j - 1]][c]
            v = bi + inner + D[c][0]
            if v < best[j + 1] - 1e-12:
                best[j + 1] = v
                pred[j + 1] = i
    routes, node = [], n
    while node > 0:
        routes.append(list(order[pred[node]:node]))
        node = pred[node]
    routes.reverse()
    return best[n], routes


def next_fit(P: Prob, order):
    """„Füllen bis voll“ nach der Last (Stück 3)."""
    out, cur, load = [], [], 0
    for c in order:
        if cur and load + P.dem[c] > P.Q:
            out.append(cur)
            cur, load = [], 0
        cur.append(c)
        load += P.dem[c]
    return out + ([cur] if cur else [])


def is_valid_plan(P: Prob, routes) -> bool:
    """Unabhängiger Prüfer: jeder Kunde genau einmal, keine Route über der Kapazität."""
    seen = sorted(c for r in routes for c in r)
    return seen == list(range(1, P.n + 1)) and all(sum(P.dem[c] for c in r) <= P.Q for r in routes)


# ----------------------------------------------------------------------------------------------------------------------------------------- Lokalsuche

def local_search(P: Prob, routes, max_rounds=50, trace=None):
    """2-opt in jeder Route, dann Verschieben (zu den Nachbarn, in dieselbe oder eine andere Route) und Tauschen (mit einem Nachbarn aus einer anderen Route); erste Verbesserung; bis ein Durchgang nichts mehr
    findet (höchstens `max_rounds` Durchgänge). Arbeitet auf einer Kopie. `trace`: eine Liste, an die je angewendetem Zug ein Wörterbuch (Art, Kunden, Gewinn, Kosten danach, Routen danach) angehängt wird."""
    D, dem, Q = P.D, P.dem, P.Q
    routes = [list(r) for r in routes if r]
    load = [sum(dem[c] for c in r) for r in routes]
    where = {}
    for ri, r in enumerate(routes):
        for pi, c in enumerate(r):
            where[c] = (ri, pi)
    cost = [plan_len(P, routes)]

    def reindex(ri):
        for pi, c in enumerate(routes[ri]):
            where[c] = (ri, pi)

    def note(kind, customers, delta):
        cost[0] += delta
        if trace is not None:
            trace.append({"kind": kind, "customers": tuple(customers), "gain": -delta, "cost": cost[0], "routes": tuple(tuple(r) for r in routes if r)})

    for _ in range(max_rounds):
        improved = False
        for ri, r in enumerate(routes):
            m = len(r)
            if m < 2:
                continue
            path = [0] + r + [0]
            done = False
            while not done:
                done = True
                for i in range(1, m):
                    for j in range(i + 1, m + 1):
                        a, b, c, d = path[i - 1], path[i], path[j], path[j + 1]
                        delta = D[a][c] + D[b][d] - D[a][b] - D[c][d]
                        if delta < -1e-10:
                            path[i:j + 1] = path[i:j + 1][::-1]
                            routes[ri] = path[1:-1]
                            note("2-opt", (b, c), delta)
                            done = False
                            improved = True
            routes[ri] = path[1:-1]
            reindex(ri)
        for u in range(1, P.n + 1):
            ru, pu = where[u]
            r = routes[ru]
            prev_u = r[pu - 1] if pu > 0 else 0
            next_u = r[pu + 1] if pu + 1 < len(r) else 0
            gain = D[prev_u][u] + D[u][next_u] - D[prev_u][next_u]
            moved = False
            for v in P.near[u]:
                rv, pv = where[v]
                if rv != ru and load[rv] + dem[u] > Q:
                    continue
                t = routes[rv]
                for after in (True, False):
                    if rv == ru:
                        rest = r[:pu] + r[pu + 1:]
                        pos = rest.index(v) + (1 if after else 0)
                        a = rest[pos - 1] if pos > 0 else 0
                        b = rest[pos] if pos < len(rest) else 0
                        delta = D[a][u] + D[u][b] - D[a][b] - gain
                        if delta < -1e-10:
                            rest.insert(pos, u)
                            routes[ru] = rest
                            reindex(ru)
                            note("Verschieben", (u,), delta)
                            improved = moved = True
                            break
                    else:
                        pos = pv + (1 if after else 0)
                        a = t[pos - 1] if pos > 0 else 0
                        b = t[pos] if pos < len(t) else 0
                        delta = D[a][u] + D[u][b] - D[a][b] - gain
                        if delta < -1e-10:
                            r.pop(pu)
                            t.insert(pos, u)
                            load[ru] -= dem[u]
                            load[rv] += dem[u]
                            reindex(ru)
                            reindex(rv)
                            note("Verschieben", (u,), delta)
                            improved = moved = True
                            break
                if moved:
                    break
            if moved:
                continue
            ru, pu = where[u]
            r = routes[ru]
            for v in P.near[u]:
                rv, pv = where[v]
                if rv == ru:
                    continue
                if load[ru] - dem[u] + dem[v] > Q or load[rv] - dem[v] + dem[u] > Q:
                    continue
                t = routes[rv]
                pu_prev = r[pu - 1] if pu > 0 else 0
                pu_next = r[pu + 1] if pu + 1 < len(r) else 0
                pv_prev = t[pv - 1] if pv > 0 else 0
                pv_next = t[pv + 1] if pv + 1 < len(t) else 0
                delta = (D[pu_prev][v] + D[v][pu_next] - D[pu_prev][u] - D[u][pu_next]) + (D[pv_prev][u] + D[u][pv_next] - D[pv_prev][v] - D[v][pv_next])
                if delta < -1e-10:
                    r[pu], t[pv] = v, u
                    load[ru] += dem[v] - dem[u]
                    load[rv] += dem[u] - dem[v]
                    where[u], where[v] = (rv, pv), (ru, pu)
                    note("Tauschen", (u, v), delta)
                    improved = True
                    break
        alive = [r for r in routes if r]
        if len(alive) != len(routes):
            routes = alive
            load = [sum(dem[c] for c in r) for r in routes]
            for ri in range(len(routes)):
                reindex(ri)
        if not improved:
            break
    return [r for r in routes if r]


# ----------------------------------------------------------------------------------------------------------------------------------------- Operatoren

def ox(rng: random.Random, p1, p2, cut=None):
    """Ordnungskreuzung (OX): das Teilstück a bis b (einschließlich, 0-basiert) von p1 bleibt an seinen Plätzen, der Rest wird in der Reihenfolge von p2 aufgefüllt. `cut` (a, b) legt den Schnitt fest."""
    n = len(p1)
    if n < 2:
        return list(p1)
    a, b = cut if cut is not None else sorted(rng.sample(range(n), 2))
    child = [None] * n
    child[a:b + 1] = p1[a:b + 1]
    used = set(p1[a:b + 1])
    fill = [c for c in p2 if c not in used]
    k = 0
    for i in range(n):
        if child[i] is None:
            child[i] = fill[k]
            k += 1
    return child


def mutate_seq(rng: random.Random, s):
    """Tauschen zweier Plätze oder Verschieben eines Kunden an eine andere Stelle (je mit Wahrscheinlichkeit 1/2)."""
    s = s[:]
    n = len(s)
    if n < 2:
        return s
    if rng.random() < 0.5:
        i, j = rng.sample(range(n), 2)
        s[i], s[j] = s[j], s[i]
    else:
        i = rng.randrange(n)
        c = s.pop(i)
        s.insert(rng.randrange(n), c)
    return s


def route_crossover(rng: random.Random, a_routes, b_routes):
    """Die Hälfte der Routen von A (mindestens eine), dazu die Routen von B ohne die schon verteilten Kunden."""
    k = max(1, len(a_routes) // 2)
    take = rng.sample(range(len(a_routes)), k)
    chosen = [list(a_routes[i]) for i in take]
    got = {c for r in chosen for c in r}
    rest = [[c for c in r if c not in got] for r in b_routes]
    return chosen + [r for r in rest if r]


def mutate_routes(P: Prob, rng: random.Random, routes):
    """Einen Kunden an die beste zulässige Stelle verschieben (in eine neue Route, wenn nirgends Platz ist oder der Umweg mehr als zweimal die Fahrt zum Depot beträgt)."""
    routes = [list(r) for r in routes]
    ri = rng.randrange(len(routes))
    r = routes[ri]
    u = r.pop(rng.randrange(len(r)))
    best = None
    load = [sum(P.dem[c] for c in t) for t in routes]
    D = P.D
    for tj, t in enumerate(routes):
        if load[tj] + P.dem[u] > P.Q:
            continue
        for pos in range(len(t) + 1):
            a = t[pos - 1] if pos > 0 else 0
            b = t[pos] if pos < len(t) else 0
            d = D[a][u] + D[u][b] - D[a][b]
            if best is None or d < best[0]:
                best = (d, tj, pos)
    if best is None or best[0] > 2 * D[0][u]:
        routes.append([u])
    else:
        routes[best[1]].insert(best[2], u)
    return [t for t in routes if t]


# ----------------------------------------------------------------------------------------------------------------------------------------- Lauf

@dataclass(frozen=True)
class Result:
    cost: float
    routes: tuple
    trace: tuple                 # ((Kinder, beste Kosten), ...) nach den festen Kinderzahlen (CHECKPOINTS, höchstens bis `children`), dazu am Ende (children, Kosten)
    seconds: float               # Gesamtzeit des Laufs (Hinweis, nie festgeschrieben)
    init_seconds: float          # Zeit der Anfangspopulation (Hinweis)
    children: int


def mutation_default(kind: str) -> float:
    return C.MUT_LS if C.HAS_LS[kind] else C.MUT_PLAIN


def run(P: Prob, kind: str, children: int, seed: int, mut: float | None = None, pop_size: int = C.POP_SIZE, checkpoints=C.CHECKPOINTS) -> Result:
    """Ein Lauf der Fassung `kind` mit `children` Kindern. Rückgabe: beste Kosten und Routen, Spur nach Kinderzahlen, Zeiten."""
    mut = mutation_default(kind) if mut is None else mut
    rng = random.Random(seed)
    t0 = time.time()
    use_ls = C.HAS_LS[kind]
    seq = kind in ("S", "SL", "SB")
    baldwin = kind == "SB"
    best_info = [INF, None]                         # beste Routen aller bewerteten Kinder (bei Baldwin trägt das Chromosom die Routen nicht)

    def make(ind):
        """Bewertet ein Chromosom und gibt (Kosten, Chromosom) zurück; bei Lokalsuche werden die Routen verbessert."""
        if seq:
            cost, routes = split(P, ind)
        else:
            routes, cost = ind, None
        if use_ls:
            routes = local_search(P, routes)
            lc = plan_len(P, routes)
            if lc < best_info[0]:
                best_info[0], best_info[1] = lc, routes
        if seq:
            if use_ls:
                return plan_len(P, routes), (ind if baldwin else [c for r in routes for c in r])
            return cost, ind
        return plan_len(P, routes), routes

    pop = []                                        # (Kosten, Chromosom)
    seen = set()
    tries = 0
    while len(pop) < pop_size:
        perm = list(range(1, P.n + 1))
        rng.shuffle(perm)
        ind = perm if seq else next_fit(P, perm)
        cost, chrom = make(ind)
        key = round(cost, 9)
        tries += 1
        if key in seen and tries < 20 * pop_size:
            continue
        seen.add(key)
        pop.append((cost, chrom))
    init_seconds = time.time() - t0
    trace = []
    best = min(p[0] for p in pop)
    marks = [c for c in checkpoints if c <= children]
    for child_no in range(1, children + 1):
        def pick():
            if len(pop) < 2:
                return pop[0]
            a, b = rng.sample(range(len(pop)), 2)
            return pop[a] if pop[a][0] <= pop[b][0] else pop[b]
        pa, pb = pick(), pick()
        if seq:
            ch = ox(rng, pa[1], pb[1])
            if rng.random() < mut:
                ch = mutate_seq(rng, ch)
        else:
            ch = route_crossover(rng, pa[1], pb[1])
            if rng.random() < mut:
                ch = mutate_routes(P, rng, ch)
        cost, chrom = make(ch)
        key = round(cost, 9)
        worst = max(range(len(pop)), key=lambda i: pop[i][0])
        if key not in {round(p[0], 9) for p in pop} and cost < pop[worst][0]:
            pop[worst] = (cost, chrom)
        best = min(best, cost)
        if child_no in marks:
            trace.append((child_no, best))
    if not trace or trace[-1][0] != children:
        trace.append((children, best))
    bc, bch = min(pop, key=lambda p: p[0])
    routes = split(P, bch)[1] if seq else bch
    if baldwin:
        bc, routes = best_info
    return Result(float(bc), tuple(tuple(r) for r in routes), tuple(trace), time.time() - t0, init_seconds, children)


def cost_at(result: Result, children: int):
    """Beste Kosten nach `children` Kindern (nur an gespeicherten Kinderzahlen), sonst None."""
    for k, c in result.trace:
        if k == children:
            return c
    return None
