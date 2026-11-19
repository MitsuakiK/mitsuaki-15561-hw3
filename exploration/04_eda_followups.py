"""Step 2, part 3: follow-up checks on the most promising patterns."""
import pandas as pd

import prep

pd.set_option("display.width", 160)


def section(title):
    """Print a section title between two rule lines.

    Args:
        title (str): Section title.

    Returns:
        None. Prints to standard output.
    """
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def price_switch_week(d):
    """Pin down the week of the list-price switch.

    Args:
        d (pandas.DataFrame): Order lines from ``prep.build_lines``.

    Returns:
        None. Prints weekly shares and monthly units.
    """
    section("12. Exact timing of the list-price switch (weekly share at list price)")
    d = d.assign(AtList=d["UnitPrice"] == d["Price"])
    w = d[(d["OrderDate"] >= "1997-02-01") & (d["OrderDate"] < "1997-06-01")]
    print(w.groupby(w["OrderDate"].dt.to_period("W"))["AtList"]
          .agg(["mean", "count"]).round(2).to_string())
    ratio = (d["UnitPrice"] / d["Price"]).round(2)
    print("Old/new price ratio before switch:",
          ratio[d["OrderDate"] < "1997-04-07"].value_counts().head(3).to_dict())
    print("\nUnits sold per month:")
    print(d.groupby("Month")["Quantity"].sum().to_string())


def growth_decomposition(ot, d):
    """Compare Jan-Apr 1998 with Jan-Apr 1997 by growth driver.

    Args:
        ot (pandas.DataFrame): Orders from ``prep.order_table``.
        d (pandas.DataFrame): Order lines from ``prep.build_lines``.

    Returns:
        None. Prints to standard output.
    """
    section("13. Jan-Apr 1998 vs Jan-Apr 1997: where did growth come from?")
    a = ot[(ot["Month"] <= prep.LAST_FULL_MONTH) & (ot["Month"].dt.month <= 4)]
    for y, g in a.groupby(a["Month"].dt.year):
        n = g["CustomerID"].nunique()
        print(f"{y}: customers={n}  orders/customer={len(g) / n:.2f}  "
              f"avg order=${g['Revenue'].mean():,.0f}  "
              f"units/order={g['Units'].mean():.1f}")
    dd = d[(d["Month"] <= prep.LAST_FULL_MONTH) & (d["Month"].dt.month <= 4)]
    dd = dd.assign(ConstRev=dd["Price"] * dd["Quantity"] * (1 - dd["Discount"]))
    print("\nRevenue at actual prices vs. at constant (current list) prices:")
    print(dd.groupby(dd["Month"].dt.year)[["Revenue", "ConstRev", "Quantity"]]
          .sum().round(0).to_string())


def rush_orders(ot):
    """Compare 14-day-deadline orders with other deadline windows.

    Args:
        ot (pandas.DataFrame): Orders from ``prep.order_table``.

    Returns:
        None. Prints to standard output.
    """
    section("14. Short-deadline (14-day) orders vs. normal (28-day) orders")
    s = ot[ot["ShippedDate"].notna()]
    s = s.assign(Window=(s["RequiredDate"] - s["OrderDate"]).dt.days)
    print(s.groupby("Window").agg(orders=("OrderID", "count"),
                                  late_rate=("Late", "mean"),
                                  median_ship_days=("ShipDays", "median"),
                                  customers=("CustomerID", "nunique"),
                                  avg_revenue=("Revenue", "mean"))
          .round(2).to_string())
    r = s[s["Window"] == 14]
    print("\n14-day orders, late rate by shipper:")
    print(r.groupby("Shipper")["Late"].agg(["mean", "count"]).round(2)
          .to_string())


def employee_trend(ot):
    """Print revenue by employee and quarter.

    Args:
        ot (pandas.DataFrame): Orders from ``prep.order_table``.

    Returns:
        None. Prints to standard output.
    """
    section("15. Revenue by employee by quarter")
    full = ot[ot["Month"] <= prep.LAST_FULL_MONTH]
    print(full.pivot_table(index="LastName",
                           columns=full["OrderDate"].dt.to_period("Q"),
                           values="Revenue", aggfunc="sum").round(0)
          .to_string())


def main():
    """Run every check in this script in order.

    Args:
        None.

    Returns:
        None. Prints results to standard output.
    """
    t = prep.load_tables()
    o, d = prep.build_lines(t)
    ot = prep.order_table(o, d)
    price_switch_week(d)
    growth_decomposition(ot, d)
    rush_orders(ot)
    employee_trend(ot)


if __name__ == "__main__":
    main()
