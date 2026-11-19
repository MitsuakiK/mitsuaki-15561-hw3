# Northwind Business Analysis

An analysis of the Northwind sample database (orders from July 1996 to
May 1998) for MIT 15.561, HW3. It answers seven business questions about
pricing, growth, shipping, discounts, markets, customer retention, and
revenue concentration.

- **Webpage:** https://mitsuakik.github.io/mitsuaki-15561-hw3/
- **All numbers, figures, and tables** on the webpage come from one
  command: `python run_all.py`.

## Reproduce the results

Requirements: Python 3.13 (tested with 3.13.2) and the packages in
`requirements.txt`.

1. Get the code and go into the folder.

   ```bash
   git clone https://github.com/MitsuakiK/mitsuaki-15561-hw3.git
   cd mitsuaki-15561-hw3
   ```

2. Create a virtual environment and install the packages.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run every analysis.

   ```bash
   python run_all.py
   ```

   This takes about 1–2 minutes. It reads `data/Northwind Database.xlsx`
   and rewrites everything in `outputs/figures/`, `outputs/tables/`, and
   `outputs/logs/`.

4. Check the results. Each question's printed numbers are in
   `outputs/logs/qN_*.txt`, its tables in `outputs/tables/qN_*.csv`, and
   its chart in `outputs/figures/qN_*.png`. A plain-language summary of
   the findings is in `outputs/RESULTS_SUMMARY.md`.

The runs are deterministic. The bootstrap and permutation tests use a
fixed random seed (561), so every run gives the same numbers. To run a
single question, use for example `python src/q3_rush_orders.py`.

## Questions and where to find them

| # | Question | Code | Figure |
|---|----------|------|--------|
| Q1 | Did the 25% price increase in April 1997 reduce demand? | `src/q1_price_increase.py` | `q1_units_price_change.png` |
| Q2 | What drove revenue growth in Jan–Apr 1998: more customers, more orders, or bigger orders? | `src/q2_growth_drivers.py` | `q2_growth_decomposition.png` |
| Q3 | Are orders with a 14-day deadline handled any faster? | `src/q3_rush_orders.py` | `q3_ship_days_by_deadline.png` |
| Q4 | Do deeper discounts buy larger orders or more repeat business? | `src/q4_discounts.py` | `q4_quantity_by_discount.png` |
| Q5 | Which country markets are growing or shrinking? | `src/q5_country_markets.py` | `q5_country_change.png` |
| Q6 | Which valuable customers are going quiet? | `src/q6_at_risk_customers.py` | `q6_at_risk_customers.png` |
| Q7 | How dependent is revenue on a few customers and one product? | `src/q7_concentration.py` | `q7_concentration_curve.png` |

## Repository layout

```
mitsuaki-15561-hw3/
├── run_all.py              # Runs Q1–Q7 and saves logs, tables, figures
├── requirements.txt        # Exact package versions
├── data/
│   └── Northwind Database.xlsx   # Course-provided dataset (unchanged)
├── src/                    # Final analysis code
│   ├── common.py           # Data loading, cleaning rules, chart style
│   └── q1_…py – q7_…py     # One script per business question
├── outputs/
│   ├── figures/            # Charts (PNG)
│   ├── tables/             # Result tables (CSV)
│   ├── logs/               # Printed output of each script
│   ├── RESULTS_SUMMARY.md  # Findings, facts vs. interpretation
│   └── VERIFICATION.md     # Key numbers re-checked by hand in Excel
└── exploration/            # Earlier steps, kept for transparency
    ├── 01_data_quality_check.py  # Data quality checks
    ├── 02–04_eda_*.py      # Exploratory analysis
    ├── DATA_DECISIONS.md   # How each data issue was handled
    ├── EDA_FINDINGS.md     # Patterns found while exploring
    └── QUESTION_CANDIDATES.md    # Candidate questions and how they were chosen
```

`src/` is the code behind the results. `exploration/` shows how the
questions were found. It is not needed to reproduce the results. Run its
scripts from the project folder, e.g.
`python exploration/01_data_quality_check.py`.

## Data handling

The source workbook is never modified. All cleaning happens in code
(`src/common.py`), following the decisions in
`exploration/DATA_DECISIONS.md`. The most important ones:

- **Revenue** = `UnitPrice × Quantity × (1 − Discount)` from the
  `Orders Details` sheet. `Product.Price` is today's list price, and all
  sales before 1997-04-07 were at 80% of it.
- **Constant-price revenue** values every sale at today's list price.
  It is used where the April 1997 price change would otherwise distort a
  comparison over time (Q2, Q5).
- **Partial years:** the data starts in July 1996 and ends on
  1998-05-06. Comparisons use the same calendar months in each year
  (e.g., Jan–Apr 1997 vs. Jan–Apr 1998), and May 1998 is left out of
  monthly trends.
- **Extra Product columns** (`Cheap`, `IsCheap`, `NewPrice`, …) are not
  part of the original database and are ignored.
- **Country** means the ordering customer's country, not the ship-to
  address.
- **Unshipped orders (21)** count toward revenue but are left out of
  shipping-time analysis.
- **Discounts** are rounded to 2 decimals (stored values look like
  0.0500000007).

## Verification

Eight key numbers (total revenue, Q1 units, Q2 order counts, Q3 late
orders, Q4 discount-line quantities, Q6 customer history, Q7 top-customer
revenue) were recomputed by hand in Excel and all matched. See
`outputs/VERIFICATION.md`.

## Limitations

- Northwind is a fictional teaching dataset. Some patterns, such as the
  single-day 25% price step and the round discount rates, may come from
  how the data was generated rather than real business behavior.
- The data covers only 22 months, with partial first and last years.
- All findings are associations. None of them prove cause and effect.

## Code documentation

Every Python file and function in this repository (`run_all.py`,
`src/`, and `exploration/`) has a Google-style docstring
describing its inputs and outputs. The docstrings were generated with the
course's `python-docstrings` skill for Claude Code
(`.claude/skills/python-docstrings/SKILL.md`) and reviewed by hand.
