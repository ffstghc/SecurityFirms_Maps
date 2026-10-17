# Dashboard code: "Security Supply vs Event Demand"

The interactive dashboard from our conversation lives on claude.ai:
https://claude.ai/artifact/WuZLv2Bf92mzqabN7r7t23 (private to your account).

It was built on claude.ai's *Dashboard* artifact type, which loads the datasets
and provides `dash.data`, `dash.calc` and `d3`. These two files are its complete
content:

- `index.html` — the page: tabs "Germany by state" and "Bavaria by district",
  the KPI tiles, maps, rankings and event tables, and the calculations
  (`state_metrics`, `national`, `by_metrics`, `by_total`).
- `datasets.json` — the dashboard title, its saved filter settings, and the
  definition of each of the 7 datasets (description, source, date). The data
  files themselves are in `data/raw/dashboard/`.

`index.html` only runs inside that dashboard type, not as a standalone page. The
Python code in `code/secmap/metrics.py` repeats the same calculations one-to-one,
so `code/build_results.py` reproduces the dashboard's numbers as static maps,
charts and tables.
