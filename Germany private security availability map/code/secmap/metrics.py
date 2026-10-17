"""Supply-vs-demand metrics, ported one-to-one from the dashboard's calculations
(`state_metrics`, `national`, `by_metrics`, `by_total` in code/dashboard/index.html).

For every area and every mix of event types:
  per100k_visits     security workers / counted event visits x 100,000
  index              that ratio relative to the overall average (= 100)
  per100k_residents  security workers / residents x 100,000
  segment            which of the two lenses is below average
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

DE_CATS = {"football": "f", "volksfest": "v", "stadtfest": "s", "fair": "m", "festival": "l"}
BY_CATS = {"football": "f", "icehockey": "h", "volksfest": "v", "xmas": "x", "fair": "m", "festival": "l"}
CAT_LABELS = {"football": "Pro football (leagues 1-3)", "icehockey": "Ice hockey (DEL)",
              "volksfest": "Volksfeste", "stadtfest": "City festivals", "xmas": "Christmas markets",
              "fair": "Trade & consumer fairs", "festival": "Music festivals"}

SEGMENTS = ["Thin on both", "Thin per event visit", "Thin per resident", "Above average",
            "No events counted"]


def js_round(x, digits: int = 0):
    """Round half up, like JavaScript's Math.round, so values match the dashboard."""
    f = 10 ** digits
    return np.floor(np.asarray(x, dtype=float) * f + 0.5) / f


def segment(ratio: float | None, ratio_avg: float, resid: float, resid_avg: float) -> str:
    if ratio is None:
        return "No events counted"
    v, r = ratio < ratio_avg, resid < resid_avg
    return "Thin on both" if v and r else "Thin per event visit" if v else \
        "Thin per resident" if r else "Above average"


def combos(cats: dict[str, str]) -> list[list[str]]:
    """Every non-empty mix of event types, in the dashboard's letter order."""
    names = list(cats)
    return [list(c) for n in range(1, len(names) + 1) for c in combinations(names, n)]


def combo_code(on: list[str], cats: dict[str, str]) -> str:
    return "".join(cats[c] for c in cats if c in on)


def visits_by_category(units: pd.DataFrame, events: pd.DataFrame, key: str,
                       cats: dict[str, str]) -> pd.DataFrame:
    """Add one column of annual visits per event category to `units` (joined on `key`)."""
    v = (events.assign(visits=events["visits"].astype(float))
         .pivot_table(index=key, columns="category", values="visits", aggfunc="sum")
         .reindex(columns=list(cats), fill_value=0).fillna(0))
    out = units.merge(v, left_on="id", right_index=True, how="left")
    out[list(cats)] = out[list(cats)].fillna(0)
    return out


def supply_vs_demand(units: pd.DataFrame, cats: dict[str, str], on: list[str],
                     base: pd.DataFrame | None = None) -> pd.DataFrame:
    """Metrics for `units` (id, name, level, workers, residents + one visits column per category).

    Averages come from `base` (default: `units` itself). The Bavaria page uses the
    96 districts as base for both districts and Regierungsbezirke.
    """
    base = units if base is None else base
    w = base["workers"].sum()
    ratio_avg = w / base[on].sum(axis=1).sum()
    resid_avg = w / base["residents"].sum()
    out = units.copy()
    out.insert(0, "combo", combo_code(on, cats))
    out["visits"] = units[on].sum(axis=1)
    ratio = (out["workers"] / out["visits"]).where(out["visits"] > 0)
    resid = out["workers"] / out["residents"]
    out["per100k_visits"] = js_round(ratio * 1e5, 1)
    out["index"] = js_round(ratio / ratio_avg * 100)
    out["per100k_residents"] = js_round(resid * 1e5, 1)
    out["resid_index"] = js_round(resid / resid_avg * 100)
    out["segment"] = [segment(None if pd.isna(a) else a, ratio_avg, b, resid_avg)
                      for a, b in zip(ratio, resid)]
    return out


def totals(rows: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Area-wide sums per mix (the dashboard's `national` / `by_total`)."""
    g = rows.groupby(by, sort=False)
    out = g[["workers", "visits", "residents"]].sum().reset_index()
    out["thin_both"] = g["segment"].apply(lambda s: int((s == "Thin on both").sum())).values
    out["per100k_visits"] = js_round(out["workers"] / out["visits"] * 1e5, 1)
    out["per100k_residents"] = js_round(out["workers"] / out["residents"] * 1e5, 1)
    return out


# ---------- the two pages ----------

def germany_units(staff: pd.DataFrame, pop: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    units = staff.merge(pop[["code", "population"]], on="code")
    units = pd.DataFrame({"level": "state", "id": units["code"], "name": units["state"],
                          "region": units["state"],
                          "workers": units["svb_801"].astype(int) + units["gb_801"].astype(int),
                          "residents": units["population"].astype(int)})
    return visits_by_category(units, events, "code", DE_CATS)


def germany(staff, pop, events, on: list[str] | None = None) -> pd.DataFrame:
    units = germany_units(staff, pop, events)
    return supply_vs_demand(units, DE_CATS, on or list(DE_CATS))


def germany_all_mixes(staff, pop, events) -> pd.DataFrame:
    units = germany_units(staff, pop, events)
    return pd.concat([supply_vs_demand(units, DE_CATS, on) for on in combos(DE_CATS)],
                     ignore_index=True)


def bavaria_units(districts: pd.DataFrame, events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = pd.DataFrame({"level": "district", "id": districts["ags"], "name": districts["district"],
                      "type": districts["type"], "region": districts["region"],
                      "workers": districts["workers_svb"].astype(int) + districts["workers_gb"].astype(int),
                      "residents": districts["population"].astype(int)})
    d = visits_by_category(d, events, "ags", BY_CATS)
    r = d.groupby("region", sort=False)[["workers", "residents", *BY_CATS]].sum().reset_index()
    r.insert(0, "level", "region")
    r.insert(1, "id", r["region"])
    r.insert(2, "name", r["region"])
    return d, r


def bavaria(districts, events, on: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    d, r = bavaria_units(districts, events)
    on = on or list(BY_CATS)
    return supply_vs_demand(d, BY_CATS, on), supply_vs_demand(r, BY_CATS, on, base=d)


def bavaria_all_mixes(districts, events) -> pd.DataFrame:
    d, r = bavaria_units(districts, events)
    parts = []
    for on in combos(BY_CATS):
        parts += [supply_vs_demand(d, BY_CATS, on), supply_vs_demand(r, BY_CATS, on, base=d)]
    return pd.concat(parts, ignore_index=True)
