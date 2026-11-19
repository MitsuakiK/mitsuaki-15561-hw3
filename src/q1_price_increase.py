"""Q1: How did sales volume respond to the April 1997 price increase?"""
import numpy as np
import pandas as pd
from scipy import stats

import common as c


def window(lines, days, before):
    """Select lines in a window just before or after the price change.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.
        days (int): Window length in days.
        before (bool): True for the window ending on 1997-04-07;
            False for the window starting on it.

    Returns:
        pandas.DataFrame: Lines whose order date is in the window
        (start inclusive, end exclusive).
    """
    start = c.PRICE_CHANGE_DATE - pd.Timedelta(days=days) if before else c.PRICE_CHANGE_DATE
    end = c.PRICE_CHANGE_DATE if before else c.PRICE_CHANGE_DATE + pd.Timedelta(days=days)
    return lines[(lines["OrderDate"] >= start) & (lines["OrderDate"] < end)]


def verify_switch(lines):
    """Print the paid-to-list price ratios before and after the change.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.

    Returns:
        None. Prints to standard output.
    """
    c.header("Q1.0 Check: every line before 1997-04-07 is at 80% of list price, every line after at 100%")
    ratio = (lines["UnitPrice"] / lines["Price"]).round(2)
    before = lines["OrderDate"] < c.PRICE_CHANGE_DATE
    print("Before:", ratio[before].value_counts().to_dict())
    print("After: ", ratio[~before].value_counts().to_dict())
    print("Last old-price order:", lines.loc[ratio < 1, "OrderDate"].max().date(),
          "| first order on/after switch:", lines.loc[~before, "OrderDate"].min().date())


def monthly_series(lines, orders):
    """Summarize sales by month, complete months only.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.
        orders (pandas.DataFrame): Orders from ``common.load_all``.

    Returns:
        pandas.DataFrame: One row per month through April 1998 with
        units, revenue, orders, customers, units per order, share of
        lines discounted, and average discount.
    """
    full_o = orders[orders["Month"] <= c.LAST_FULL_MONTH]
    full_l = lines[lines["Month"] <= c.LAST_FULL_MONTH]
    m = full_l.groupby("Month").agg(units=("Quantity", "sum"),
                                    revenue=("Revenue", "sum"))
    m["orders"] = full_o.groupby("Month")["OrderID"].count()
    m["customers"] = full_o.groupby("Month")["CustomerID"].nunique()
    m["units_per_order"] = m["units"] / m["orders"]
    m["share_lines_discounted"] = full_l.groupby("Month")["Discount"].apply(
        lambda s: (s > 0).mean())
    m["avg_discount"] = full_l.groupby("Month")["Discount"].mean()
    return m


def window_compare(lines, orders):
    """Compare 60-, 90-, and 180-day windows around the price change.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.
        orders (pandas.DataFrame): Order totals; not used.

    Returns:
        pandas.DataFrame: One row per window length and period with
        volume, revenue, and discount measures. Also prints it and
        saves q1_window_compare.csv.
    """
    c.header("Q1.1 Before vs after the price change (equal-length windows)")
    rows = []
    for days in [60, 90, 180]:
        for before in [True, False]:
            w = window(lines, days, before)
            rows.append({
                "window_days": days, "period": "before" if before else "after",
                "orders": w["OrderID"].nunique(),
                "customers": w["CustomerID"].nunique(),
                "units": w["Quantity"].sum(),
                "units_per_order": w["Quantity"].sum() / w["OrderID"].nunique(),
                "revenue": w["Revenue"].sum(),
                "share_lines_discounted": (w["Discount"] > 0).mean(),
                "avg_discount": w["Discount"].mean(),
                "paid_vs_list_after_discount": (w["Revenue"].sum() /
                                                (w["Price"] * w["Quantity"]).sum()),
            })
    t = pd.DataFrame(rows)
    print(t.round(3).to_string(index=False))
    piv = t.pivot(index="window_days", columns="period")
    change = (piv.xs("after", axis=1, level=1) / piv.xs("before", axis=1, level=1) - 1)
    print("\n% change after vs before:")
    print(change[["orders", "customers", "units", "units_per_order",
                  "revenue"]].round(3).to_string())
    c.save_table(t, "q1_window_compare", index=False)
    return t


def trend_projection(m):
    """Fit a line to pre-change monthly units and compare with actuals.

    The fit uses July 1996 to March 1997 and is extended to all months.

    Args:
        m (pandas.DataFrame): Monthly table from ``monthly_series``.

    Returns:
        tuple: ``(m, resid_sd)`` -- a copy of ``m`` with a ``trend``
        column (pandas.DataFrame), and the standard deviation of the
        fit's residuals in units (float).
    """
    c.header("Q1.2 Pre-change trend projected forward (linear fit on Jul 1996-Mar 1997)")
    pre = m.loc[:pd.Period("1997-03", "M")]
    x = np.arange(len(m))
    fit = stats.linregress(x[:len(pre)], pre["units"].values)
    m = m.assign(trend=fit.intercept + fit.slope * x)
    resid_sd = np.std(pre["units"].values - (fit.intercept + fit.slope * x[:len(pre)]), ddof=2)
    print(f"Pre-period slope: {fit.slope:.0f} units/month, R^2={fit.rvalue ** 2:.2f}, "
          f"residual SD={resid_sd:.0f}")
    post = m.loc[pd.Period("1997-04", "M"):pd.Period("1997-11", "M")]
    out = post[["units", "trend"]].assign(gap=post["units"] - post["trend"])
    print(out.round(0).to_string())
    print(f"Apr-Nov 1997 actual / trend: {post['units'].sum() / post['trend'].sum():.2f}")
    return m, resid_sd


def same_customers(lines):
    """Compare units bought by the same customers 180 days before/after.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.

    Returns:
        None. Prints the comparison and a Wilcoxon test, and saves
        q1_same_customers.csv.
    """
    c.header("Q1.3 Same customers, 180 days before vs after")
    b = window(lines, 180, True).groupby("CustomerID")["Quantity"].sum()
    a = window(lines, 180, False).groupby("CustomerID")["Quantity"].sum()
    both = pd.concat([b.rename("before"), a.rename("after")], axis=1)
    print(f"Customers before: {b.size}, after: {a.size}, in both: "
          f"{both.dropna().shape[0]}, only before: {both['after'].isna().sum()}, "
          f"only after: {both['before'].isna().sum()}")
    k = both.dropna()
    print(f"Among customers in both: total units {k['before'].sum():.0f} -> "
          f"{k['after'].sum():.0f} ({k['after'].sum() / k['before'].sum() - 1:+.1%}); "
          f"{(k['after'] > k['before']).mean():.0%} bought more, "
          f"median change {(k['after'] / k['before'] - 1).median():+.1%}")
    w = stats.wilcoxon(k["after"], k["before"])
    print(f"Wilcoxon signed-rank test (after vs before): p={w.pvalue:.3f}")
    c.save_table(both, "q1_same_customers")


def by_segment(lines):
    """Compare 180-day unit changes by price tier and by category.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.

    Returns:
        None. Prints the tables and saves q1_by_segment.csv.
    """
    c.header("Q1.4 Did expensive products or some categories react more? (180-day windows)")
    lines = lines.assign(PriceTier=pd.qcut(lines["Price"], 3,
                                           labels=["low", "mid", "high"]))
    out = []
    for key in ["PriceTier", "CategoryName"]:
        b = window(lines, 180, True).groupby(key, observed=True)["Quantity"].sum()
        a = window(lines, 180, False).groupby(key, observed=True)["Quantity"].sum()
        t = pd.DataFrame({"before": b, "after": a})
        t["change"] = t["after"] / t["before"] - 1
        print(t.round(3).to_string())
        out.append(t.rename_axis("segment").assign(dimension=key))
    tiers = lines.groupby("PriceTier", observed=True)["Price"].agg(["min", "max"])
    print("Price tier ranges (list price):", tiers.to_dict("index"))
    c.save_table(pd.concat(out), "q1_by_segment")


def chart(m, resid_sd):
    """Draw monthly units against the pre-change trend band.

    Args:
        m (pandas.DataFrame): Monthly table with a ``trend`` column,
            from ``trend_projection``.
        resid_sd (float): Residual SD; the band is trend +/- 2 SD.

    Returns:
        None. Saves q1_units_price_change.png.
    """
    fig, ax = c.new_figure()
    x = m.index.to_timestamp()
    pre_mask = m.index <= pd.Period("1997-11", "M")
    ax.fill_between(x[pre_mask], (m["trend"] - 2 * resid_sd)[pre_mask],
                    (m["trend"] + 2 * resid_sd)[pre_mask], color=c.GRAY,
                    alpha=0.15, linewidth=0, label="Pre-change trend ±2 SD")
    ax.plot(x[pre_mask], m["trend"][pre_mask], color=c.GRAY, linewidth=1.2)
    ax.plot(x, m["units"], color=c.BLUE, linewidth=2, marker="o",
            markersize=4, label="Units sold per month")
    ax.axvline(c.PRICE_CHANGE_DATE, color=c.ORANGE, linewidth=1.5)
    ax.text(c.PRICE_CHANGE_DATE + pd.Timedelta(days=6), m["units"].max() * 0.97,
            "All list prices +25%\n(week of Apr 7, 1997)", color=c.INK2,
            fontsize=9, va="top")
    c.style_axes(ax, "Unit sales held steady after the 25% price increase, "
                     "but stopped growing until Dec 1997",
                 "Order month", "Units sold",
                 subtitle="Monthly units, Jul 1996 – Apr 1998 (May 1998 partial, excluded). "
                          "Gray = linear trend of the 9 months before the change.")
    ax.set_ylim(0, m["units"].max() * 1.08)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    c.save_figure(fig, "q1_units_price_change")


def main():
    """Run the full Q1 analysis.

    Args:
        None.

    Returns:
        None. Prints results and writes Q1 tables and the figure.
    """
    tables, lines, orders = c.load_all()
    verify_switch(lines)
    m = monthly_series(lines, orders)
    c.header("Q1 Monthly series")
    print(m.round(3).to_string())
    window_compare(lines, orders)
    m, resid_sd = trend_projection(m)
    same_customers(lines)
    by_segment(lines)
    c.save_table(m, "q1_monthly")
    chart(m, resid_sd)


if __name__ == "__main__":
    main()
