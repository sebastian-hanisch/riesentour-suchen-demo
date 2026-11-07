"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import rsk_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(inst, routes, title_prefix="Route", rays=None, start_ray=None, legend=True):
    """Karte: Depot als Quadrat, Kunden als Kreise (Größe = Nachfrage, Beschriftung = Nummer), jede Route eine Farbe. `rays`: Winkel (Bogenmaß) der Schnitte zwischen den Clustern als gestrichelte
    Strahlen vom Depot, `start_ray`: Winkel des Startkunden (durchgezogener grauer Strahl). Gleicher Maßstab in x und y über scaleanchor mit autorange; der Rand kommt von zwei unsichtbaren Eckmarken."""
    xs = [p[0] for p in inst.xy]
    ys = [p[1] for p in inst.xy]
    pad = 0.08 * max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys) - pad, max(ys) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    reach = 1.15 * max(math.dist(inst.xy[0], p) for p in inst.xy[1:]) if inst.n else 1.0
    for angle, dash, name in [(a, "dot", "Schnitt") for a in (rays or [])] + ([(start_ray, "solid", "Start")] if start_ray is not None else []):
        fig.add_trace(go.Scatter(x=[inst.xy[0][0], inst.xy[0][0] + reach * math.cos(angle)], y=[inst.xy[0][1], inst.xy[0][1] + reach * math.sin(angle)], mode="lines",
                                 line=dict(color="rgba(120,120,120,0.55)", width=1.5, dash=dash), hoverinfo="skip", showlegend=False))
    for r, route in enumerate(routes):
        pts = [inst.xy[0]] + [inst.xy[c] for c in route] + [inst.xy[0]]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color=C.ROUTE_COLORS[r % len(C.ROUTE_COLORS)], width=3),
                                 name=f"{title_prefix} {r + 1} (Last {inst.load(route)} von {inst.capacity})", hoverinfo="skip"))
    customers = list(range(1, inst.n + 1))
    fig.add_trace(go.Scatter(
        x=[inst.xy[c][0] for c in customers], y=[inst.xy[c][1] for c in customers], mode="markers+text", text=[str(c) for c in customers], textposition="top center",
        marker=dict(size=[9 + 2.5 * inst.demand[c - 1] for c in customers], color="rgba(150,150,150,0.55)", line=dict(color="#555", width=1)),
        customdata=[[inst.demand[c - 1]] for c in customers], hovertemplate="Kunde %{text}: Nachfrage %{customdata[0]}<extra></extra>", name="Kunden (Größe = Nachfrage)"))
    fig.add_trace(go.Scatter(x=[inst.xy[0][0]], y=[inst.xy[0][1]], mode="markers", marker=dict(symbol="square", size=15, color="#222"), name="Depot", hoverinfo="skip"))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig = _base(fig, 380 if legend else 300)
    if not legend:
        fig.update_layout(showlegend=False)
    return fig


def build_curves(results, reference, baselines=None):
    """Beste Kosten nach der Kinderzahl für jede Fassung (logarithmische x-Achse); Linien: Referenz und die Maßstäbe der Konstruktion (Einfügen nach Split, Savings, bestes von 9 λ)."""
    fig = go.Figure()
    for kind, res in results.items():
        fig.add_trace(go.Scatter(x=[k for k, _ in res.trace], y=[c for _, c in res.trace], mode="lines+markers", name=C.KIND_NAMES[kind], line=dict(color=C.KIND_COLORS[kind], width=3), marker=dict(size=7),
                                 hovertemplate="%{x} Kinder: %{y:.2f}<extra>" + C.KIND_NAMES[kind] + "</extra>"))
    fig.add_hline(y=reference, line=dict(color=C.COLOR_REF, width=1.5, dash="dot"), annotation_text=f"Referenz {reference:.2f}", annotation_position="top left", annotation_font_size=11)
    for name, (cost, _) in (baselines or {}).items():
        fig.add_hline(y=cost, line=dict(color="rgba(120,120,120,0.6)", width=1, dash="dash"), annotation_text=name, annotation_position="bottom right", annotation_font_size=10)
    fig.update_xaxes(title_text="Kinder (Bewertungen)", type="log")
    fig.update_yaxes(title_text="Beste Gesamtlänge")
    fig = _base(fig, 400)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=60), legend=dict(orientation="h", y=-0.3))
    return fig


def build_band_curves(stats, kinds=None, title="Abstand zur Referenz (Median, %)"):
    """Median-Abstand zur Referenz nach festen Kinderzahlen je Fassung (logarithmische x-Achse); die Maßstäbe der Konstruktion als waagerechte Linien."""
    fig = go.Figure()
    for kind in (kinds or C.ALL_KINDS):
        pts = stats["at"].get(kind)
        if not pts:
            continue
        xs = sorted(pts)
        fig.add_trace(go.Scatter(x=xs, y=[pts[k]["median"] for k in xs], mode="lines+markers", name=C.KIND_NAMES[kind], line=dict(color=C.KIND_COLORS[kind], width=3), marker=dict(size=7),
                                 hovertemplate="%{x} Kinder: %{y:.1f} %<extra>" + C.KIND_NAMES[kind] + "</extra>"))
    for key, name in (("es", "Einfügen nach Split"), ("best9", "bestes von 9 λ")):
        fig.add_hline(y=stats["baselines"][key]["median"], line=dict(color="rgba(120,120,120,0.6)", width=1, dash="dash"), annotation_text=name, annotation_position="top right", annotation_font_size=10)
    fig.update_xaxes(title_text="Kinder (Bewertungen)", type="log")
    fig.update_yaxes(title_text=title)
    fig = _base(fig, 400)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=60), legend=dict(orientation="h", y=-0.3))
    return fig
