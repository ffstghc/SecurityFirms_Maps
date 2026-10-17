# Part 3 — Owners: how many private security firms there are, and where

In 2024 Germany had **4,517 VAT-registered private guarding and security firms** (WZ 2008 class 80.10), +23% since 2014. That is 5.4 firms per 100,000 residents, and about 60 security workers per firm. Sole proprietors make up 43% of the firms but take only 8% of the turnover; GmbHs are 50% of the firms and take 65% of the turnover. Since 2020 the GmbH share of firms rose from 42% to 50% while sole proprietors fell from 49% to 43%.

Most firms are registered in Nordrhein-Westfalen (944), Bayern (648) and Hessen (488). Relative to population, Berlin leads (12.5 firms per 100,000 residents), followed by Brandenburg (8.2) and Hessen (7.8); Baden-Württemberg (3.7) and Saarland (3.3) have the fewest. The number of firms grew fastest in Berlin (+92%) and Hamburg (+76%) and fell most in Sachsen-Anhalt (-19%).

## Bavaria

- **648 firms** in 2024, rank 2 of 16 by number; +11% since 2014 (Germany +23%).
- **4.9 firms per 100,000 residents**, rank 10 of 16 (1 = densest; Germany 5.4).
- **61 security workers per firm** (Germany 60): 39,266 WZ 80.1 workers on 31 Mar 2026 ÷ 648 firms.
- **€1,470 million** taxable turnover, €2,269k per firm.

### Bavarian districts

**Not available by district from open sources.** The VAT statistic is published by state only. At district level, Regionalstatistik.de offers firm counts only for broad WZ sections (security falls under section N together with cleaning, temp agencies, travel agencies and more), and the Bavarian State Office for Statistics keeps finer industry detail per district in its GENESIS database (www.statistikdaten.bayern.de, statistic 52111 Unternehmensregister), which can only be queried interactively or with a registered account. To add the district map, export security firms (WZ 80.1 or 80) per district from there and save them as `data/raw/manual/bavaria_firms_by_district.csv` with columns `ags,firms`; `build_results.py` then draws `map_3_bavaria_firms_per_100k_residents.png` and `map_4_bavaria_workers_per_firm.png` automatically.

## Firms by state

| State | Firms 2014 | Firms 2024 | Change % | Per 100k residents | Workers per firm | Turnover per firm (€k) |
|:---|---:|---:|---:|---:|---:|---:|
| Nordrhein-Westfalen | 721 | 944 | +31% | 5.2 | 56 | 4,115 |
| Bayern | 585 | 648 | +11% | 4.9 | 61 | 2,269 |
| Hessen | 334 | 488 | +46% | 7.8 | 62 | 2,602 |
| Berlin | 241 | 462 | +92% | 12.5 | 49 | 2,281 |
| Baden-Württemberg | 384 | 415 | +8% | 3.7 | 70 | 2,950 |
| Niedersachsen | 286 | 357 | +25% | 4.5 | 59 | 2,773 |
| Brandenburg | 177 | 208 | +18% | 8.2 | 38 | 1,643 |
| Sachsen | 191 | 201 | +5% | 5.0 | 85 | 2,520 |
| Rheinland-Pfalz | 176 | 171 | -3% | 4.1 | 41 | 1,024 |
| Schleswig-Holstein | 150 | 153 | +2% | 5.2 | 70 | 4,353 |
| Hamburg | 70 | 123 | +76% | 6.6 | 97 | 2,724 |
| Sachsen-Anhalt | 131 | 106 | -19% | 5.0 | 59 | 2,961 |
| Thüringen | 79 | 88 | +11% | 4.2 | 54 | 1,361 |
| Mecklenburg-Vorpommern | 80 | 74 | -7% | 4.7 | 71 | 2,930 |
| Bremen | 33 | 46 | +39% | 6.5 | 87 | 1,979 |
| Saarland | 34 | 33 | -3% | 3.3 | 79 | 879 |

## Legal form, Germany 2024

| Legal form | Firms | Share of firms % | Turnover (€M) | Share of turnover % |
|:---|---:|---:|---:|---:|
| GmbH | 2,237 | 49.5 | 8,293 | 65.4 |
| Sole proprietors | 1,946 | 43.1 | 1,030 | 8.1 |
| KG | 240 | 5.3 | 3,206 | 25.3 |
| OHG, GbR | 80 | 1.8 | 60 | 0.5 |
| AG, KGaA, other | 8 | 0.2 | 97 | 0.8 |
| not disclosed | 6 | 0.1 | 1 | 0.0 |

"AG, KGaA, other" also holds cooperatives, public bodies and other legal forms; "not disclosed" is the difference to the published total where Destatis suppresses a cell.

## Files

- `map_1_firms_per_100k_residents.png` — firm density by state, labelled with the number of firms
- `map_2_workers_per_firm.png` — security workers per registered firm
- `chart_firms_by_state.png`, `chart_firm_change_by_state.png`, `chart_firms_trend.png`, `chart_legal_forms.png`
- `firms_by_state.csv` — firms 2014–2024, density, workers per firm, turnover, and firms in 80.20 (alarm systems) and 80.30 (detectives)
- `firms_germany_2009_2024.csv` — national series for division 80 and its three classes
- `legal_forms_germany_2020_2024.csv` — firms and turnover by legal form

## How to read this

**What counts as a firm** — a business that filed VAT advance returns in the year with taxable turnover above €22,000 (€17,500 before 2020), classified by its main activity as WZ 2008 class 80.10 "Private Wach- und Sicherheitsdienste". Small businesses below the threshold and annual-only filers are not counted, so solo guards and very small firms are understated. Source: Destatis, Umsatzsteuerstatistik (Voranmeldungen), GENESIS tables 73311-0011 (states), 73311-0002 (Germany) and 73311-0005 (legal forms); latest year 2024.

**Where a firm counts** — at its seat (the tax office of the head office). A firm with branches in several states counts once, with its whole turnover, in its head-office state; workers in Part 1 count where they work. Workers per firm therefore mixes two geographies: it is high where many staff work for firms based in another state or for a few large firms (Hamburg 97, Bremen 87, Sachsen 85), and low where many small firms are registered or firms' staff work across the border (Brandenburg 38, Rheinland-Pfalz 41). Turnover per firm is likewise high where large groups have their head office.

**Owner structure** — legal form is the closest official proxy for who owns a firm: a sole proprietor is one person; GmbH, KG and AG are companies whose owners the statistic does not name.
