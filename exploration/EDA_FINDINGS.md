# Exploratory Findings (Step 2)

Source scripts: `exploration/02_eda_basics.py`, `03_eda_patterns.py`,
`04_eda_followups.py` (shared data prep in `prep.py`, applying
`DATA_DECISIONS.md`). Revenue = `UnitPrice * Quantity * (1 - Discount)`.
"Fact" = computed from the data. "Hypothesis" = not yet tested.

## Basic features and distributions
- Fact: $1,265,793 revenue, 830 orders, 89 active customers, 77 products.
- Fact: Order value is right-skewed: median $943, mean $1,525, max $16,388. Top 10% of orders = 38% of revenue.
- Fact: 34 of 89 customers make 80% of revenue; top 3 (QUICK, ERNSH, SAVEA) = 25%.
- Fact: Côte de Blaye alone = 11.2% of revenue.
- Fact: 39% of order lines are discounted; discounts cost $88,666 (6.5% of gross).
- Fact: Orders only Monday–Friday.

## Unusual values / unexpected patterns
- Fact: All 77 list prices rose exactly 25% (old = 80% of current) in the week of 1997-04-07. No overlap: every sale before uses the old price, every sale after uses the new one.
- Fact: Units sold did not drop after the price rise (Feb–Mar 1997: ~1,950/month; May 1997: 2,164; Oct 1997: 2,679).
- Fact: Order 11077 (last day) has 25 lines; it contains all 8 lines with 1–4%/6% discounts.
- Fact: Orders with a 14-day deadline are late 18% of the time vs 4% for 28-day orders, yet median ship time is the same (7.5 vs 7 days).
- Fact: Inventory snapshot: 38 of 69 active products hold < 1 month of stock at the Jan–Apr 1998 sales rate (snapshot date unknown).

## Group and time differences
- Fact: Monthly orders rose from 22 (Jul 1996) to 74 (Apr 1998); sharp acceleration from Dec 1997.
- Fact: Jan–Apr 1998 vs Jan–Apr 1997: revenue +121%; at constant prices +86%; customers 65 → 80; orders per customer 1.89 → 3.20; avg order $1,555 → $1,650.
- Fact: Jan–Apr growth varies by country: USA +169%, Germany +167%, Brazil +286%, but Canada −24%, Denmark −69%, Mexico −44%, Finland −45%, France +5%.
- Fact: Seafood +185% vs Grains/Cereals +32% (Jan–Apr comparison).
- Fact: Peacock is the top employee overall (18%) but is the only one whose Jan–Apr revenue fell (−12%).
- Fact: 5 customers have not ordered in 180+ days (incl. Mère Paillarde, Canada, $28,872 lifetime).
- Hypothesis / likely artifact: "new customers" fall from 42 (Q3 1996) to 1 (Q1 1998), but the data starts in July 1996, so early "new" customers are mostly existing customers seen for the first time.

## Relationships and combinations
- Fact: Discounted lines are larger on average (27.1 vs 21.7 units), but quantity is almost the same across 5–25% rates (25–28 units).
- Fact: Employees differ in how often they discount (32% of lines for Fuller/Leverling vs 50% for Buchanan); avg rate when discounted is similar (13–16%).
- Fact: Customer discount share is barely related to customer revenue (corr 0.12).
- Fact: Freight correlates with order revenue (0.76). Shippers have similar late rates (4–5%).
- Fact: Category mix differs by country (e.g., Venezuela 31% Dairy; Brazil 34% Beverages; France 19% Seafood).
- Fact: A customer is served by 5 different employees on average; both offices (USA, UK) serve all 21 countries.

## Limitation
Northwind is fictional. The clean 25% price step, weekday-only orders, and
round discount rates may be artifacts of how the data was generated.
