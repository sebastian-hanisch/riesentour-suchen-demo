"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import rsk_constants as C
from rsk_evaluation import Analysis, Settings, de, gap_percent, pct, reference

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2", "λ": "lambda"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, a: Analysis, results: dict) -> bytes:
    inst = a.inst
    ref, label = reference(a, results)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Riesentour suchen"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    where = "Handinstanz (6 Kunden)" if s.family == C.HAND_FAMILY else f"{s.n} Kunden, Karte: {C.FAMILIES[s.family]}, Depot: {C.DEPOTS[s.depot].lower()}, Zielroutenzahl {s.routes}, Auslastung {s.fill} %"
    pdf.multi_cell(0, 5, _s(f"{where}, Seed {s.seed}. Kapazität {inst.capacity}, Gesamtnachfrage {sum(inst.demand)}. Alles simuliert. Referenz: {label}, {de(ref)}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    widths = (78, 28, 36, 20, 22)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(widths, ("Verfahren", "Gesamtlänge", "Abstand zur Referenz", "Routen", "Kinder")):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    rows = [(f"Konstruktion: {nm}", v[0], len(v[1]), "-") for nm, v in (("Einfügen nach Split", a.baselines["es"]), ("Savings lambda = 1", a.baselines["sav"]), ("bestes von 9 lambda", a.baselines["best9"]))]
    rows += [(C.KIND_NAMES[k], r.cost, len(r.routes), str(r.children)) for k, r in results.items()]
    for name, cost, k, ch in rows:
        for w, v in zip(widths, (name, de(cost), pct(gap_percent(cost, ref)), str(k), ch)):
            pdf.cell(w, 5.5, _s(v), border=1)
        pdf.ln()
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Verglichen wird nach gleicher Zahl von Kindern (Bewertungen), nicht nach Zeit. Ein Lauf je Verfahren; kein HGS. Quelle: riesentour-suchen-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
