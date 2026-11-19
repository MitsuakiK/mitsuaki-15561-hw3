# Results Summary (Step 4 draft)

All numbers come from `python run_all.py` (logs in `outputs/logs/`, tables in
`outputs/tables/`, figures in `outputs/figures/`). "Constant prices" = revenue
at today's list price, which removes the April 1997 price increase.

## Q1. Did the 25% across-the-board price increase in April 1997 reduce demand?
- Fact: Every order line before 1997-04-07 was at ~80% of today's list price; every line from 1997-04-07 on is at 100%.
- Fact: Units in the 180 days after vs before: +2% (11,848 → 12,084). Revenue: +17%. Orders +13%, customers +13%, units per order −10%.
- Fact: The same 54 customers bought +4.6% units after vs before (Wilcoxon p = 0.49: no significant change).
- Fact: Discounts were not raised to compensate (avg discount 6.2% → 5.8%).
- Fact: All three price tiers changed by +1% to +2% in units. Categories varied: Seafood +87%, Meat/Poultry −37%.
- Fact: Before the change, units were rising about 111 per month. From Apr to Nov 1997, actual units were 24% below that straight-line projection. Then growth resumed strongly from Dec 1997.
- Interpretation: There was no visible drop in demand, and revenue rose. But growth paused for about 8 months, and the data cannot tell whether the price change caused the pause. There is no comparison group, and the projection rests on only 9 points.
- Implication: The price rise appears to have been absorbed. Future price changes should be tested on part of the range first, so their effect can be measured.

## Q2. What drove the growth in Jan–Apr 1998?
- Fact: Revenue rose 2.21x at actual prices and 1.86x at constant prices.
  - Active customers rose 1.23x (65 → 80).
  - Orders per customer rose 1.69x (1.89 → 3.20).
  - Revenue per order fell to 0.89x.
- Fact: Order frequency explains about 85% of the (log) growth. The same pattern holds in two other comparisons: Nov–Apr (+58%) and Jul–Dec (+29%).
- Fact: Only 1 of the 21 customers who appear in 1998 but not in Jan–Apr 1997 was truly new. The other 20 were returning customers.
- Fact: The top 10 contributors account for 76% of the net change. Without the top 3, growth is still +67%. Without the top 1% of orders, it is still 1.88x.
- Implication: Growth comes from existing accounts buying more often, not from new customers. Smaller, more frequent orders also raise handling and shipping load. Acquisition of new customers has been almost nil since mid-1997.

## Q3. Are 14-day-deadline orders handled any faster?
- Fact: 14-day orders ship after the deadline 17.6% of the time (12 of 68), vs 3.7% for 28-day orders (Fisher p = 0.00004, odds ratio 5.6).
- Fact: Median ship time is 7.5 days for 14-day orders vs 7.0 days for 28-day orders. If anything, 14-day orders ship slower (mean 10.0 vs 8.3 days; Mann-Whitney p = 0.06).
- Fact: The gap holds within every shipper and every year, and in a permutation test within shipper × year strata (p = 0.0002).
- Fact: 14-day orders are 8% of shipped orders but 32% of late orders. They are larger on average ($1,969 vs $1,497).
- Note: "Late" here means shipped after the required date. Actual delivery dates are not in the data.
- Implication: The order queue appears to ignore deadlines. Flagging 14-day orders for priority picking could prevent most of the 12 late orders.

## Q4. Do deeper discounts buy larger orders or more repeat business?
- Fact: Discounted lines are about 30% larger than undiscounted ones, relative to each product's usual quantity.
- Fact: Among discounted lines, the rate does not matter. A 25% line is the same size as a 5% line (Kruskal-Wallis p = 0.34, Spearman rho = 0.04). This holds in every year.
- Fact: The 20–25% rates cost $55k of the $89k total given away.
- Fact: After a discounted order, customers reorder within 90 days 83% of the time, vs 64% after an undiscounted order. But frequent buyers get more discounts (rho = 0.62). Within the same customer, the gap shrinks to 78% vs 66% (p = 0.049).
- Hypothesis (not tested): Capping discounts at 10% would have saved about $36k if quantities stayed the same.
- Implication: Offering a discount is linked with larger orders and return visits, but deeper discounts show no extra effect. A test of a lower cap is worth running. Causality cannot be claimed from this data.

## Q5. Which country markets are growing or shrinking?
- Fact: At constant prices, Jan–Apr 1998 vs Jan–Apr 1997, the largest gains are USA +$46.8k, Germany +$44.1k and Brazil +$29.0k. The top 4 countries account for 71% of the total gain.
- Fact: 15 of 21 countries grew in all three comparisons.
- Fact: Each decline traces to one or two customers:
  - Denmark: one large Jan 1997 order from Simons bistro.
  - Canada: Mère Paillarde stopped ordering after Oct 1997.
  - Finland: Wartian Herkku.
  - Mexico: Tortuga Restaurante.
  - France: flat overall, with churn across its 10 customers.
- Fact: In 6 countries, one customer makes ≥ 70% of that country's revenue.
- Implication: Country is too coarse a unit for decisions here. Account-level attention matters more than market-level strategy.

## Q6. Which valuable customers are going quiet?
- Fact: 8 customers with ≥ 3 orders have been silent for ≥ 2x their usual gap and ≥ 60 days. Together they represent $51.8k (6.0%) of last-12-month revenue.
  - Top of the list: Berglunds snabbköp ($16.2k), Mère Paillarde ($12.9k, 188 days, 10.7x its usual gap), Seven Seas Imports ($7.2k).
- Fact: The list is stable across thresholds of 1.5x–2x and 45–90 days (7–8 customers).
- Fact (backtest): Flagged customers at earlier dates still reordered within 120 days 58–87% of the time, vs 80–93% for unflagged customers. Silence is a weak warning sign, not proof of loss.
- Implication: Use the list for a low-cost check-in call. Mère Paillarde, at 10x its usual gap, is the clearest case.

## Q7. How dependent is revenue on a few customers and one product?
- Fact: The top 3 customers (QUICK, ERNSH, SAVEA) bring 25% of revenue, and the top 10% of customers bring 43%.
- Fact: The customer HHI is 337, low by the usual 1,500 threshold, and the top-3 share is not trending up. It was 18%, 24%, 30% and 25% by half-year.
- Fact: Côte de Blaye alone is 11.2% of revenue (10.2% of the last 12 months). It sold only 24 order lines to 19 customers, and its share swings between 3% and 16% by half-year.
- Fact: Losing the top customer would remove 9.6% of last-12-month revenue. Losing the top 3 would remove 27.3%.
- Implication: The risk is moderate overall but real at the top. Key-account care for the top 3, and a backup source for the one wine supplier, are prudent steps.

## Limitations (all questions)
- Northwind is fictional. The single-day 25% price step, weekday-only orders and round discount rates may be artifacts of how the data was generated.
- The data covers 22 months with partial first and last years. Comparisons use equal calendar windows.
- All findings are associations, not causal effects.
