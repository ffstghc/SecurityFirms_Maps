# Germany private security availability map

Where is private security supply thin relative to event demand? This folder holds
the code and results from our conversation, plus a third part on the firms themselves.

| Part | Results | Question |
|---|---|---|
| 1 | [results/1_Germany](results/1_Germany/summary.md) | Security workers vs. event visits and residents, by federal state |
| 2 | [results/2_Bavaria](results/2_Bavaria/summary.md) | The same for Bavaria's 96 districts and 7 Regierungsbezirke |
| 3 | [results/3_Owners](results/3_Owners/summary.md) | How many private security firms per state, their trend since 2014, and their legal form (who runs them) |

## Headline results

- **Germany:** 272,919 workers in private guarding firms (WZ 80.1) against 88.5 million counted event visits a year, or 308.5 workers per 100,000 visits. Fewest per visit: Bremen, Hamburg and Bayern. Below average both per event visit *and* per resident: Bayern, Nordrhein-Westfalen, Niedersachsen and Baden-Württemberg.
- **Bavaria:** 74,476 people in security occupations against 30.5 million counted visits. Mittelfranken (Nürnberg and Fürth) and Oberbayern (Munich) are thinnest per visit; Rosenheim (Stadt) and Kulmbach are the two districts below average on both lenses.
- **Owners:** 4,517 VAT-registered private security firms in 2024 (+23% since 2014). Bayern has 648 (2nd after NRW) but only 4.9 per 100,000 residents (10th of 16). 43% of firms are sole proprietors with 8% of turnover; 50% are GmbHs with 65% of turnover.

## Folder layout

```
README.md                      this file
results/
  README.md                    index of the three parts
  1_Germany/  2_Bavaria/  3_Owners/
                               summary.md + maps/charts (PNG) + tables (CSV)
code/
  build_results.py             builds everything in results/
  fetch_owners_data.py         downloads the Destatis tables for Part 3
  secmap/
    data.py                    paths and loaders
    metrics.py                 supply-vs-demand metrics (same calculations as the dashboard)
    figures.py                 maps and charts (matplotlib)
    genesis.py                 Destatis GENESIS-Online download without an account
  dashboard/                   page code and dataset definitions of the claude.ai dashboard
  requirements.txt
data/raw/
  dashboard/                   the 7 data files behind the dashboard (Parts 1 and 2)
  destatis/                    VAT statistics downloaded by fetch_owners_data.py (Part 3)
```

## Running it

Python 3.11 or newer. From this folder:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r code\requirements.txt
.venv\Scripts\python code\fetch_owners_data.py   # optional: refresh the Destatis data (needs internet)
.venv\Scripts\python code\build_results.py       # rebuilds results\ from data\raw\
```

`build_results.py` deletes and rewrites `results/1_Germany`, `results/2_Bavaria` and `results/3_Owners`.

## Data sources

| Used in | Data | Source, reference date |
|---|---|---|
| Part 1 | Workers in WZ 2008 class 80.1 "Private Wach- und Sicherheitsdienste", insured + minijobs, by place of work | Statistik der Bundesagentur für Arbeit, Beschäftigte nach Wirtschaftszweigen – Länder (Quartalszahlen), 31.03.2026 |
| Part 1 | Residents by state | Destatis, 31.12.2025 (census-based) |
| Part 1 | 118 recurring crowd events with annual visits | football leagues 1–3 2025/26 (diefalsche9.de), DSB Volksfest study 2023, city festivals > 1M visits, largest fairs 2025, top-10 music festivals; each row names its source |
| Part 2 | People in security occupations (KldB 2010 group 53), insured + minijobs, by district | Bundesagentur für Arbeit, Regionalreport über Beschäftigte, 31.03.2026 |
| Part 2 | Residents by district | Destatis Gemeindeverzeichnis, 31.12.2024 |
| Part 2 | 33 Bavarian events with annual visits | as above, plus DEL ice hockey, BAYERN TOURISMUS, Christmas markets Munich/Nuremberg |
| Parts 1–3 | State and district outlines | deutschlandGeoJSON (isellsoap, GitHub), based on DIVA-GIS, simplified |
| Part 3 | VAT-registered firms and taxable turnover in WZ 80.10, by state, 2014–2024 | Destatis GENESIS 73311-0011, Umsatzsteuerstatistik (Voranmeldungen) |
| Part 3 | The same for Germany, 2009–2024 | Destatis GENESIS 73311-0002 |
| Part 3 | The same for Germany by legal form, 2020–2024 | Destatis GENESIS 73311-0005 |

## Caveats

- **Supply is total headcount**, not event staff: object protection, aviation security and public contracts dominate. Read the maps as a relative indicator of where local supply is stretched, not as a staffing count.
- **Demand covers large recurring events only.** Christmas markets (outside Bavaria), arena concerts, carnival and demonstrations are missing, which understates demand in Berlin, Saxony and Thuringia.
- **Part 2 is not comparable with Part 1.** At district level only the occupation count (KldB 53) is published, not industry 80.1; it includes in-house security and airport screeners (Freising, Erding).
- **Part 3 counts firms at their seat**, with all their branches' turnover, and leaves out firms with turnover up to €22,000 (€17,500 before 2020). The 2020 dip in firm numbers coincides with that threshold change.
- **Bavarian districts in Part 3:** security-firm counts per district are not available from open sources (state-level VAT data only; district data only for broad sections). If you export them from the Bavarian State Office's GENESIS database (statistic 52111), save them as `data/raw/manual/bavaria_firms_by_district.csv` with columns `ags,firms` (optional `source`) and rerun `build_results.py`; two district maps are then added to `results/3_Owners`.
- `code/secmap/genesis.py` uses the public API behind the GENESIS-Online web app, which needs no account but is not a documented interface and may change. The official web service needs a free registration.
