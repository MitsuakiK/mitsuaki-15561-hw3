"""Q6: Which regular customers have gone quiet and may be lost?"""
import numpy as np
import pandas as pd

import common as c

MIN_ORDERS = 3
RATIO = 2.0
MIN_DAYS = 60
BACKTEST_CUTOFFS = ["1997-08-06", "1997-11-06", "1998-01-06"]
FOLLOW_UP_DAYS = 120


def customer_status(orders, as_of, ratio=RATIO, min_days=MIN_DAYS):
    """Flag customers who are silent far longer than their usual gap.

    At risk means at least ``MIN_ORDERS`` orders, days since the last
    order >= ``ratio`` x the median gap between orders, and days since
    the last order >= ``min_days``. Only orders up to ``as_of`` count.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.
        as_of (pandas.Timestamp): Date the status is measured on.
        ratio (float): Minimum silence as a multiple of the usual gap.
        min_days (int): Minimum days since the last order.

    Returns:
        pandas.DataFrame: One row per customer (index CustomerID) with
        order count, last order, usual gap, days since, overdue ratio,
        revenue in the 12 months to ``as_of``, and ``at_risk``.
    """
    o =orders[orders["OrderDate"] <= as_of].sort_values("OrderDate")
    gaps = o.groupby("CustomerID")["OrderDate"].diff().dt.days
    o = o.assign(Gap=gaps)
    yr = o[o["OrderDate"] > as_of - pd.Timedelta(days=365)]
    t = o.groupby("CustomerID").agg(
        company=("CompanyName", "first"), country=("Country", "first"),
        orders=("OrderID", "count"), last_order=("OrderDate", "max"),
        usual_gap=("Gap", "median"))
    t["revenue_12m"] = yr.groupby("CustomerID")["Revenue"].sum()
    t["revenue_12m"] = t["revenue_12m"].fillna(0)
    t["days_since"] = (as_of - t["last_order"]).dt.days
    t["overdue_ratio"] = t["days_since"] / t["usual_gap"]
    t["at_risk"] = ((t["orders"] >= MIN_ORDERS) & (t["overdue_ratio"] >= ratio)
                    & (t["days_since"] >= min_days))
    return t


def current_list(orders):
    """List at-risk customers as of the last date in the data.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.

    Returns:
        pandas.DataFrame: Status table from ``customer_status`` for
        all customers. Also prints the list and saves
        q6_customer_status.csv.
    """
    c.header(f"Q6.1 At-risk customers as of {c.DATA_END.date()} "
             f"(>= {MIN_ORDERS} orders, silent >= {RATIO:.0f}x their usual gap and >= {MIN_DAYS} days)")
    t = customer_status(orders, c.DATA_END)
    print(f"Customers: {len(t)}; with >= {MIN_ORDERS} orders: {(t['orders'] >= MIN_ORDERS).sum()}; "
          f"with 1-2 orders: {(t['orders'] < MIN_ORDERS).sum()}")
    risk = t[t["at_risk"]].sort_values("revenue_12m", ascending=False)
    cols = ["company", "country", "orders", "last_order", "usual_gap", "days_since",
            "overdue_ratio", "revenue_12m"]
    print(risk[cols].round({"overdue_ratio": 1, "revenue_12m": 0}).to_string())
    print(f"\nAt-risk: {len(risk)} customers, 12-month revenue ${risk['revenue_12m'].sum():,.0f} "
          f"({risk['revenue_12m'].sum() / t['revenue_12m'].sum():.1%} of all 12-month revenue)")
    print("Customers with only 1-2 orders:")
    print(t[t["orders"] < MIN_ORDERS][["company", "orders", "last_order", "revenue_12m"]]
          .to_string())
    c.save_table(t.sort_values("overdue_ratio", ascending=False), "q6_customer_status")
    return t


def sensitivity(orders):
    """Show how the at-risk list changes with other thresholds.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.

    Returns:
        None. Prints to standard output.
    """
    c.header("Q6.2 Sensitivity: how the list changes with the threshold")
    base = set(customer_status(orders, c.DATA_END).query("at_risk").index)
    for ratio in [1.5, 2.0, 3.0]:
        for min_days in [45, 60, 90]:
            t = customer_status(orders, c.DATA_END, ratio, min_days)
            r = t[t["at_risk"]]
            print(f"ratio>={ratio}, days>={min_days}: {len(r):2d} customers, "
                  f"${r['revenue_12m'].sum():>9,.0f}; overlap with base list "
                  f"{len(base & set(r.index))}/{len(base)}")


def backtest(orders):
    """Check whether past flags predicted no order in the next period.

    For each cutoff in ``BACKTEST_CUTOFFS``, compares the share of
    flagged and unflagged customers who ordered within
    ``FOLLOW_UP_DAYS`` days.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.

    Returns:
        None. Prints results and saves q6_backtest.csv.
    """
    c.header(f"Q6.3 Backtest: did flagged customers really go quiet? "
             f"(next {FOLLOW_UP_DAYS} days after each cutoff)")
    rows = []
    for cut in BACKTEST_CUTOFFS:
        cut = pd.Timestamp(cut)
        t = customer_status(orders, cut)
        t = t[t["orders"] >= MIN_ORDERS]
        nxt = orders[(orders["OrderDate"] > cut) &
                     (orders["OrderDate"] <= cut + pd.Timedelta(days=FOLLOW_UP_DAYS))]
        t["ordered_next"] = t.index.isin(nxt["CustomerID"])
        for flag, g in t.groupby("at_risk"):
            rows.append({"cutoff": cut.date(), "flagged": flag, "customers": len(g),
                         "share_ordered_next": g["ordered_next"].mean()})
    b = pd.DataFrame(rows)
    print(b.round(2).to_string(index=False))
    c.save_table(b, "q6_backtest", index=False)


def chart(t):
    """Plot days since last order against each customer's usual gap.

    Args:
        t (pandas.DataFrame): Status table from ``current_list``.

    Returns:
        None. Saves q6_at_risk_customers.png.
    """
    d = t[t["orders"] >= MIN_ORDERS]
    fig, ax = c.new_figure(8, 5)
    sizes = 20 + d["revenue_12m"] / d["revenue_12m"].max() * 400
    base = d[~d["at_risk"]]
    risk = d[d["at_risk"]]
    ax.scatter(base["usual_gap"], base["days_since"], s=sizes[base.index],
               color=c.GRAY, alpha=0.45, edgecolor=c.SURFACE, linewidth=1.5,
               label="Ordering on rhythm")
    ax.scatter(risk["usual_gap"], risk["days_since"], s=sizes[risk.index],
               color=c.ORANGE, edgecolor=c.SURFACE, linewidth=1.5,
               label=f"At risk: silent ≥ {RATIO:.0f}× usual gap and ≥ {MIN_DAYS} days")
    xs = np.linspace(0, d["usual_gap"].max() * 1.05, 50)
    ax.plot(xs, np.maximum(RATIO * xs, MIN_DAYS), color=c.ORANGE, linewidth=1)
    for _, r in risk.iterrows():
        ax.annotate(r["company"], (r["usual_gap"], r["days_since"]),
                    xytext=(6, 4), textcoords="offset points", fontsize=8, color=c.INK2)
    c.style_axes(ax, "A handful of regular customers have gone quiet for far longer "
                     "than their usual rhythm",
                 "Customer's usual days between orders (median)",
                 f"Days since last order (as of {c.DATA_END:%b %d, %Y})",
                 subtitle=f"Customers with ≥ {MIN_ORDERS} orders. Bubble size = revenue in "
                          "the last 12 months. Orange line = at-risk threshold.")
    ax.set_xlim(0, d["usual_gap"].max() * 1.05)
    ax.set_ylim(0, d["days_since"].max() * 1.1)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right", markerscale=0.5)
    c.save_figure(fig, "q6_at_risk_customers")


def main():
    """Run the full Q6 analysis.

    Args:
        None.

    Returns:
        None. Prints results and writes Q6 tables and the figure.
    """
    tables, lines, orders = c.load_all()
    t = current_list(orders)
    sensitivity(orders)
    backtest(orders)
    chart(t)


if __name__ == "__main__":
    main()
