# Part 2 — Bavaria: security workforce vs. event demand by district

**Districts:** Fewest security workers per 100,000 event visits: Rosenheim (Stadt) (33.5), Straubing (41.7) and Fürth (Stadt) (52.6), against 244.1 for Bavaria. Below average on both lenses, i.e. also thin per resident: Rosenheim (Stadt), Kulmbach — the clearest case for extra event-security capacity.

**Regierungsbezirke:** Fewest security workers per 100,000 event visits: Mittelfranken (135.0), Oberbayern (205.0) and Niederbayern (327.9), against 244.1 for Bavaria. No area is below average on both lenses for this event mix.

| | |
|---|---:|
| People working in security occupations (KldB 53) in Bavaria, insured + minijobs, 31 Mar 2026 | 74,476 |
| Event visits per year counted in Bavaria (all six event types) | 30.5 million |
| Security workers per 100,000 event visits — Bavaria | 244.1 |
| Security workers per 100,000 residents — Bavaria | 562.1 |
| Districts below the Bavarian average on both lenses | 2 |
| Districts with at least one counted event | 16 of 96 |

## Regierungsbezirke, fewest workers per event visit first

| Regierungsbezirk | Workers | Event visits (M) | Per 100k visits | Index | Per 100k residents | Segment |
|:---|---:|---:|---:|---:|---:|:---|
| Mittelfranken | 12,966 | 9.6 | 135.0 | 55 | 722.0 | Thin per event visit |
| Oberbayern | 31,244 | 15.2 | 205.0 | 84 | 655.8 | Thin per event visit |
| Niederbayern | 4,718 | 1.4 | 327.9 | 134 | 374.7 | Thin per resident |
| Schwaben | 8,657 | 1.7 | 520.3 | 213 | 447.8 | Thin per resident |
| Oberpfalz | 6,502 | 1.2 | 556.2 | 228 | 579.8 | Above average |
| Unterfranken | 6,191 | 1.1 | 573.5 | 235 | 469.4 | Thin per resident |
| Oberfranken | 4,198 | 0.3 | 1,311.9 | 537 | 397.6 | Thin per resident |

## Districts with counted events

| District | Region | Workers | Event visits (M) | Per 100k visits | Index | Per 100k residents | Segment |
|:---|:---|---:|---:|---:|---:|---:|:---|
| Rosenheim (Stadt) | Oberbayern | 335 | 1.0 | 33.5 | 14 | 513.2 | Thin on both |
| Straubing | Niederbayern | 600 | 1.4 | 41.7 | 17 | 1,224.4 | Thin per event visit |
| Fürth (Stadt) | Mittelfranken | 902 | 1.7 | 52.6 | 22 | 683.1 | Thin per event visit |
| München, Landeshauptstadt | Oberbayern | 11,439 | 13.3 | 85.8 | 35 | 760.1 | Thin per event visit |
| Kulmbach | Oberfranken | 114 | 0.1 | 95.0 | 39 | 159.4 | Thin on both |
| Erlangen | Mittelfranken | 976 | 1.0 | 97.6 | 40 | 841.9 | Thin per event visit |
| Nürnberg | Mittelfranken | 7,181 | 6.8 | 105.0 | 43 | 1,356.2 | Thin per event visit |
| Würzburg (Stadt) | Unterfranken | 1,414 | 1.0 | 141.4 | 58 | 1,061.1 | Thin per event visit |
| Regensburg (Stadt) | Oberpfalz | 1,684 | 1.2 | 144.1 | 59 | 1,112.4 | Thin per event visit |
| Augsburg (Stadt) | Schwaben | 2,427 | 1.7 | 145.9 | 60 | 806.0 | Thin per event visit |
| Dachau | Oberbayern | 778 | 0.3 | 259.3 | 106 | 506.5 | Thin per resident |
| Bamberg (Stadt) | Oberfranken | 731 | 0.2 | 365.5 | 150 | 947.5 | Above average |
| Erding | Oberbayern | 1,575 | 0.4 | 393.8 | 161 | 1,124.0 | Above average |
| Ingolstadt | Oberbayern | 1,282 | 0.2 | 627.2 | 257 | 908.0 | Above average |
| Schweinfurt (Stadt) | Unterfranken | 591 | 0.1 | 744.0 | 305 | 1,084.8 | Above average |
| Ansbach (Lkr.) | Mittelfranken | 632 | 0.0 | 1,404.4 | 575 | 336.8 | Thin per resident |

The other 80 districts host none of the counted events; their per-resident values are in `district_metrics.csv`.

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
