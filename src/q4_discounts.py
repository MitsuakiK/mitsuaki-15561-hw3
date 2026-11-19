"""Q4: Do deeper discounts go with larger purchase quantities?"""
import numpy as np
import pandas as pd
from scipy import stats

import common as c

STANDARD_RATES = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]
SEED = 561
N_BOOT = 5000


def prepare(lines):
    """Keep standard-rate lines and add quantity relative to the norm.

    ``RelQty`` is line quantity divided by the median undiscounted
    quantity of the same product. Lines of products never sold
    without a discount are dropped.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.

    Returns:
        pandas.DataFrame: Copy of the kept lines with ``RelQty``.
    """
    d =lines[lines["Discount"].isin(STANDARD_RATES)].copy()
    print(f"Lines with standard rates: {len(d)} of {len(lines)} "
          f"(dropped {len(lines) - len(d)} lines with 1-6% rates, all in order 11077)")
    base = d[d["Discount"] == 0].groupby("ProductID")["Quantity"].median()
    d["RelQty"] = d["Quantity"] / d["ProductID"].map(base)
    d = d[d["RelQty"].notna()]
    return d


def bootstrap_ci(x, rng):
    """Compute a 95% bootstrap interval for the mean.

    Args:
        x (numpy.ndarray): Sample values.
        rng (numpy.random.Generator): Random generator; advanced by
            ``N_BOOT`` resamples.

    Returns:
        numpy.ndarray: Lower and upper bounds (2.5th and 97.5th
        percentiles of the resampled means).
    """
    means = [rng.choice(x, len(x)).mean() for _ in range(N_BOOT)]
    return np.percentile(means, [2.5, 97.5])


def quantity_by_rate(d):
    """Compare relative quantity across discount rates.

    Args:
        d (pandas.DataFrame): Lines from ``prepare``.

    Returns:
        pandas.DataFrame: One row per rate with line count, quantity
        measures, bootstrap interval, and dollars given away. Also
        prints tests and saves q4_quantity_by_rate.csv.
    """
    c.header("Q4.1 Quantity per line by discount rate")
    rng = np.random.default_rng(SEED)
    rows = []
    for rate, g in d.groupby("Discount"):
        lo, hi = bootstrap_ci(g["RelQty"].values, rng)
        rows.append({"rate": rate, "lines": len(g),
                     "mean_quantity": g["Quantity"].mean(),
                     "median_quantity": g["Quantity"].median(),
                     "mean_rel_qty": g["RelQty"].mean(), "ci_low": lo, "ci_high": hi,
                     "discount_cost": (g["Gross"] - g["Revenue"]).sum()})
    t = pd.DataFrame(rows)
    print("rel_qty = quantity / median undiscounted quantity of the same product")
    print(t.round(3).to_string(index=False))
    disc = d[d["Discount"] > 0]
    kw = stats.kruskal(*[g["RelQty"] for _, g in disc.groupby("Discount")])
    print(f"\nKruskal-Wallis across 5/10/15/20/25%: p={kw.pvalue:.3f} "
          "(large p = no evidence that deeper discounts go with bigger quantities)")
    rho = stats.spearmanr(disc["Discount"], disc["RelQty"])
    print(f"Spearman correlation, rate vs relative quantity (discounted lines): "
          f"rho={rho.statistic:.3f}, p={rho.pvalue:.3f}")
    mw = stats.mannwhitneyu(disc["RelQty"], d.loc[d["Discount"] == 0, "RelQty"])
    print(f"Discounted vs undiscounted relative quantity: Mann-Whitney p={mw.pvalue:.4f}")
    c.save_table(t, "q4_quantity_by_rate", index=False)
    return t


def by_year(d):
    """Repeat the rate-vs-quantity comparison within each year.

    Args:
        d (pandas.DataFrame): Lines from ``prepare``.

    Returns:
        None. Prints to standard output.
    """
    c.header("Q4.2 Robustness: the same pattern in each year")
    t = d.pivot_table(index="Discount", columns=d["OrderDate"].dt.year,
                      values="RelQty", aggfunc="mean")
    print(t.round(2).to_string())
    for year, g in d[d["Discount"] > 0].groupby(d["OrderDate"].dt.year):
        rho = stats.spearmanr(g["Discount"], g["RelQty"])
        print(f"{year}: Spearman rho={rho.statistic:+.3f}, p={rho.pvalue:.3f}, n={len(g)}")


def how_assigned(lines, orders):
    """Describe how discounts vary by order, customer, and employee.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.
        orders (pandas.DataFrame): Order totals; not used.

    Returns:
        None. Prints results and saves q4_by_employee.csv.
    """
    c.header("Q4.3 How are discounts given? (per order vs per line)")
    per_order = lines.groupby("OrderID")["Discount"].agg(["nunique", "max"])
    multi = per_order[per_order["max"] > 0]
    print(f"Orders with any discount: {len(multi)} of {len(per_order)}; "
          f"of these, {(multi['nunique'] == 1).mean():.0%} use one rate on every line")
    cust = lines.groupby("CompanyName").agg(lines=("OrderID", "count"),
                                            share_disc=("Discount", lambda s: (s > 0).mean()))
    cust = cust[cust["lines"] >= 20]
    print(f"Customers with >=20 lines: share of lines discounted ranges "
          f"{cust['share_disc'].min():.0%}-{cust['share_disc'].max():.0%}, "
          f"median {cust['share_disc'].median():.0%}")
    emp = lines.groupby("LastName").agg(lines=("OrderID", "count"),
                                        share_disc=("Discount", lambda s: (s > 0).mean()),
                                        avg_rate_when_disc=("Discount", lambda s: s[s > 0].mean()))
    print(emp.sort_values("share_disc").round(2).to_string())
    c.save_table(emp, "q4_by_employee")


def repeat_behavior(orders, lines):
    """Compare reorder within 90 days after discounted vs other orders.

    Only orders placed at least 90 days before the data ends are
    used. Results are associations, not causal effects.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.
        lines (pandas.DataFrame): Order lines from ``common.load_all``.

    Returns:
        None. Prints results and saves q4_repeat_behavior.csv.
    """
    c.header("Q4.4 Do customers come back sooner after a discounted order? (association only)")
    disc = lines.groupby("OrderID")["Discount"].max().rename("MaxDiscount")
    o = orders.merge(disc, on="OrderID").sort_values(["CustomerID", "OrderDate"])
    o["NextOrder"] = o.groupby("CustomerID")["OrderDate"].shift(-1)
    o["DaysToNext"] = (o["NextOrder"] - o["OrderDate"]).dt.days
    o = o[o["OrderDate"] < c.DATA_END - pd.Timedelta(days=90)]  # allow time to reorder
    o["Returned90"] = o["DaysToNext"] <= 90
    o["Discounted"] = o["MaxDiscount"] > 0
    t = o.groupby("Discounted").agg(orders=("OrderID", "count"),
                                    median_days_to_next=("DaysToNext", "median"),
                                    reorder_within_90d=("Returned90", "mean"))
    print(t.round(3).to_string())
    a, b = o[o["Discounted"]], o[~o["Discounted"]]
    tab = [[a["Returned90"].sum(), (~a["Returned90"]).sum()],
           [b["Returned90"].sum(), (~b["Returned90"]).sum()]]
    print(f"Fisher exact test on reorder-within-90-days: p={stats.fisher_exact(tab)[1]:.3f}")
    print("Caution: frequent buyers may simply receive more discounts. Check within "
          "the same customer:")
    per = o.pivot_table(index="CustomerID", columns="Discounted",
                        values="Returned90", aggfunc="mean").dropna()
    w = stats.wilcoxon(per[True], per[False])
    print(f"Customers with both kinds of orders: {len(per)}; mean reorder-within-90d "
          f"after discounted {per[True].mean():.0%} vs undiscounted "
          f"{per[False].mean():.0%}; Wilcoxon p={w.pvalue:.3f}")
    freq = o.groupby("CustomerID").agg(n=("OrderID", "count"),
                                       share_disc=("Discounted", "mean"))
    rho = stats.spearmanr(freq["n"], freq["share_disc"])
    print(f"Across customers: number of orders vs share of orders discounted: "
          f"rho={rho.statistic:.2f}, p={rho.pvalue:.3f}")
    c.save_table(t, "q4_repeat_behavior")


def cost_scenarios(lines):
    """Print discount cost and savings under 5/10/15% caps.

    Savings assume quantities would not change under a cap.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.

    Returns:
        None. Prints to standard output.
    """
    c.header("Q4.5 What do discounts cost, and what would a cap save? (hypothetical)")
    total = (lines["Gross"] - lines["Revenue"]).sum()
    print(f"Total given away: ${total:,.0f} ({total / lines['Gross'].sum():.1%} of gross)")
    for cap in [0.05, 0.10, 0.15]:
        over = lines[lines["Discount"] > cap]
        saved = (over["Gross"] * (over["Discount"] - cap)).sum()
        print(f"Cap at {cap:.0%}: affects {len(over)} lines; saves ${saved:,.0f} "
              f"IF quantities stay the same")
    recent = lines[(lines["OrderDate"] >= "1998-01-01") & (lines["Month"] <= c.LAST_FULL_MONTH)]
    print(f"Jan-Apr 1998 given away: ${(recent['Gross'] - recent['Revenue']).sum():,.0f}")


def chart(t):
    """Draw mean relative quantity with intervals by discount rate.

    Args:
        t (pandas.DataFrame): Table from ``quantity_by_rate``.

    Returns:
        None. Saves q4_quantity_by_discount.png.
    """
    fig, ax = c.new_figure()
    x = np.arange(len(t))
    y = t["mean_rel_qty"].values
    ax.errorbar(x, y, yerr=[y - t["ci_low"], t["ci_high"] - y], fmt="o",
                color=c.BLUE, ecolor=c.BLUE, elinewidth=1.5, capsize=0,
                markersize=8, markeredgecolor=c.SURFACE, markeredgewidth=2)
    for xi, yi, lo, n, cost in zip(x, y, t["ci_low"], t["lines"], t["discount_cost"]):
        label = f"{yi:.2f}\n{n} lines" + (f"\n${cost / 1000:.0f}k given away" if cost > 0 else "")
        ax.text(xi, lo - 0.03, label, fontsize=8.5, color=c.INK2, va="top",
                ha="center")
    ax.axhline(1, color=c.AXIS, linewidth=0.8)
    ax.set_xticks(x, [f"{r:.0%}" for r in t["rate"]])
    ax.set_xlim(-0.5, len(t) - 0.5)
    ax.set_ylim(0.8, 2.05)
    c.style_axes(ax, "Discounted lines are larger, but 25% off buys no more than 5% off",
                 "Discount rate on the order line",
                 "Quantity vs. product's usual\n(undiscounted median = 1.0)",
                 subtitle="Mean relative quantity with 95% bootstrap interval. "
                          "Relative quantity = line quantity / median undiscounted "
                          "quantity of the same product.")
    c.save_figure(fig, "q4_quantity_by_discount")


def main():
    """Run the full Q4 analysis.

    Args:
        None.

    Returns:
        None. Prints results and writes Q4 tables and the figure.
    """
    tables, lines, orders = c.load_all()
    c.header("Q4.0 Data used")
    d = prepare(lines)
    t = quantity_by_rate(d)
    by_year(d)
    how_assigned(lines, orders)
    repeat_behavior(orders, lines)
    cost_scenarios(lines)
    chart(t)


if __name__ == "__main__":
    main()
