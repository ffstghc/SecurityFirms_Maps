"""Static maps and charts (matplotlib, PNG).

Colours follow one rule per job: a diverging blue/red ramp with a grey midpoint
for "index vs. average", a single-hue blue ramp for magnitudes, and three
validated category colours for the priority segments. Every map labels its
areas (or ships a CSV table next to it), so no value relies on colour alone.
"""

from __future__ import annotations

import logging
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Polygon  # noqa: E402

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"
NONE = "#f7f6f3"  # no value: near-surface fill, always drawn with a light hatch
NONE_HATCH = "////"

# index vs. average: red = below (thin supply), grey = about average, blue = above
DIVERGING = ["#a32f2f", "#d65b55", "#ef9f97", "#f0efec", "#9ec5f4", "#5598e7", "#1c5cab"]
INDEX_EDGES = [50, 70, 90, 110, 140, 200]
INDEX_LABELS = ["under 50", "50-70", "70-90", "90-110", "110-140", "140-200", "200 and more"]
# magnitude: one hue, light -> dark
SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SEGMENT_COLORS = {"Thin on both": "#d03b3b", "Thin per event visit": "#eda100",
                  "Thin per resident": "#6250d6", "Above average": AXIS,
                  "No events counted": NONE}
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # categorical, fixed order

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "hatch.linewidth": 0.5,
})
HALO = [pe.withStroke(linewidth=2.6, foreground=SURFACE)]
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)  # fallback-font weight notices


def binned(value, edges: list[float], colors: list[str], missing: str = NONE) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return missing
    for edge, color in zip(edges, colors):
        if value < edge:
            return color
    return colors[len(edges)]


def index_color(index) -> str:
    return binned(index, INDEX_EDGES, DIVERGING)


def nice_edges(values, n: int = 6) -> list[float]:
    """Round class edges at quantiles of `values` (n classes -> n-1 edges)."""
    vals = sorted(v for v in values if v is not None and not math.isnan(v))
    edges = []
    for i in range(1, n):
        q = vals[min(len(vals) - 1, round(i * (len(vals) - 1) / n))]
        mag = 10 ** max(0, math.floor(math.log10(q)) - 1) if q > 0 else 1
        e = round(q / mag) * mag
        if not edges or e > edges[-1]:
            edges.append(e)
    return edges


def edge_labels(edges: list[float], fmt=lambda v: f"{v:,.0f}") -> list[str]:
    return ([f"under {fmt(edges[0])}"] + [f"{fmt(a)}-{fmt(b)}" for a, b in zip(edges, edges[1:])]
            + [f"{fmt(edges[-1])} and more"])


# ---------- geometry ----------

def _polygons(geom: dict) -> list[list]:
    return [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]


def _area(ring) -> float:
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]))) / 2


def _centroid(ring) -> tuple[float, float]:
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    if a == 0:
        return ring[0][0], ring[0][1]
    return cx / (3 * a), cy / (3 * a)


class Map:
    """Shapes in a simple equal-area-ish projection: x = lon * cos(lat0), y = lat."""

    def __init__(self, shapes: list[tuple[str, dict]], kx: float | None = None):
        """`kx` lets a second layer (e.g. region labels over districts) share another map's scale."""
        self.shapes = shapes
        lats = [lat for _, g in shapes for poly in _polygons(g) for _, lat in poly[0]]
        self.kx = kx or math.cos(math.radians(sum(lats) / len(lats)))

    def xy(self, lon: float, lat: float) -> tuple[float, float]:
        return lon * self.kx, lat

    def outer_rings(self, geom: dict) -> list[list[tuple[float, float]]]:
        return [[self.xy(lon, lat) for lon, lat in poly[0]] for poly in _polygons(geom)]

    def label_point(self, geom: dict) -> tuple[float, float]:
        return _centroid(max(self.outer_rings(geom), key=_area))

    def draw(self, ax, fills: dict[str, str], edge: str = SURFACE, lw: float = 0.7) -> None:
        # largest first, so a city drawn inside its surrounding district stays visible
        order = sorted(self.shapes, key=lambda s: -sum(_area(r) for r in self.outer_rings(s[1])))
        for sid, geom in order:
            fill = fills.get(sid, NONE)
            for ring in self.outer_rings(geom):
                ax.add_patch(Polygon(ring, closed=True, facecolor=fill, edgecolor=edge, linewidth=lw,
                                     hatch=NONE_HATCH if fill == NONE else None, hatchcolor=AXIS))
        ax.set_aspect("equal")
        ax.autoscale_view()
        ax.axis("off")

    def outline(self, ax, shapes: list[tuple[str, dict]], color: str = INK2, lw: float = 1.3) -> None:
        for _, geom in shapes:
            for ring in self.outer_rings(geom):
                ax.add_patch(Polygon(ring, closed=True, fill=False, edgecolor=color, linewidth=lw))

    def labels(self, ax, texts: dict[str, str], nudge: dict[str, tuple[float, float]] | None = None,
               size: float = 8, weight: str = "semibold") -> None:
        for sid, geom in self.shapes:
            if sid not in texts:
                continue
            x, y = self.label_point(geom)
            dx, dy = (nudge or {}).get(sid, (0, 0))
            ax.text(x + dx * self.kx, y + dy, texts[sid], ha="center", va="center", fontsize=size,
                    color=INK, fontweight=weight, path_effects=HALO, zorder=5, linespacing=1.05)

    def bubbles(self, ax, lons, lats, sizes, size_max: float, area_max_pt2: float = 420) -> None:
        xs, ys = zip(*(self.xy(lo, la) for lo, la in zip(lons, lats)))
        s = [area_max_pt2 * v / size_max for v in sizes]
        ax.scatter(xs, ys, s=s, facecolor=(0.04, 0.04, 0.04, 0.16), edgecolor=INK,
                   linewidth=0.6, zorder=4)


def bubble_handles(refs: list[float], size_max: float, area_max_pt2: float = 420,
                   fmt=lambda v: f"{v / 1e6:g}M visits") -> list:
    return [Line2D([], [], linestyle="none", marker="o", markersize=math.sqrt(area_max_pt2 * r / size_max),
                   markerfacecolor=(0.04, 0.04, 0.04, 0.16), markeredgecolor=INK,
                   markeredgewidth=0.6, label=fmt(r)) for r in refs]


def patches(labels: list[str], colors: list[str]) -> list:
    return [Patch(facecolor=c, edgecolor=AXIS, linewidth=0.5, label=lab,
                  hatch=NONE_HATCH if c == NONE else None, hatchcolor=AXIS)
            for lab, c in zip(labels, colors)]


def map_figure(m: Map, fills: dict[str, str], title: str, subtitle: str, source: str,
               legend: list, legend_title: str, bubble_legend: list | None = None,
               labels: dict[str, str] | None = None, nudge=None, label_size: float = 8,
               outline: list | None = None, figsize=(7.2, 8.4), bubbles=None,
               legend_cols: int = 4):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0.03, 0.17, 0.94, 0.70])
    m.draw(ax, fills, lw=0.5 if len(m.shapes) > 30 else 0.8)
    if outline:
        m.outline(ax, outline)
    if bubbles is not None:
        m.bubbles(ax, *bubbles)
    if labels:
        m.labels(ax, labels, nudge, size=label_size)
    fig.text(0.03, 0.965, title, fontsize=14, fontweight="semibold", color=INK, va="top")
    fig.text(0.03, 0.925, subtitle, fontsize=9, color=INK2, va="top", wrap=True)
    leg = fig.legend(handles=legend, title=legend_title, loc="lower left", bbox_to_anchor=(0.03, 0.065),
                     ncol=legend_cols, frameon=False, fontsize=8, title_fontsize=8.5,
                     alignment="left", handlelength=1.4, columnspacing=1.2)
    leg.get_title().set_color(INK2)
    if bubble_legend:
        bl = fig.legend(handles=bubble_legend, title="Event hotspots (annual visits)",
                        loc="lower right", bbox_to_anchor=(0.97, 0.065), ncol=len(bubble_legend),
                        frameon=False, fontsize=8, title_fontsize=8.5, alignment="left",
                        columnspacing=1.2, handletextpad=0.9, borderpad=0.2)
        bl.get_title().set_color(INK2)
    fig.text(0.03, 0.018, source, fontsize=7, color=MUTED, va="bottom", wrap=True)
    return fig


# ---------- charts ----------

def _frame(fig, title: str, subtitle: str, source: str, top: float = 0.83) -> None:
    fig.text(0.02, 0.975, title, fontsize=13, fontweight="semibold", color=INK, va="top")
    fig.text(0.02, 0.915, subtitle, fontsize=9, color=INK2, va="top", wrap=True)
    fig.text(0.02, 0.012, source, fontsize=7, color=MUTED, va="bottom", wrap=True)


def ranked_bars(names: list[str], values: list[float], colors: list[str], title: str, subtitle: str,
                xlabel: str, source: str, ref: float | None = None, ref_label: str = "",
                legend: list | None = None, fmt=lambda v: f"{v:,.0f}", figsize=None):
    """Horizontal bars in the given order (top first), value label at each bar end."""
    n = len(names)
    fig = plt.figure(figsize=figsize or (7.6, 1.6 + 0.29 * n))
    bottom = 0.10 + (0.06 if legend else 0)
    ax = fig.add_axes([0.30, bottom, 0.62, 0.83 - bottom])
    ys = list(range(n))[::-1]
    ax.barh(ys, values, color=colors, height=0.68, edgecolor=SURFACE, linewidth=0, zorder=2)
    vmax = max(v for v in values if v is not None)
    for y, v in zip(ys, values):
        ax.text(v + vmax * 0.012, y, fmt(v), va="center", fontsize=7.5, color=INK2,
                path_effects=HALO, zorder=3)
    ax.set_yticks(ys, names, fontsize=8.5, color=INK)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, vmax * 1.12)
    ax.set_xlabel(xlabel, fontsize=8)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    if ref is not None:
        ax.axvline(ref, color=INK, linewidth=1, linestyle=(0, (3, 2)), zorder=1.5)
        ax.text(ref, n - 0.35, f" {ref_label}", fontsize=7.5, color=INK, va="bottom", ha="left",
                path_effects=HALO)
    if legend:
        fig.legend(handles=legend, loc="lower left", bbox_to_anchor=(0.30, 0.045), ncol=len(legend),
                   frameon=False, fontsize=7.5, handlelength=1.2, columnspacing=1.0)
    _frame(fig, title, subtitle, source)
    return fig


def signed_bars(names: list[str], values: list[float], title: str, subtitle: str, xlabel: str,
                source: str, fmt=lambda v: f"{v:+.0f}%"):
    """Diverging horizontal bars around zero (red = decline, blue = growth)."""
    n = len(names)
    fig = plt.figure(figsize=(7.6, 1.6 + 0.29 * n))
    ax = fig.add_axes([0.30, 0.10, 0.62, 0.73])
    ys = list(range(n))[::-1]
    colors = [DIVERGING[1] if v < 0 else DIVERGING[5] for v in values]
    ax.barh(ys, values, color=colors, height=0.68, zorder=2)
    span = max(abs(v) for v in values)
    for y, v in zip(ys, values):
        ax.text(v + (span * 0.015 if v >= 0 else -span * 0.015), y, fmt(v), va="center",
                ha="left" if v >= 0 else "right", fontsize=7.5, color=INK2)
    ax.axvline(0, color=INK2, linewidth=0.8)
    ax.set_yticks(ys, names, fontsize=8.5, color=INK)
    ax.tick_params(axis="y", length=0)
    lo = min(0, min(values))
    ax.set_xlim(lo - span * 0.15, max(values) + span * 0.15)
    ax.set_xlabel(xlabel, fontsize=8)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    _frame(fig, title, subtitle, source)
    return fig


def index_lines(years: list[int], series: dict[str, list[float]], labels: dict[str, str], title: str,
                subtitle: str, source: str, ylabel: str, notes: dict[int, str] | None = None):
    """Up to three lines on one axis, each direct-labelled at its last point."""
    fig = plt.figure(figsize=(7.6, 4.6))
    ax = fig.add_axes([0.09, 0.13, 0.72, 0.62])
    for color, (name, vals) in zip(SERIES, series.items()):
        ax.plot(years, vals, color=color, linewidth=2, label=name)
        ax.plot(years[-1], vals[-1], marker="o", markersize=5, color=color,
                markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.text(years[-1] + 0.25, vals[-1], labels[name], color=INK, fontsize=8, va="center")
    ax.axhline(100, color=AXIS, linewidth=0.8)
    for year, text in (notes or {}).items():
        ax.axvline(year, color=MUTED, linewidth=0.8, linestyle=(0, (2, 2)))
        ax.text(year + 0.1, ax.get_ylim()[1], text, fontsize=7, color=INK2, va="top")
    ax.set_xticks(years, [str(y) if (y - years[0]) % 2 == 0 else "" for y in years], fontsize=8)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    _frame(fig, title, subtitle, source)
    return fig


def share_bars(rows: dict[str, dict[str, float]], order: list[str], title: str, subtitle: str,
               source: str):
    """100 % stacked horizontal bars, one per row; segments direct-labelled where wide enough."""
    fig = plt.figure(figsize=(7.6, 3.6))
    ax = fig.add_axes([0.16, 0.30, 0.80, 0.40])
    names = list(rows)
    for i, name in enumerate(names):
        total = sum(rows[name].values())
        left = 0.0
        for color, part in zip(SERIES, order):
            share = rows[name].get(part, 0) / total * 100
            ax.barh(len(names) - 1 - i, share, left=left, color=color, height=0.62,
                    edgecolor=SURFACE, linewidth=2)
            if share >= 6:
                ax.text(left + share / 2, len(names) - 1 - i, f"{share:.0f}%", ha="center",
                        va="center", fontsize=8, color=INK, path_effects=HALO)
            left += share
    ax.set_yticks(range(len(names))[::-1], names, fontsize=9, color=INK)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"], fontsize=8)
    ax.spines["left"].set_visible(False)
    fig.legend(handles=patches(order, SERIES[:len(order)]), loc="lower left",
               bbox_to_anchor=(0.16, 0.08), ncol=len(order), frameon=False, fontsize=8,
               handlelength=1.2, columnspacing=1.0)
    _frame(fig, title, subtitle, source)
    return fig


def save(fig, path) -> None:
    fig.savefig(path, dpi=200)
    plt.close(fig)
