"""Q5: Which countries are growing or shrinking, and why?"""
import numpy as np
import pandas as pd

import common as c

# label, (earlier start, end), (later start, end); end dates exclusive.
COMPARISONS = [
    ("JanApr", ("1997-01-01", "1997-05-01"), ("1998-01-01", "1998-05-01")),
    ("NovApr", ("1996-11-01", "1997-05-01"), ("1997-11-01", "1998-05-01")),
    ("Last6vsPrev6", ("1997-05-01", "1997-11-01"), ("1997-11-01", "1998-05-01")),
]
SMALL_ORDERS = 10


def period(orders, start, end):
    """Select orders placed in a date range.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.
        start (str): First date, inclusive (YYYY-MM-DD).
        end (str): Last date, exclusive (YYYY-MM-DD).

    Returns:
        pandas.DataFrame: Orders in the range.
    """
    return orders[(orders["OrderDate"] >= start) & (orders["OrderDate"] < end)]


def country_changes(orders):
    """Compute each country's constant-price revenue change.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.

    Returns:
        tuple[pandas.DataFrame, pandas.DataFrame]: The Jan-Apr
        1998 vs 1997 table by country (sorted by dollar change, with
        a ``small_sample`` flag), and the dollar change by country
        for all three comparisons with ``periods_growing``. Also
        prints both and saves q5_country_changes.csv.
    """
    c.header("Q5.1 Country revenue change at constant prices")
    frames = []
    for label, (s1, e1), (s2, e2) in COMPARISONS:
        a = period(orders, s1, e1).groupby("Country").agg(
            rev_before=("ConstRevenue", "sum"), orders_before=("OrderID", "count"),
            cust_before=("CustomerID", "nunique"))
        b = period(orders, s2, e2).groupby("Country").agg(
            rev_after=("ConstRevenue", "sum"), orders_after=("OrderID", "count"),
            cust_after=("CustomerID", "nunique"))
        t = a.join(b, how="outer").fillna(0)
        t["change"] = t["rev_after"] - t["rev_before"]
        t["growth"] = np.where(t["rev_before"] > 0, t["rev_after"] / t["rev_before"] - 1, np.nan)
        t["comparison"] = label
        frames.append(t)
    allc = pd.concat(frames)
    main = allc[allc["comparison"] == "JanApr"].sort_values("change", ascending=False)
    main["small_sample"] = (main[["orders_before", "orders_after"]].min(axis=1) < SMALL_ORDERS)
    print(main.drop(columns="comparison").round(2).to_string())

    wide = allc.pivot_table(index="Country", columns="comparison", values="change")
    wide["periods_growing"] = (wide[["JanApr", "NovApr", "Last6vsPrev6"]] > 0).sum(axis=1)
    print("\nAbsolute change in each comparison and how many of 3 show growth:")
    print(wide.sort_values("JanApr").round(0).to_string())
    c.save_table(allc, "q5_country_changes")
    total = main["change"].sum()
    top4 = main.head(4)
    print(f"\nTotal change ${total:,.0f}; top 4 countries ({', '.join(top4.index)}) "
          f"= {top4['change'].sum() / total:.0%}")
    return main, wide


def decliners(orders, wide):
    """List customer-level changes in countries that declined.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.
        wide (pandas.DataFrame): Second table from
            ``country_changes``; countries with a negative Jan-Apr
            change are examined.

    Returns:
        None. Prints results and saves q5_decliner_customers.csv.
    """
    c.header("Q5.2 Inside the declining countries: which customers?")
    (_, (s1, e1), (s2, e2)) = COMPARISONS[0]
    neg = wide[wide["JanApr"] < 0].index
    a = period(orders, s1, e1).groupby(["Country", "CompanyName"])["ConstRevenue"].sum()
    b = period(orders, s2, e2).groupby(["Country", "CompanyName"])["ConstRevenue"].sum()
    t = pd.concat([a.rename("before"), b.rename("after")], axis=1).fillna(0)
    t["change"] = t["after"] - t["before"]
    t = t.loc[t.index.get_level_values(0).isin(neg)].sort_values("change")
    print(t.round(0).to_string())
    last = orders.groupby("CompanyName")["OrderDate"].max()
    print("\nLast order date of customers that fell to zero:")
    zero = t[t["after"] == 0].index.get_level_values(1)
    print(last[zero].dt.date.to_string())
    c.save_table(t, "q5_decliner_customers")


def customers_per_country(orders):
    """Count customers per country and the top customer's share.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.

    Returns:
        None. Prints results and saves q5_customers_per_country.csv.
    """
    c.header("Q5.3 How many customers stand behind each country? (all data)")
    t = orders.groupby("Country").agg(customers=("CustomerID", "nunique"),
                                      orders=("OrderID", "count"),
                                      revenue=("Revenue", "sum"))
    t["top_customer_share"] = orders.groupby(["Country", "CustomerID"])["Revenue"].sum() \
        .groupby("Country").max() / t["revenue"]
    print(t.sort_values("revenue", ascending=False).round(2).to_string())
    c.save_table(t, "q5_customers_per_country")


def chart(main):
    """Draw each country's dollar change as horizontal bars.

    Args:
        main (pandas.DataFrame): First table from ``country_changes``.

    Returns:
        None. Saves q5_country_change.png.
    """
    d =main.sort_values("change")
    fig, ax = c.new_figure(8, 6.2)
    colors = [c.BLUE if v >= 0 else c.RED for v in d["change"]]
    ax.barh(d.index, d["change"] / 1000, color=colors, height=0.7)
    for i, (country, row) in enumerate(d.iterrows()):
        g = "new" if np.isnan(row["growth"]) else f"{row['growth']:+.0%}"
        note = f"{g}  ({int(row['orders_before'])}→{int(row['orders_after'])} orders)"
        x = row["change"] / 1000
        ax.text(x + (0.8 if x >= 0 else -0.8), i, note, va="center",
                ha="left" if x >= 0 else "right", fontsize=8, color=c.INK2)
    ax.axvline(0, color=c.AXIS, linewidth=0.8)
    ax.grid(axis="x", color=c.GRID, linewidth=0.6)
    lo, hi = d["change"].min() / 1000, d["change"].max() / 1000
    ax.set_xlim(lo - 22, hi + 25)
    c.style_axes(ax, "USA, Germany and Brazil add the most; each decline traces "
                     "to one or two customers",
                 "Change in revenue, Jan–Apr 1998 vs Jan–Apr 1997 ($ thousands, constant prices)",
                 "", subtitle="Bar = dollar change. Label = % change and number of orders "
                              "(1997 → 1998). Countries with < 10 orders in a period are "
                              "small samples.")
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", labelsize=8.5)
    c.save_figure(fig, "q5_country_change")


def main():
    """Run the full Q5 analysis.

    Args:
        None.

    Returns:
        None. Prints results and writes Q5 tables and the figure.
    """
    tables, lines, orders = c.load_all()
    main_t, wide = country_changes(orders)
    decliners(orders, wide)
    customers_per_country(orders)
    chart(main_t)


if __name__ == "__main__":
    main()
