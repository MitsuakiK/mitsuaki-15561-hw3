"""Step 2, part 1: sizes, trends, concentration, and group totals."""
import pandas as pd

import prep

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 30)


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


def basics(o, d, ot):
    """Print overall totals and distributions of orders and lines.

    Args:
        o (pandas.DataFrame): Orders; not used.
        d (pandas.DataFrame): Order lines from ``prep.build_lines``.
        ot (pandas.DataFrame): Orders from ``prep.order_table``.

    Returns:
        None. Prints to standard output.
    """
    section("1. Basic size and distributions")
    full = ot[ot["Month"] <= prep.LAST_FULL_MONTH]
    print(f"Revenue total: {d['Revenue'].sum():,.0f}  orders: {len(ot)}  "
          f"active customers: {ot['CustomerID'].nunique()}  "
          f"products sold: {d['ProductID'].nunique()}")
    print("\nOrder value (revenue per order) distribution:")
    print(ot["Revenue"].describe(percentiles=[.1, .25, .5, .75, .9, .99])
          .round(0).to_string())
    top10 = ot.nlargest(int(len(ot) * 0.1), "Revenue")["Revenue"].sum()
    print(f"Top 10% of orders = {top10 / ot['Revenue'].sum():.0%} of revenue")
    print("\nLines per order:", ot["Lines"].value_counts().sort_index().to_dict())
    print("Quantity per line:")
    print(d["Quantity"].describe(percentiles=[.5, .9, .99]).round(1).to_string())
    print("\nShare of lines with any discount:",
          f"{(d['Discount'] > 0).mean():.0%}",
          "| revenue given away by discounts:",
          f"{(d['Gross'] - d['Revenue']).sum():,.0f}",
          f"({(d['Gross'] - d['Revenue']).sum() / d['Gross'].sum():.1%} of gross)")
    print("\nFreight per order:")
    print(ot["Freight"].describe(percentiles=[.5, .9, .99]).round(1).to_string())
    print("Freight as % of order revenue (median):",
          f"{(ot['Freight'] / ot['Revenue']).median():.1%}")


def monthly(o, d, ot):
    """Print the monthly trend and a Jan-Apr year-over-year view.

    Args:
        o (pandas.DataFrame): Orders; not used.
        d (pandas.DataFrame): Order lines; not used.
        ot (pandas.DataFrame): Orders from ``prep.order_table``.

    Returns:
        None. Prints to standard output.
    """
    section("2. Monthly trend (May 1998 excluded)")
    full = ot[ot["Month"] <= prep.LAST_FULL_MONTH]
    m = full.groupby("Month").agg(
        orders=("OrderID", "count"), revenue=("Revenue", "sum"),
        customers=("CustomerID", "nunique"), avg_order=("Revenue", "mean"))
    print(m.round(0).to_string())
    a = full[full["Month"].dt.month <= 4]
    yoy = a.groupby(a["Month"].dt.year).agg(
        orders=("OrderID", "count"), revenue=("Revenue", "sum"),
        customers=("CustomerID", "nunique"))
    print("\nJan-Apr comparison:")
    print(yoy.round(0).to_string())


def concentration(o, d, ot):
    """Print how much revenue the top customers and products hold.

    Args:
        o (pandas.DataFrame): Orders; not used.
        d (pandas.DataFrame): Order lines from ``prep.build_lines``.
        ot (pandas.DataFrame): Orders with totals; not used.

    Returns:
        None. Prints to standard output.
    """
    section("3. Concentration (Pareto) of customers and products")
    for key, name in [("CustomerID", "customers"), ("ProductName", "products")]:
        s = d.groupby(key)["Revenue"].sum().sort_values(ascending=False)
        cum = s.cumsum() / s.sum()
        n80 = (cum < 0.8).sum() + 1
        print(f"{name}: {len(s)} total; top 5 = {s.head(5).sum() / s.sum():.0%}"
              f" of revenue; {n80} {name} make 80%")
        print("  top 5:", (s.head(5) / s.sum()).round(3).to_dict())


def groups(o, d, ot):
    """Print revenue and Jan-Apr growth by several groupings.

    Groups by customer country, category, employee, shipper, and
    supplier country.

    Args:
        o (pandas.DataFrame): Orders; not used.
        d (pandas.DataFrame): Order lines from ``prep.build_lines``.
        ot (pandas.DataFrame): Orders with totals; not used.

    Returns:
        None. Prints to standard output.
    """
    section("4. Group comparisons")
    full = d[d["Month"] <= prep.LAST_FULL_MONTH]
    a = full[full["Month"].dt.month <= 4]
    a = a.assign(Year=a["Month"].dt.year)

    def table(key):
        """Summarize revenue and Jan-Apr growth for one grouping.

        Args:
            key (str): Column of ``d`` to group by.

        Returns:
            pandas.DataFrame: Total revenue, share, Jan-Apr 1997 and
            1998 revenue, and growth, largest total first.
        """
        tot = d.groupby(key)["Revenue"].sum()
        yoy = a.pivot_table(index=key, columns="Year", values="Revenue",
                            aggfunc="sum", fill_value=0)
        res = pd.DataFrame({"revenue_all": tot, "share": tot / tot.sum()})
        res["JanApr97"] = yoy.get(1997)
        res["JanApr98"] = yoy.get(1998)
        res["growth"] = res["JanApr98"] / res["JanApr97"] - 1
        return res.sort_values("revenue_all", ascending=False)

    for key in ["Country", "CategoryName", "LastName", "Shipper", "SupCountry"]:
        print(f"\n--- by {key} ---")
        print(table(key).round(2).to_string())


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
    basics(o, d, ot)
    monthly(o, d, ot)
    concentration(o, d, ot)
    groups(o, d, ot)


if __name__ == "__main__":
    main()
