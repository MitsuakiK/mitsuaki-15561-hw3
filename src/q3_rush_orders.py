"""Q3: Are short-deadline (14-day) orders shipped late more often?"""
import numpy as np
import pandas as pd
from scipy import stats

import common as c

SEED = 561
N_PERMUTATIONS = 10000


def shipped(orders):
    """Keep only orders that have a ship date.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.

    Returns:
        pandas.DataFrame: Copy of the shipped orders.
    """
    return orders[orders["ShippedDate"].notna()].copy()


def summary(s):
    """Compare late rate and shipping time across deadline windows.

    Args:
        s (pandas.DataFrame): Shipped orders from ``shipped``.

    Returns:
        tuple[pandas.DataFrame, pandas.DataFrame]: Orders with a
        14-day window and orders with a 28-day window. Also prints
        tests and saves q3_by_window.csv.
    """
    c.header("Q3.1 Late rate and shipping time by deadline window")
    t = s.groupby("Window").agg(
        orders=("OrderID", "count"), late=("Late", "sum"),
        late_rate=("Late", "mean"), median_ship_days=("ShipDays", "median"),
        mean_ship_days=("ShipDays", "mean"),
        customers=("CustomerID", "nunique"),
        avg_order_revenue=("Revenue", "mean"))
    print(t.round(3).to_string())
    c.save_table(t, "q3_by_window")

    short, normal = s[s["Window"] == 14], s[s["Window"] == 28]
    table = [[short["Late"].sum(), (~short["Late"]).sum()],
             [normal["Late"].sum(), (~normal["Late"]).sum()]]
    odds, p = stats.fisher_exact(table)
    print(f"\nFisher exact test, late rate 14-day vs 28-day: odds ratio {odds:.1f}, p={p:.5f}")
    mw = stats.mannwhitneyu(short["ShipDays"], normal["ShipDays"])
    print(f"Mann-Whitney test, ship days 14-day vs 28-day: p={mw.pvalue:.3f} "
          "(large p = no evidence that short-deadline orders ship faster)")
    benchmark = (s["ShipDays"] > 14).mean()
    print(f"Share of ALL shipped orders that take more than 14 days: {benchmark:.1%} "
          f"-> expected late rate for 14-day orders if they get no priority; "
          f"observed {short['Late'].mean():.1%}")
    return short, normal


def stratified(s):
    """Check the 14- vs 28-day late-rate gap within subgroups.

    Prints late rates by shipper, year, and employee, then runs a
    permutation test that shuffles deadline labels within each
    shipper x year group.

    Args:
        s (pandas.DataFrame): Shipped orders from ``shipped``.

    Returns:
        None. Prints to standard output.
    """
    c.header("Q3.2 Same comparison within shipper, year, and employee")
    s = s[s["Window"].isin([14, 28])].assign(Year=s["OrderDate"].dt.year)
    for key in ["Shipper", "Year", "LastName"]:
        t = s.pivot_table(index=key, columns="Window", values="Late",
                          aggfunc=["mean", "count"])
        print(f"\n--- {key} ---")
        print(t.round(2).to_string())

    rng = np.random.default_rng(SEED)
    strata = s["Shipper"] + "_" + s["Year"].astype(str)
    late = s["Late"].astype(float).values
    is_short = (s["Window"] == 14).values
    observed = late[is_short].mean() - late[~is_short].mean()
    groups = [np.where(strata.values == g)[0] for g in strata.unique()]
    diffs = np.empty(N_PERMUTATIONS)
    for i in range(N_PERMUTATIONS):
        perm = is_short.copy()
        for idx in groups:
            perm[idx] = rng.permutation(perm[idx])
        diffs[i] = late[perm].mean() - late[~perm].mean()
    p = (np.sum(diffs >= observed) + 1) / (N_PERMUTATIONS + 1)
    print(f"\nPermutation test within shipper x year strata: observed gap "
          f"{observed:+.1%}, one-sided p={p:.4f} ({N_PERMUTATIONS} shuffles)")


def stakes(short, s):
    """Size the late 14-day orders in orders, revenue, and days late.

    Args:
        short (pandas.DataFrame): Shipped 14-day-window orders.
        s (pandas.DataFrame): All shipped orders.

    Returns:
        None. Prints to standard output.
    """
    c.header("Q3.3 What is at stake")
    late_short = short[short["Late"] == True]
    print(f"14-day orders: {len(short)} orders from {short['CustomerID'].nunique()} "
          f"customers, revenue ${short['Revenue'].sum():,.0f}; "
          f"{len(late_short)} late, revenue ${late_short['Revenue'].sum():,.0f}")
    print("Days late (14-day orders):",
          (late_short["ShippedDate"] - late_short["RequiredDate"]).dt.days
          .describe().round(1).to_dict())
    print("Ship days of late 14-day orders:", sorted(late_short["ShipDays"].tolist()))
    for target in [10, 14]:
        print(f"If 14-day orders shipped within {target} days of order: "
              f"{(short['ShipDays'] > target).sum()} orders would need faster handling")
    print("Late share of all late orders that are 14-day orders:",
          f"{len(late_short) / s['Late'].sum():.0%}",
          f"(14-day orders are {len(short) / len(s):.0%} of shipped orders)")
    excl = short[short["OrderID"] != short.nlargest(1, "ShipDays")["OrderID"].iloc[0]]
    print(f"Robustness: drop the slowest 14-day order -> late rate {excl['Late'].mean():.1%}")


def chart(short, normal):
    """Draw the cumulative share shipped by day for both windows.

    Args:
        short (pandas.DataFrame): Shipped 14-day-window orders.
        normal (pandas.DataFrame): Shipped 28-day-window orders.

    Returns:
        None. Saves q3_ship_days_by_deadline.png.
    """
    fig, ax = c.new_figure()
    days = np.arange(0, 38)
    for grp, label, color in [(short, f"14-day deadline (n={len(short)})", c.ORANGE),
                              (normal, f"28-day deadline (n={len(normal)})", c.BLUE)]:
        share = [(grp["ShipDays"] <= d).mean() * 100 for d in days]
        ax.step(days, share, where="post", color=color, linewidth=2, label=label)
    ax.axvline(14, color=c.GRAY, linewidth=1)
    ax.text(14.4, 8, "14-day deadline", color=c.INK2, fontsize=9)
    s14 = (short["ShipDays"] <= 14).mean() * 100
    ax.annotate(f"Only {s14:.0f}% of 14-day orders\nshipped by day 14",
                xy=(14, s14), xytext=(19, 55), fontsize=9, color=c.INK2,
                arrowprops=dict(arrowstyle="-", color=c.GRAY, linewidth=0.8))
    c.style_axes(ax, "14-day-deadline orders ship no faster than normal ones, "
                     "so 18% ship after the deadline",
                 "Days from order to shipment", "Share of orders shipped (%)",
                 subtitle="Cumulative share of orders shipped by each day after the "
                          "order date (shipped orders only).")
    ax.set_xlim(0, 37)
    ax.set_ylim(0, 102)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    c.save_figure(fig, "q3_ship_days_by_deadline")


def main():
    """Run the full Q3 analysis.

    Args:
        None.

    Returns:
        None. Prints results and writes the Q3 table and figure.
    """
    tables, lines, orders = c.load_all()
    s = shipped(orders)
    short, normal = summary(s)
    stratified(s)
    stakes(short, s)
    chart(short, normal)


if __name__ == "__main__":
    main()
