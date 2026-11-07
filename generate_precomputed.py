"""Erzeugt rsk_bands.json: die Bänder über feste Instanzen (genetische Suche über Riesentouren: Folge + Split und Routen, mit und ohne Lokalsuche, dazu Baldwin).

Die Instanzen und Referenzen stammen aus svv_bands.json der savings-varianten-demo (Stück 5, Ordner daneben): je Größe (12, 25, 50, 100 Kunden) die ersten 5, 4, 4, 2 Instanzen jeder der vier Zellen
(Karte zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke), drei Zielrouten, Auslastung 90 %; Referenz = exaktes Optimum bis 12 Kunden, PyVRP 0.14.1 (5 Sekunden, ein Seed) darüber; dazu die Kosten
von Einfügen nach Split, Savings λ = 1 und bestes von 9 λ (aus derselben Datei). Je Instanz und Fassung ein Lauf mit Seed gleich Instanzseed und festem Kinderbudget (BAND_BUDGET), Spur nach Kinderzahlen.
Die Zeiten stehen als Hinweis in den Zeilen und werden nie geprüft.

Aufruf (Teile können parallel laufen):
    python generate_precomputed.py runs 50 SL --out parts/part_50_SL.json     # Größe, Fassung
    python generate_precomputed.py merge parts/part_*.json                    # zu rsk_bands.json zusammenführen"""

import argparse
import json
import time
from pathlib import Path

import rsk_constants as C
import rsk_search as G
from rsk_scenario import make_instance

TARGET = Path(__file__).with_name(C.BAND_FILE)
SOURCE = Path(__file__).resolve().parent.parent / "savings-varianten-demo" / C.SOURCE_BANDS_FILE


def source_rows(n: int):
    """Die Instanzzeilen der Größe n: (Familie, Depot, Seed, Referenz, Einfügen nach Split, Savings λ = 1, bestes von 9 λ), Zellen in der Reihenfolge von BAND_CELLS."""
    cells = {(c["family"], c["depot"]): c for c in json.loads(SOURCE.read_text(encoding="utf-8"))["cells"] if c["n"] == n and c["fill"] == C.BAND_FILL and c["routes"] == C.BAND_ROUTES}
    out = []
    for cell in C.BAND_CELLS:
        for r in cells[cell]["rows"][:C.BAND_PER_CELL[n]]:
            out.append((cell[0], cell[1], r["seed"], r["ref"], r["es"], r["par"]["1.0"], min(r["par"].values())))
    return out


def build(n: int, kind: str) -> list[dict]:
    rows, start = [], time.time()
    budget = C.BAND_BUDGET[n][1 if C.HAS_LS[kind] else 0]
    for family, depot, seed, ref, es, sav, best9 in source_rows(n):
        P = G.Prob(make_instance(n, family, depot, C.BAND_ROUTES, seed, C.BAND_FILL))
        res = G.run(P, kind, budget, seed)
        assert G.is_valid_plan(P, [list(r) for r in res.routes])
        rows.append({"n": n, "family": family, "depot": depot, "seed": seed, "ref": ref, "es": es, "sav": sav, "best9": best9,
                     "kind": kind, "cost": res.cost, "children": res.children, "trace": [list(t) for t in res.trace], "seconds": round(res.seconds, 2), "init_seconds": round(res.init_seconds, 3)})
        print("runs", n, kind, seed, f"{time.time() - start:.0f} s", flush=True)
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["runs", "merge"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.kind == "merge":
        flat = []
        for f in args.args:
            flat += json.loads(Path(f).read_text(encoding="utf-8"))["rows"]
        grouped = {}
        for r in flat:
            key = (r["n"], r["family"], r["depot"], r["seed"])
            row = grouped.setdefault(key, {k: r[k] for k in ("n", "family", "depot", "seed", "ref", "es", "sav", "best9")} | {"runs": {}})
            row["runs"][r["kind"]] = {k: r[k] for k in ("cost", "children", "trace", "seconds", "init_seconds")}
        cell_order = {cell: i for i, cell in enumerate(C.BAND_CELLS)}
        rows = sorted(grouped.values(), key=lambda r: (r["n"], cell_order[(r["family"], r["depot"])], r["seed"]))
        meta = {"budget": {str(n): {"ohne Lokalsuche": b[0], "mit Lokalsuche": b[1]} for n, b in C.BAND_BUDGET.items()}, "per_cell": {str(n): v for n, v in C.BAND_PER_CELL.items()},
                "mutation": {"ohne Lokalsuche": C.MUT_PLAIN, "mit Lokalsuche": C.MUT_LS}, "population": C.POP_SIZE, "checkpoints": list(C.CHECKPOINTS),
                "source": f"Instanzen und Referenzen aus {C.SOURCE_BANDS_FILE} (savings-varianten-demo, Stück 5); Referenz bis 12 Kunden exakt, darüber PyVRP (5 s, ein Seed)"}
        TARGET.write_text(json.dumps({"meta": meta, "rows": rows}, ensure_ascii=False), encoding="utf-8")
        print("geschrieben:", TARGET.name, len(rows), "Zeilen")
    else:
        Path(args.out).write_text(json.dumps({"rows": build(int(args.args[0]), args.args[1])}, ensure_ascii=False), encoding="utf-8")
        print("geschrieben:", args.out)
