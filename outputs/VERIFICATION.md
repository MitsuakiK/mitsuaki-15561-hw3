# Independent Verification in Excel

Key numbers produced by `python run_all.py` were recomputed by hand in
Microsoft Excel. The check used a copy of the original workbook, not the
file in `data/`. All 8 checks matched.

## Setup
Three helper columns were added to the `Orders Details` sheet:
- `OrderDate`: `=XLOOKUP(A2, Orders!A:A, Orders!D:D)`
- `CustomerID`: `=XLOOKUP(A2, Orders!A:A, Orders!B:B)`
- `Revenue`: `=C2*D2*(1-ROUND(E2,2))`

## Checks

| # | Question | What was checked | Excel method | Python result | Excel |
|---|----------|------------------|--------------|---------------|-------|
| 1 | All | Total revenue | `SUM` of Revenue | 1,265,793.04 | Match |
| 2 | Q1 | Old vs current price (order 10248, product 11) | Lookup | 14.0 vs list 21.0 | Match |
| 3 | Q1 | Units in the 180 days before / after 1997-04-07 | `SUMIFS` on OrderDate | 11,848 / 12,084 | Match |
| 4 | Q2 | Orders in Jan–Apr 1997 / 1998 | `COUNTIFS` on Orders | 123 / 256 | Match |
| 5 | Q3 | Late orders by deadline window (14 / 28 days) | Helper columns + PivotTable | 12 of 68 / 25 of 682 | Match |
| 6 | Q4 | Lines and mean quantity at 0% and 25% discount | PivotTable | 1,317 lines, 21.7 / 154 lines, 28.2 | Match |
| 7 | Q6 | Mère Paillarde (MEREP): order count, last order | Filter | 13 orders, 1997-10-30 | Match |
| 8 | Q7 | Revenue of top customer QUICK | `SUMIFS` on CustomerID | 110,277.30 (8.7%) | Match |

Not re-checked in Excel: the statistical tests (Fisher exact, Mann-Whitney,
Kruskal-Wallis, Wilcoxon, permutation and bootstrap). These come from
`scipy`, and the permutation and bootstrap results use fixed random seeds,
so they are the same on every run.
