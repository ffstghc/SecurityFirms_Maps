"""Build every result: maps, charts, tables and a summary per part.

  results/1_Germany   security workers vs. event demand by federal state
  results/2_Bavaria   the same by Bavarian district and Regierungsbezirk
  results/3_Owners    how many security firms there are, where, and in which legal form

Run from the project folder:  python code/build_results.py
(Part 3 reads data/raw/destatis/, which code/fetch_owners_data.py downloads.)
"""

from __future__ import annotations

import shutil

import pandas as pd

from secmap import data as D
from secmap import figures as F
from secmap import metrics as M

OUT_DE = D.RESULTS / "1_Germany"
OUT_BY = D.RESULTS / "2_Bavaria"
OUT_OW = D.RESULTS / "3_Owners"

SRC_STAFF = "Workers: Statistik der Bundesagentur für Arbeit, Beschäftigte nach Wirtschaftszweigen (WZ 2008 class 80.1), 31.03.2026, insured + minijobs."
SRC_POP = "Residents: Destatis, 31.12.2025."
SRC_EVENTS = "Event visits: football leagues 1-3 2025/26 (diefalsche9.de), DSB Volksfest study 2023, city festivals, fairs 2025, music festivals; see events.csv."
SRC_BY = ("Workers: Bundesagentur für Arbeit, Regionalreport über Beschäftigte, security occupations (KldB 53), "
          "31.03.2026, insured + minijobs. Residents: Destatis 31.12.2024. Events: see events_counted.csv.")
SRC_VAT = "Firms: Destatis GENESIS 73311-0011 / -0002 / -0005, Umsatzsteuerstatistik (Voranmeldungen), WZ 2008 class 80.10."
DE_NUDGE = {"BB": (0.55, -0.55), "HB": (0, 0.12), "HH": (0.1, 0.1)}


def fmt1(v) -> str:
    return "–" if pd.isna(v) else f"{v:,.1f}"


def fmt0(v) -> str:
    return "–" if pd.isna(v) else f"{v:,.0f}"


def md_table(df: pd.DataFrame, formats: dict | None = None, align_left: tuple = ()) -> str:
    formats = formats or {}
    cols = list(df.columns)
    head = "| " + " | ".join(cols) + " |"
    sep = "|" + "|".join(":---" if c in align_left else "---:" for c in cols) + "|"
    rows = ["| " + " | ".join(formats.get(c, str)(v) for c, v in zip(cols, r)) + " |"
            for r in df.itertuples(index=False)]
    return "\n".join([head, sep, *rows])


def list_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def takeaway(rows: pd.DataFrame, total: pd.Series, area: str) -> str:
    """The dashboard's headline sentence."""
    ranked = rows.dropna(subset=["per100k_visits"]).sort_values("per100k_visits")
    both = rows[rows["segment"] == "Thin on both"].sort_values("per100k_visits")
    first = list_names([f"{r.name} ({r.per100k_visits:,.1f})" for r in ranked.head(3).itertuples()])
    text = (f"Fewest security workers per 100,000 event visits: {first}, against "
            f"{total['per100k_visits']:,.1f} for {area}. ")
    if len(both):
        text += ("Below average on both lenses, i.e. also thin per resident: "
                 + ", ".join(both["name"].head(8)) + (f" and {len(both) - 8} more" if len(both) > 8 else "")
                 + " — the clearest case for extra event-security capacity.")
    else:
        text += "No area is below average on both lenses for this event mix."
    return text


def index_legend(rows: pd.DataFrame) -> list:
    none = ["no counted events"] if rows["per100k_visits"].isna().any() else []
    return F.patches(F.INDEX_LABELS + none, F.DIVERGING + [F.NONE] * len(none))


def segment_legend(present: set[str]) -> list:
    names = [s for s in M.SEGMENTS if s in present]
    return F.patches(names, [F.SEGMENT_COLORS[s] for s in names])


def seq_fills(values: dict[str, float], edges: list[float]) -> dict[str, str]:
    return {k: F.binned(v if v else None, edges, F.SEQUENTIAL) for k, v in values.items()}


# =====================================================================
# Part 1: Germany
# =====================================================================

def part_germany() -> dict:
    OUT_DE.mkdir(parents=True, exist_ok=True)
    staff, pop, ev = D.security_staff(), D.population(), D.events()
    rows = M.germany(staff, pop, ev)
    total = M.totals(rows, ["combo", "level"]).iloc[0]
    m = F.Map([(r["code"], r["geometry"]) for r in D.state_shapes()])
    bubbles = (ev["lon"].astype(float), ev["lat"].astype(float), ev["visits"].astype(float),
               float(ev["visits"].max()))
    blegend = F.bubble_handles([1e6, 3e6, 7e6], float(ev["visits"].max()))
    src = f"{SRC_STAFF} {SRC_POP} {SRC_EVENTS}"
    by_id = rows.set_index("id")

    fig = F.map_figure(
        m, {i: F.index_color(r["index"]) for i, r in by_id.iterrows()},
        "Security workers per event visit, by state",
        f"Index, Germany = 100 ({total['per100k_visits']:,.1f} workers per 100,000 counted event visits). "
        "Red = fewer workers per visit than average (thin supply), blue = more.\nBubbles show where the visits happen.",
        src, index_legend(rows), "Index, workers per 100,000 event visits", blegend,
        labels={i: f"{i}\n{r['index']:.0f}" for i, r in by_id.iterrows()}, nudge=DE_NUDGE,
        bubbles=bubbles)
    F.save(fig, OUT_DE / "map_1_workers_per_event_visit.png")

    fig = F.map_figure(
        m, {i: F.index_color(r["resid_index"]) for i, r in by_id.iterrows()},
        "Security workers per resident, by state",
        f"Index, Germany = 100 ({total['per100k_residents']:,.1f} workers per 100,000 residents). "
        "Demand-free view of the security labour pool.",
        src, F.patches(F.INDEX_LABELS, F.DIVERGING), "Index, workers per 100,000 residents",
        labels={i: f"{i}\n{r['resid_index']:.0f}" for i, r in by_id.iterrows()}, nudge=DE_NUDGE)
    F.save(fig, OUT_DE / "map_2_workers_per_resident.png")

    fig = F.map_figure(
        m, {i: F.SEGMENT_COLORS[r["segment"]] for i, r in by_id.iterrows()},
        "Priority segments, by state",
        "Combines both lenses. Thin on both = below the German average per event visit and per resident.",
        src, segment_legend(set(rows["segment"])), "Segment",
        labels={i: i for i in by_id.index}, nudge=DE_NUDGE, legend_cols=2)
    F.save(fig, OUT_DE / "map_3_priority_segments.png")

    edges = [1e6, 2e6, 5e6, 10e6, 20e6]
    fig = F.map_figure(
        m, seq_fills(by_id["visits"].to_dict(), edges),
        "Counted event visits per year, by state",
        "Demand side: annual visits to the large recurring events in events.csv.",
        src, F.patches(F.edge_labels(edges, lambda v: f"{v / 1e6:g}M"), F.SEQUENTIAL[:len(edges) + 1]),
        "Event visits per year", blegend,
        labels={i: f"{i}\n{r['visits'] / 1e6:.1f}M" for i, r in by_id.iterrows()}, nudge=DE_NUDGE,
        bubbles=bubbles)
    F.save(fig, OUT_DE / "map_4_event_demand.png")

    ranked = rows.sort_values("per100k_visits")
    fig = F.ranked_bars(
        list(ranked["name"]), list(ranked["per100k_visits"]),
        [F.SEGMENT_COLORS[s] for s in ranked["segment"]],
        "States ranked: fewest security workers per event visit first",
        "Security workers (WZ 80.1) per 100,000 counted event visits. Bar colour = priority segment.",
        "Workers per 100,000 event visits", src, ref=total["per100k_visits"],
        ref_label=f"Germany {total['per100k_visits']:,.1f}", legend=segment_legend(set(rows["segment"])))
    F.save(fig, OUT_DE / "chart_states_ranked.png")

    # tables
    cols = ["id", "name", "workers", "residents", "visits", *M.DE_CATS, "per100k_visits", "index",
            "per100k_residents", "resid_index", "segment"]
    ranked[cols].rename(columns={"id": "code", "name": "state"}).to_csv(
        OUT_DE / "state_metrics.csv", index=False)
    M.germany_all_mixes(staff, pop, ev).rename(columns={"id": "code", "name": "state"}).to_csv(
        OUT_DE / "state_metrics_all_event_mixes.csv", index=False)
    ev.sort_values("visits", ascending=False).to_csv(OUT_DE / "events_counted.csv", index=False)

    table = ranked.assign(visits_m=ranked["visits"] / 1e6)[
        ["name", "workers", "visits_m", "per100k_visits", "index", "per100k_residents", "segment"]]
    table.columns = ["State", "Workers", "Event visits (M)", "Per 100k visits", "Index", "Per 100k residents", "Segment"]
    summary = f"""# Part 1 — Germany: private security supply vs. event demand by state

{takeaway(rows, total, "Germany")}

| | |
|---|---:|
| Security workers in private guarding firms (WZ 80.1), insured + minijobs, 31 Mar 2026 | {total['workers']:,.0f} |
| Event visits per year counted (all five event types) | {total['visits'] / 1e6:,.1f} million |
| Security workers per 100,000 event visits — Germany | {total['per100k_visits']:,.1f} |
| Security workers per 100,000 residents — Germany | {total['per100k_residents']:,.1f} |
| States below the German average on both lenses | {int(total['thin_both'])} |

## States, fewest workers per event visit first

{md_table(table, {"Workers": fmt0, "Event visits (M)": fmt1, "Per 100k visits": fmt1, "Index": fmt0, "Per 100k residents": fmt1}, align_left=("State", "Segment"))}

Index 100 = German average. Event types counted: {", ".join(M.CAT_LABELS[c] for c in M.DE_CATS)}.

## Files

- `map_1_workers_per_event_visit.png` — index of workers per event visit, with event hotspots
- `map_2_workers_per_resident.png` — index of workers per resident (demand-free)
- `map_3_priority_segments.png` — which lens is below average
- `map_4_event_demand.png` — counted event visits, with event hotspots
- `chart_states_ranked.png` — the ranking table as a chart
- `state_metrics.csv` — the table above with all columns (default mix: all event types)
- `state_metrics_all_event_mixes.csv` — the same for all 31 mixes of event types (`combo`: f football, v Volksfeste, s city festivals, m fairs, l music festivals)
- `events_counted.csv` — the 118 events behind the demand side, with sources

## How to read this

**Supply** — people working in private guarding and security firms (WZ 2008 class 80.1, "Private Wach- und Sicherheitsdienste") at their place of work: employees subject to social insurance plus minijobs, Federal Employment Agency, 31 March 2026. This is total headcount, not event staff only: most of it is object protection, aviation security (strong in Hessen because of Frankfurt airport) and public-sector contracts (strong in Berlin), so a high value does not mean spare event capacity.

**Demand** — annual visits to large recurring crowd events with published figures, assigned to the state where they take place: professional football (leagues 1–3, 2025/26), the 30 biggest Volksfeste (DSB 2023), city festivals above one million visits, the largest fairs of 2025 and the ten biggest music festivals. Christmas markets, arena concerts, carnival, demonstrations and most smaller events are not included; states whose demand sits mostly in such events (e.g. Berlin, Saxony, Thuringia) are understated.

**Segments** — "Thin on both" = below average per event visit *and* per resident, the clearest gap; "Thin per event visit" = many events but an average-or-better labour pool; "Thin per resident" = small labour pool but few counted events.

Workers cross state lines for big events and firms deploy staff nationally, so read the maps as a relative indicator of where local supply is stretched, not as a staffing count.
"""
    (OUT_DE / "summary.md").write_text(summary, encoding="utf-8")
    return {"rows": rows, "total": total}


# =====================================================================
# Part 2: Bavaria
# =====================================================================

def part_bavaria() -> dict:
    OUT_BY.mkdir(parents=True, exist_ok=True)
    districts, ev = D.by_districts(), D.by_events()
    drows, rrows = M.bavaria(districts, ev)
    total = M.totals(drows, ["combo", "level"]).iloc[0]
    shapes = D.by_shapes()
    dshapes = [(s["id"], s["geometry"]) for s in shapes if s["level"] == "district"]
    rshapes = [(s["id"], s["geometry"]) for s in shapes if s["level"] == "region"]
    md = F.Map(dshapes)
    mr = F.Map(rshapes, kx=md.kx)
    vmax = float(ev["visits"].max())
    bubbles = (ev["lon"].astype(float), ev["lat"].astype(float), ev["visits"].astype(float), vmax, 520)
    blegend = F.bubble_handles([1e6, 3e6, 7e6], vmax, area_max_pt2=520)
    src = SRC_BY
    d_by, r_by = drows.set_index("id"), rrows.set_index("id")
    region_labels = {i: i for i in r_by.index}
    size = (8.0, 8.4)

    def district_map(fills, title, subtitle, legend, legend_title, file, with_bubbles=False, cols=4):
        fig = F.map_figure(md, fills, title, subtitle, src, legend, legend_title,
                           blegend if with_bubbles else None, outline=rshapes, figsize=size,
                           bubbles=bubbles if with_bubbles else None, legend_cols=cols)
        mr.labels(fig.axes[0], region_labels, size=7.5, weight="normal")
        F.save(fig, OUT_BY / file)

    district_map({i: F.index_color(r["index"]) for i, r in d_by.iterrows()},
                 "Security workers per event visit, by district",
                 f"Index, Bavaria = 100 ({total['per100k_visits']:,.1f} people in security occupations per 100,000 counted "
                 "event visits).\nRed = fewer workers per visit than average, blue = more; hatched = no counted event in the district.",
                 index_legend(drows), "Index, workers per 100,000 event visits", "map_1_districts_workers_per_event_visit.png",
                 with_bubbles=True)
    district_map({i: F.index_color(r["resid_index"]) for i, r in d_by.iterrows()},
                 "Security workers per resident, by district",
                 f"Index, Bavaria = 100 ({total['per100k_residents']:,.1f} per 100,000 residents). "
                 "Freising and Erding stand out because of Munich airport.",
                 F.patches(F.INDEX_LABELS, F.DIVERGING), "Index, workers per 100,000 residents",
                 "map_2_districts_workers_per_resident.png")
    district_map({i: F.SEGMENT_COLORS[r["segment"]] for i, r in d_by.iterrows()},
                 "Priority segments, by district",
                 "Thin on both = below the Bavarian average per event visit and per resident.",
                 segment_legend(set(drows["segment"])), "Segment", "map_3_districts_priority_segments.png", cols=3)
    edges = [0.25e6, 0.5e6, 1e6, 2e6, 5e6]
    district_map(seq_fills(d_by["visits"].to_dict(), edges),
                 "Counted event visits per year, by district",
                 "Demand side: annual visits to the Bavarian events in events_counted.csv; hatched = none counted.",
                 F.patches(F.edge_labels(edges, lambda v: f"{v / 1e6:g}M") + ["none counted"],
                           F.SEQUENTIAL[:len(edges) + 1] + [F.NONE]),
                 "Event visits per year", "map_4_districts_event_demand.png", with_bubbles=True)

    for fills, title, subtitle, legend, ltitle, file in [
        ({i: F.index_color(r["index"]) for i, r in r_by.iterrows()},
         "Security workers per event visit, by Regierungsbezirk",
         "Index, Bavaria = 100. Regions pool staff from neighbouring districts, so this is the fairer comparison.",
         F.patches(F.INDEX_LABELS, F.DIVERGING), "Index, workers per 100,000 event visits",
         "map_5_regions_workers_per_event_visit.png"),
        ({i: F.SEGMENT_COLORS[r["segment"]] for i, r in r_by.iterrows()},
         "Priority segments, by Regierungsbezirk",
         "Thin on both = below the Bavarian average per event visit and per resident.",
         segment_legend(set(rrows["segment"])), "Segment", "map_6_regions_priority_segments.png"),
    ]:
        fig = F.map_figure(mr, fills, title, subtitle, src, legend, ltitle, blegend, figsize=size,
                           bubbles=bubbles, legend_cols=4 if "index" in file or "event_visit" in file else 3,
                           labels={i: f"{i}\n{r['index']:.0f}" if "event_visit" in file else i
                                   for i, r in r_by.iterrows()})
        F.save(fig, OUT_BY / file)

    rr = rrows.sort_values("per100k_visits")
    fig = F.ranked_bars(list(rr["name"]), list(rr["per100k_visits"]), [F.SEGMENT_COLORS[s] for s in rr["segment"]],
                        "Regierungsbezirke ranked: fewest security workers per event visit first",
                        "People in security occupations (KldB 53) per 100,000 counted event visits. Bar colour = segment.",
                        "Workers per 100,000 event visits", src, ref=total["per100k_visits"],
                        ref_label=f"Bavaria {total['per100k_visits']:,.1f}", legend=segment_legend(set(rr["segment"])))
    F.save(fig, OUT_BY / "chart_regions_ranked.png")
    dr = drows.dropna(subset=["per100k_visits"]).sort_values("per100k_visits")
    fig = F.ranked_bars(list(dr["name"]), list(dr["per100k_visits"]), [F.SEGMENT_COLORS[s] for s in dr["segment"]],
                        "Districts with counted events, fewest workers per event visit first",
                        f"{len(dr)} of 96 districts host a counted event; the others have no per-visit value. Bar colour = segment.",
                        "Workers per 100,000 event visits", src, ref=total["per100k_visits"],
                        ref_label=f"Bavaria {total['per100k_visits']:,.1f}", legend=segment_legend(set(dr["segment"])))
    F.save(fig, OUT_BY / "chart_districts_ranked.png")

    cols = ["id", "name", "region", "workers", "residents", "visits", *M.BY_CATS, "per100k_visits", "index",
            "per100k_residents", "resid_index", "segment"]
    drows.sort_values(["per100k_visits", "per100k_residents"], na_position="last")[["type", *cols]].rename(
        columns={"id": "ags", "name": "district"}).to_csv(OUT_BY / "district_metrics.csv", index=False)
    rr[cols].rename(columns={"id": "region_id"}).drop(columns="name").to_csv(OUT_BY / "region_metrics.csv", index=False)
    M.bavaria_all_mixes(districts, ev).to_csv(OUT_BY / "metrics_all_event_mixes.csv", index=False)
    ev.sort_values("visits", ascending=False).to_csv(OUT_BY / "events_counted.csv", index=False)

    rtable = rr[["name", "workers", "visits", "per100k_visits", "index", "per100k_residents", "segment"]].assign(
        visits=lambda x: x["visits"] / 1e6)
    rtable.columns = ["Regierungsbezirk", "Workers", "Event visits (M)", "Per 100k visits", "Index", "Per 100k residents", "Segment"]
    dtable = dr[["name", "region", "workers", "visits", "per100k_visits", "index", "per100k_residents", "segment"]].assign(
        visits=lambda x: x["visits"] / 1e6)
    dtable.columns = ["District", "Region", "Workers", "Event visits (M)", "Per 100k visits", "Index", "Per 100k residents", "Segment"]
    rtotal = M.totals(rrows, ["combo", "level"]).iloc[0]
    fm = {"Workers": fmt0, "Event visits (M)": fmt1, "Per 100k visits": fmt1, "Index": fmt0, "Per 100k residents": fmt1}
    summary = f"""# Part 2 — Bavaria: security workforce vs. event demand by district

**Districts:** {takeaway(drows, total, "Bavaria")}

**Regierungsbezirke:** {takeaway(rrows, rtotal, "Bavaria")}

| | |
|---|---:|
| People working in security occupations (KldB 53) in Bavaria, insured + minijobs, 31 Mar 2026 | {total['workers']:,.0f} |
| Event visits per year counted in Bavaria (all six event types) | {total['visits'] / 1e6:,.1f} million |
| Security workers per 100,000 event visits — Bavaria | {total['per100k_visits']:,.1f} |
| Security workers per 100,000 residents — Bavaria | {total['per100k_residents']:,.1f} |
| Districts below the Bavarian average on both lenses | {int(total['thin_both'])} |
| Districts with at least one counted event | {len(dr)} of 96 |

## Regierungsbezirke, fewest workers per event visit first

{md_table(rtable, fm, align_left=("Regierungsbezirk", "Segment"))}

## Districts with counted events

{md_table(dtable, fm, align_left=("District", "Region", "Segment"))}

The other {96 - len(dr)} districts host none of the counted events; their per-resident values are in `district_metrics.csv`.

## Files

- `map_1_districts_workers_per_event_visit.png`, `map_2_districts_workers_per_resident.png`, `map_3_districts_priority_segments.png`, `map_4_districts_event_demand.png` — the 96 districts (Regierungsbezirk borders drawn thicker)
- `map_5_regions_workers_per_event_visit.png`, `map_6_regions_priority_segments.png` — the 7 Regierungsbezirke
- `chart_regions_ranked.png`, `chart_districts_ranked.png` — rankings
- `district_metrics.csv`, `region_metrics.csv` — all values (default mix: all event types)
- `metrics_all_event_mixes.csv` — all 63 mixes (`combo`: f football, h ice hockey, v Volksfeste, x Christmas markets, m fairs, l music festivals)
- `events_counted.csv` — the 33 Bavarian events, with sources

## How to read the Bavaria view

**Supply** — at district level the Federal Employment Agency does not publish industry class 80.1, so this part counts people working in security *occupations* (KldB 2010 main group 53 "Schutz-, Sicherheits-, Überwachungsberufe") at their place of work, insured employees plus minijobs, 31 March 2026. That is broader than Part 1: it also includes in-house security, plant fire brigades and airport screeners, which is why Freising and Erding (Munich airport) stand out. Police officers are civil servants and are not included. The Bavarian figures are therefore not comparable with the state figures in Part 1.

**Demand** — Bavarian events with published visitor figures: football leagues 1–3 and DEL ice hockey (2025/26 home attendance), the Bavarian Volksfeste from the DSB list plus further large Volksfeste reported by BAYERN TOURISMUS and press, the Christmas markets in Munich and Nuremberg, the largest fairs of 2025 and the biggest music festivals. Basketball, arena concerts and smaller local fairs are not included. Most districts host none of these events.

**Reading it** — index 100 = Bavarian average. Low values mean few security workers in the area relative to the event visits it hosts. Big event cities draw staff from the surrounding districts, so pair the district view with the Regierungsbezirk view.
"""
    (OUT_BY / "summary.md").write_text(summary, encoding="utf-8")
    return {"districts": drows, "regions": rrows, "total": total}


# =====================================================================
# Part 3: Owners — number of security firms per region
# =====================================================================

LEGAL_ORDER = ["GmbH", "Sole proprietors", "KG", "OHG, GbR", "AG, KGaA, other"]
LEGAL_MAP = {"RECHT-GMBH": "GmbH", "RECHT-EZU": "Sole proprietors", "RECHT-KG": "KG",
             "RECHT-OHG-GBR-S": "OHG, GbR", "RECHT-AG-KGAA-S": "AG, KGaA, other",
             "RECHT-EWG": "AG, KGaA, other", "RECHT-KRP-OEFF": "AG, KGaA, other",
             "RECHT-SONST": "AG, KGaA, other"}


def part_owners(germany: dict) -> dict:
    OUT_OW.mkdir(parents=True, exist_ok=True)
    vat = D.vat_firms_by_state()
    nat = D.vat_firms_germany()
    lf = D.vat_firms_by_legal_form()
    staff, pop = D.security_staff(), D.population()
    year = int(vat["year"].max())
    y0 = int(vat["year"].min())

    firms = vat[(vat["wz"] == "80100") & (vat["measure"] == "firms")].pivot(index="code", columns="year", values="value")
    turnover = vat[(vat["wz"] == "80100") & (vat["measure"] == "turnover_keur")].pivot(index="code", columns="year", values="value")
    other = vat[(vat["year"] == year) & (vat["measure"] == "firms") & vat["wz"].isin(["80200", "80300"])].pivot(
        index="code", columns="wz", values="value")
    st = staff.merge(pop, on=["code", "state"]).set_index("code")
    t = pd.DataFrame({
        "state": st["state"],
        **{f"firms_{y}": firms[y] for y in firms.columns},
        "change_pct": (firms[year] / firms[y0] - 1) * 100,
        "residents": st["population"],
        "firms_per_100k_residents": firms[year] / st["population"] * 1e5,
        "workers_801": st["svb_801"] + st["gb_801"],
        "turnover_eur_m": turnover[year] / 1e3,
        "turnover_per_firm_eur_k": turnover[year] / firms[year],
        "firms_alarm_systems_8020": other.get("80200"),
        "firms_detectives_8030": other.get("80300"),
    })
    t["workers_per_firm"] = t["workers_801"] / t[f"firms_{year}"]
    t = t.sort_values(f"firms_{year}", ascending=False)
    t.index.name = "code"
    t.round(1).to_csv(OUT_OW / "firms_by_state.csv")

    natp = nat[nat["measure"] == "firms"].pivot(index="year", columns="wz", values="value")
    natp = natp[["80", "80100", "80200", "80300"]].rename(columns={
        "80": "firms_division_80", "80100": "firms_private_security_8010",
        "80200": "firms_alarm_systems_8020", "80300": "firms_detectives_8030"})
    natp["turnover_8010_eur_m"] = nat[(nat["measure"] == "turnover_keur") & (nat["wz"] == "80100")].set_index("year")["value"] / 1e3
    natp.round(1).to_csv(OUT_OW / "firms_germany_2009_2024.csv")

    l = lf[lf["wz"] == "80100"].copy()
    l["group"] = l["legal_form"].map(LEGAL_MAP)
    lt = l[l["legal_form"] == "TOTAL"].pivot(index="year", columns="measure", values="value")
    lg = l.dropna(subset=["group"]).groupby(["year", "group", "measure"])["value"].sum(min_count=1).unstack("measure")
    legal = lg.reset_index()
    known = legal.groupby("year")[["firms", "turnover_keur"]].sum()
    gap = (lt - known).reset_index().assign(group="not disclosed")
    legal = pd.concat([legal, gap], ignore_index=True).sort_values(["year", "group"])
    legal["firms_share_pct"] = legal["firms"] / legal["year"].map(lt["firms"]) * 100
    legal["turnover_share_pct"] = legal["turnover_keur"] / legal["year"].map(lt["turnover_keur"]) * 100
    legal.rename(columns={"group": "legal_form"}).round(1).to_csv(OUT_OW / "legal_forms_germany_2020_2024.csv", index=False)

    m = F.Map([(r["code"], r["geometry"]) for r in D.state_shapes()])
    per100k = t["firms_per_100k_residents"]
    edges = [4, 5, 6, 7, 9]
    src = f"{SRC_VAT} Residents: Destatis 31.12.2025."
    fig = F.map_figure(
        m, {c: F.binned(v, edges, F.SEQUENTIAL) for c, v in per100k.items()},
        f"Private security firms per 100,000 residents, {year}",
        f"VAT-registered firms in WZ 80.10 (private guarding and security), counted at the firm's seat. "
        f"Label = number of firms.\nGermany: {natp.loc[year, 'firms_private_security_8010']:,.0f} firms, "
        f"{natp.loc[year, 'firms_private_security_8010'] / pop['population'].sum() * 1e5:.1f} per 100,000 residents.",
        src, F.patches(F.edge_labels(edges), F.SEQUENTIAL[:len(edges) + 1]), "Firms per 100,000 residents",
        labels={c: f"{c}\n{v:,.0f}" for c, v in t[f"firms_{year}"].items()}, nudge=DE_NUDGE)
    F.save(fig, OUT_OW / "map_1_firms_per_100k_residents.png")

    wpf = t["workers_per_firm"]
    edges = [40, 50, 60, 75, 100]
    fig = F.map_figure(
        m, {c: F.binned(v, edges, F.SEQUENTIAL) for c, v in wpf.items()},
        "Security workers per registered firm, by state",
        f"Workers in WZ 80.1 at their place of work (31 Mar 2026) ÷ firms registered in the state ({year}).\n"
        "High = staff work for firms based elsewhere or for a few large firms; low = many small firms or staff working in other states.",
        f"{SRC_VAT} {SRC_STAFF}", F.patches(F.edge_labels(edges), F.SEQUENTIAL[:len(edges) + 1]),
        "Workers per firm", labels={c: f"{c}\n{v:.0f}" for c, v in wpf.items()}, nudge=DE_NUDGE)
    F.save(fig, OUT_OW / "map_2_workers_per_firm.png")

    by_firms = t.sort_values(f"firms_{year}", ascending=False)
    fig = F.ranked_bars(list(by_firms["state"]), list(by_firms[f"firms_{year}"]),
                        [F.SERIES[1] if c == "BY" else F.SERIES[0] for c in by_firms.index],
                        f"Private security firms by state, {year}",
                        "VAT-registered firms in WZ 80.10, counted at the firm's seat. Bavaria highlighted.",
                        "Firms", src)
    F.save(fig, OUT_OW / "chart_firms_by_state.png")

    ch = t.sort_values("change_pct", ascending=False)
    fig = F.signed_bars(list(ch["state"]), list(ch["change_pct"]),
                        f"Change in the number of security firms, {y0}–{year}",
                        f"VAT-registered firms in WZ 80.10. Germany: {(natp.loc[year, 'firms_private_security_8010'] / natp.loc[y0, 'firms_private_security_8010'] - 1) * 100:+.0f}%.",
                        f"Change {y0}–{year}", SRC_VAT)
    F.save(fig, OUT_OW / "chart_firm_change_by_state.png")

    years = list(range(y0, year + 1))
    de = natp.loc[years, "firms_private_security_8010"]
    byv = firms.loc["BY", years]
    fig = F.index_lines(
        years, {"Germany": list(de / de.iloc[0] * 100), "Bavaria": list(byv / byv.iloc[0] * 100)},
        {"Germany": f"Germany {de.iloc[-1]:,.0f}", "Bavaria": f"Bavaria {byv.iloc[-1]:,.0f}"},
        f"Security firms over time, {y0} = 100",
        "VAT-registered firms in WZ 80.10. The 2020 dip coincides with the VAT small-business threshold\n"
        "rising from €17,500 to €22,000, which removes the smallest firms from the statistic.",
        SRC_VAT, f"Index, {y0} = 100", notes={2020: "threshold €22,000"})
    F.save(fig, OUT_OW / "chart_firms_trend.png")

    l24 = legal[legal["year"] == year].set_index("group")
    rows = {"Firms": {g: l24.loc[g, "firms"] for g in LEGAL_ORDER if g in l24.index},
            "Turnover": {g: l24.loc[g, "turnover_keur"] for g in LEGAL_ORDER if g in l24.index}}
    fig = F.share_bars(rows, LEGAL_ORDER, f"Who owns them: legal form of security firms in Germany, {year}",
                       f"Share of the {lt.loc[year, 'firms']:,.0f} VAT-registered firms in WZ 80.10 and of their "
                       f"€{lt.loc[year, 'turnover_keur'] / 1e6:,.1f} billion taxable turnover.", SRC_VAT)
    F.save(fig, OUT_OW / "chart_legal_forms.png")

    manual = D.manual_bavaria_firms()
    manual_note = owners_bavaria_districts(manual) if manual is not None else None

    nat_firms = natp.loc[year, "firms_private_security_8010"]
    by = t.loc["BY"]
    rank_firms = int((t[f"firms_{year}"] > by[f"firms_{year}"]).sum()) + 1
    rank_density = int((t["firms_per_100k_residents"] > by["firms_per_100k_residents"]).sum()) + 1
    de_density = nat_firms / pop["population"].sum() * 1e5
    de_wpf = t["workers_801"].sum() / nat_firms
    sole = l24.loc["Sole proprietors"]
    gmbh = l24.loc["GmbH"]
    ly0 = int(legal["year"].min())
    l0 = legal[legal["year"] == ly0].set_index("group")
    dens = t.sort_values("firms_per_100k_residents", ascending=False)
    growth = t.sort_values("change_pct", ascending=False)
    table = t.reset_index()[["state", f"firms_{y0}", f"firms_{year}", "change_pct", "firms_per_100k_residents",
                             "workers_per_firm", "turnover_per_firm_eur_k"]]
    table.columns = ["State", f"Firms {y0}", f"Firms {year}", "Change %", "Per 100k residents",
                     "Workers per firm", "Turnover per firm (€k)"]
    ltab = legal[legal["year"] == year][["group", "firms", "firms_share_pct", "turnover_keur", "turnover_share_pct"]].copy()
    ltab["turnover_keur"] = ltab["turnover_keur"] / 1e3
    ltab = ltab.set_index("group").reindex(LEGAL_ORDER + ["not disclosed"]).reset_index()
    ltab.columns = ["Legal form", "Firms", "Share of firms %", "Turnover (€M)", "Share of turnover %"]
    pct = lambda v: "–" if pd.isna(v) else f"{v:+.0f}%"  # noqa: E731

    bavaria_section = (manual_note or
        "**Not available by district from open sources.** The VAT statistic is published by state only. At "
        "district level, Regionalstatistik.de offers firm counts only for broad WZ sections (security falls under "
        "section N together with cleaning, temp agencies, travel agencies and more), and the Bavarian State Office "
        "for Statistics keeps finer industry detail per district in its GENESIS database "
        "(www.statistikdaten.bayern.de, statistic 52111 Unternehmensregister), which can only be queried "
        "interactively or with a registered account. To add the district map, export security firms (WZ 80.1 or "
        "80) per district from there and save them as `data/raw/manual/bavaria_firms_by_district.csv` with "
        "columns `ags,firms`; `build_results.py` then draws `map_3_bavaria_firms_per_100k_residents.png` "
        "and `map_4_bavaria_workers_per_firm.png` automatically.")

    summary = f"""# Part 3 — Owners: how many private security firms there are, and where

In {year} Germany had **{nat_firms:,.0f} VAT-registered private guarding and security firms** (WZ 2008 class 80.10), {pct((nat_firms / natp.loc[y0, 'firms_private_security_8010'] - 1) * 100)} since {y0}. That is {de_density:.1f} firms per 100,000 residents, and about {de_wpf:.0f} security workers per firm. Sole proprietors make up {sole['firms_share_pct']:.0f}% of the firms but take only {sole['turnover_share_pct']:.0f}% of the turnover; GmbHs are {gmbh['firms_share_pct']:.0f}% of the firms and take {gmbh['turnover_share_pct']:.0f}% of the turnover. Since {ly0} the GmbH share of firms rose from {l0.loc['GmbH', 'firms_share_pct']:.0f}% to {gmbh['firms_share_pct']:.0f}% while sole proprietors fell from {l0.loc['Sole proprietors', 'firms_share_pct']:.0f}% to {sole['firms_share_pct']:.0f}%.

Most firms are registered in {list_names([f"{r.state} ({r[f'firms_{year}']:,.0f})" for _, r in t.head(3).iterrows()])}. Relative to population, {dens.iloc[0]['state']} leads ({dens.iloc[0]['firms_per_100k_residents']:.1f} firms per 100,000 residents), followed by {list_names([f"{r.state} ({r.firms_per_100k_residents:.1f})" for _, r in dens.iloc[1:3].iterrows()])}; {list_names([f"{r.state} ({r.firms_per_100k_residents:.1f})" for _, r in dens.tail(2).iterrows()])} have the fewest. The number of firms grew fastest in {list_names([f"{r.state} ({pct(r.change_pct)})" for _, r in growth.head(2).iterrows()])} and fell most in {growth.iloc[-1]['state']} ({pct(growth.iloc[-1]['change_pct'])}).

## Bavaria

- **{by[f'firms_{year}']:,.0f} firms** in {year}, rank {rank_firms} of 16 by number; {pct(by['change_pct'])} since {y0} (Germany {pct((nat_firms / natp.loc[y0, 'firms_private_security_8010'] - 1) * 100)}).
- **{by['firms_per_100k_residents']:.1f} firms per 100,000 residents**, rank {rank_density} of 16 (1 = densest; Germany {de_density:.1f}).
- **{by['workers_per_firm']:.0f} security workers per firm** (Germany {de_wpf:.0f}): {by['workers_801']:,.0f} WZ 80.1 workers on 31 Mar 2026 ÷ {by[f'firms_{year}']:,.0f} firms.
- **€{by['turnover_eur_m']:,.0f} million** taxable turnover, €{by['turnover_per_firm_eur_k']:,.0f}k per firm.

### Bavarian districts

{bavaria_section}

## Firms by state

{md_table(table, {f"Firms {y0}": fmt0, f"Firms {year}": fmt0, "Change %": pct, "Per 100k residents": fmt1, "Workers per firm": fmt0, "Turnover per firm (€k)": fmt0}, align_left=("State",))}

## Legal form, Germany {year}

{md_table(ltab, {"Firms": fmt0, "Share of firms %": fmt1, "Turnover (€M)": fmt0, "Share of turnover %": fmt1}, align_left=("Legal form",))}

"AG, KGaA, other" also holds cooperatives, public bodies and other legal forms; "not disclosed" is the difference to the published total where Destatis suppresses a cell.

## Files

- `map_1_firms_per_100k_residents.png` — firm density by state, labelled with the number of firms
- `map_2_workers_per_firm.png` — security workers per registered firm
- `chart_firms_by_state.png`, `chart_firm_change_by_state.png`, `chart_firms_trend.png`, `chart_legal_forms.png`
- `firms_by_state.csv` — firms {y0}–{year}, density, workers per firm, turnover, and firms in 80.20 (alarm systems) and 80.30 (detectives)
- `firms_germany_2009_2024.csv` — national series for division 80 and its three classes
- `legal_forms_germany_2020_2024.csv` — firms and turnover by legal form

## How to read this

**What counts as a firm** — a business that filed VAT advance returns in the year with taxable turnover above €22,000 (€17,500 before 2020), classified by its main activity as WZ 2008 class 80.10 "Private Wach- und Sicherheitsdienste". Small businesses below the threshold and annual-only filers are not counted, so solo guards and very small firms are understated. Source: Destatis, Umsatzsteuerstatistik (Voranmeldungen), GENESIS tables 73311-0011 (states), 73311-0002 (Germany) and 73311-0005 (legal forms); latest year {year}.

**Where a firm counts** — at its seat (the tax office of the head office). A firm with branches in several states counts once, with its whole turnover, in its head-office state; workers in Part 1 count where they work. Workers per firm therefore mixes two geographies: it is high where many staff work for firms based in another state or for a few large firms (Hamburg {t.loc['HH', 'workers_per_firm']:.0f}, Bremen {t.loc['HB', 'workers_per_firm']:.0f}, Sachsen {t.loc['SN', 'workers_per_firm']:.0f}), and low where many small firms are registered or firms' staff work across the border (Brandenburg {t.loc['BB', 'workers_per_firm']:.0f}, Rheinland-Pfalz {t.loc['RP', 'workers_per_firm']:.0f}). Turnover per firm is likewise high where large groups have their head office.

**Owner structure** — legal form is the closest official proxy for who owns a firm: a sole proprietor is one person; GmbH, KG and AG are companies whose owners the statistic does not name.
"""
    (OUT_OW / "summary.md").write_text(summary, encoding="utf-8")
    return {"table": t}


def owners_bavaria_districts(manual: pd.DataFrame) -> str:
    """District maps from a hand-exported firm count (data/raw/manual/bavaria_firms_by_district.csv)."""
    d = D.by_districts().merge(manual[["ags", "firms"]], on="ags", how="left")
    d["firms_per_100k"] = d["firms"] / d["population"] * 1e5
    d["workers_per_firm"] = (d["workers_svb"] + d["workers_gb"]) / d["firms"].where(d["firms"] > 0)
    d.round(1).to_csv(OUT_OW / "bavaria_firms_by_district.csv", index=False)
    shapes = D.by_shapes()
    md = F.Map([(s["id"], s["geometry"]) for s in shapes if s["level"] == "district"])
    rshapes = [(s["id"], s["geometry"]) for s in shapes if s["level"] == "region"]
    src = (f"Firms: {manual['source'].iloc[0] if 'source' in manual else 'manual export'}. Workers: Bundesagentur "
           "für Arbeit, security occupations (KldB 53), 31.03.2026. Residents: Destatis 31.12.2024.")
    for col, title, file, unit in [
        ("firms_per_100k", "Security firms per 100,000 residents, by district", "map_3_bavaria_firms_per_100k_residents.png", "Firms per 100,000 residents"),
        ("workers_per_firm", "Security-occupation workers per firm, by district", "map_4_bavaria_workers_per_firm.png", "Workers per firm"),
    ]:
        edges = F.nice_edges(d[col].tolist())
        fig = F.map_figure(md, {a: F.binned(v, edges, F.SEQUENTIAL) for a, v in zip(d["ags"], d[col])},
                           title, "From data/raw/manual/bavaria_firms_by_district.csv; hatched = no value.", src,
                           F.patches(F.edge_labels(edges, lambda v: f"{v:g}"), F.SEQUENTIAL[:len(edges) + 1]), unit,
                           outline=rshapes, figsize=(8.0, 8.4))
        F.save(fig, OUT_OW / file)
    n = int(d["firms"].notna().sum())
    return (f"Drawn from the hand-exported file `data/raw/manual/bavaria_firms_by_district.csv` ({n} of 96 districts, "
            f"{d['firms'].sum():,.0f} firms): see `map_3_bavaria_firms_per_100k_residents.png`, "
            "`map_4_bavaria_workers_per_firm.png` and `bavaria_firms_by_district.csv`. Workers per firm uses the "
            "KldB 53 occupation count from Part 2.")


def write_index(de: dict, by: dict, ow: dict) -> None:
    (D.RESULTS / "README.md").write_text(f"""# Results

| Part | Folder | What it answers |
|---|---|---|
| 1 | [1_Germany](1_Germany/summary.md) | Where in Germany is private security supply thin relative to event demand and population? (16 states) |
| 2 | [2_Bavaria](2_Bavaria/summary.md) | The same inside Bavaria (96 districts, 7 Regierungsbezirke) |
| 3 | [3_Owners](3_Owners/summary.md) | How many private security firms are there per state, how has that changed, and in which legal form are they run? |

Each folder holds a `summary.md` with the headline numbers and tables, the maps and charts as PNG, and the full tables as CSV.
Rebuild everything with `python code/build_results.py` (see the project README).
""", encoding="utf-8")


def main() -> None:
    for out in (OUT_DE, OUT_BY, OUT_OW):
        if out.exists():
            shutil.rmtree(out)
    de = part_germany()
    by = part_bavaria()
    ow = part_owners(de)
    write_index(de, by, ow)
    print("Results written to", D.RESULTS)


if __name__ == "__main__":
    main()
