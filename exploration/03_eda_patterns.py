"""Step 2, part 2: outliers, price change, customers, discounts,
shipping, inventory, and cross-tabulations.
"""
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


def outlier_orders(ot, d):
    """Print the largest orders and other unusual orders.

    Args:
        ot (pandas.DataFrame): Orders from ``prep.order_table``.
        d (pandas.DataFrame): Order lines; not used.

    Returns:
        None. Prints to standard output.
    """
    section("5. Unusual orders")
    big = ot.nlargest(1, "Lines")
    print("Order with most lines:", big[["OrderID", "CompanyName", "OrderDate",
                                        "Lines", "Revenue"]].to_string(index=False))
    print("\nTop 5 orders by revenue:")
    print(ot.nlargest(5, "Revenue")[["OrderID", "CompanyName", "Country",
                                     "OrderDate", "Lines", "Revenue"]]
          .round({"Revenue": 0}).to_string(index=False))
    print("\nOrders by weekday:", ot["OrderDate"].dt.day_name()
          .value_counts().to_dict())
    r = ot["Freight"] / ot["Revenue"]
    print("Orders where freight > 50% of order value:", (r > 0.5).sum())


def price_change(d):
    """Find when each product moved from the old to the list price.

    Args:
        d (pandas.DataFrame): Order lines from ``prep.build_lines``.

    Returns:
        None. Prints to standard output.
    """
    section("6. When did list prices change? (order price vs current list price)")
    d = d.assign(AtList=d["UnitPrice"] == d["Price"])
    per = d.groupby("ProductName").apply(lambda g: pd.Series({
        "last_old": g.loc[~g["AtList"], "OrderDate"].max(),
        "first_new": g.loc[g["AtList"], "OrderDate"].min()}),
        include_groups=False)
    print("Last old-price sale (distribution across products):")
    print(per["last_old"].describe().to_string())
    print("First list-price sale:")
    print(per["first_new"].describe().to_string())
    print("Products with overlap (old price used after first new price):",
          (per["last_old"] > per["first_new"]).sum())
    cut = pd.Timestamp("1997-01-01")
    sw = d[(d["OrderDate"] >= "1996-12-01") & (d["OrderDate"] < "1997-02-01")]
    print("\nShare at list price by week around the switch:")
    print(sw.groupby(sw["OrderDate"].dt.to_period("W"))["AtList"].mean()
          .round(2).to_string())


def customers(ot):
    """Print new vs. existing customers and lapsed customers.

    Args:
        ot (pandas.DataFrame): Orders from ``prep.order_table``.

    Returns:
        None. Prints to standard output.
    """
    section("7. Customer dynamics: new vs. existing, lapsed customers")
    first = ot.groupby("CustomerID")["Month"].min().rename("FirstMonth")
    x = ot.merge(first, on="CustomerID")
    x["Type"] = (x["Month"] == x["FirstMonth"]).map({True: "new", False: "existing"})
    full = x[x["Month"] <= prep.LAST_FULL_MONTH]
    q = full.groupby([full["OrderDate"].dt.to_period("Q"), "Type"]).agg(
        customers=("CustomerID", "nunique"), orders=("OrderID", "count"),
        revenue=("Revenue", "sum")).unstack()
    print(q.round(0).to_string())
    print("\nNew customers acquired per quarter:")
    print(first.dt.asfreq("Q", how="start").value_counts().sort_index()
          .to_string())

    end = ot["OrderDate"].max()
    last = ot.groupby(["CustomerID", "CompanyName", "Country"]).agg(
        last_order=("OrderDate", "max"), orders=("OrderID", "count"),
        revenue=("Revenue", "sum")).reset_index()
    last["days_since"] = (end - last["last_order"]).dt.days
    gap = ot.sort_values("OrderDate").groupby("CustomerID")["OrderDate"].diff()
    print("\nMedian days between a customer's orders:", gap.dt.days.median())
    lapsed = last[last["days_since"] > 180].sort_values("revenue",
                                                       ascending=False)
    print(f"Customers with no order in last 180 days: {len(lapsed)}, "
          f"lifetime revenue {lapsed['revenue'].sum():,.0f}")
    print(lapsed.head(10).round({"revenue": 0}).to_string(index=False))
    print("\nOrders per customer:", last["orders"].describe().round(1).to_dict())


def discounts(d, ot):
    """Print who gets discounts and how line size relates to them.

    Args:
        d (pandas.DataFrame): Order lines from ``prep.build_lines``.
        ot (pandas.DataFrame): Orders with totals; not used.

    Returns:
        None. Prints to standard output.
    """
    section("8. Discounts: who gets them, and do they go with bigger lines?")
    d = d.assign(HasDisc=d["Discount"] > 0)
    print("Avg quantity per line, discounted vs not:")
    print(d.groupby("HasDisc")["Quantity"].agg(["mean", "median", "count"])
          .round(1).to_string())
    print("\nAvg quantity by discount rate:")
    print(d.groupby("Discount")["Quantity"].agg(["mean", "count"]).round(1)
          .to_string())
    print("\nDiscount use by employee (share of lines discounted, avg rate when discounted, $ given away):")
    e = d.groupby("LastName").apply(lambda g: pd.Series({
        "lines": len(g), "share_disc": g["HasDisc"].mean(),
        "avg_rate": g.loc[g["HasDisc"], "Discount"].mean(),
        "given_away": (g["Gross"] - g["Revenue"]).sum()}), include_groups=False)
    print(e.sort_values("share_disc").round(2).to_string())
    print("\nCustomers: share of lines discounted (customers with >= 20 lines):")
    c = d.groupby("CompanyName").agg(lines=("OrderID", "count"),
                                     share=("HasDisc", "mean"),
                                     revenue=("Revenue", "sum"))
    c = c[c["lines"] >= 20]
    print("customers never discounted:", (c["share"] == 0).sum(), "of", len(c),
          "| always/mostly (>80%):", (c["share"] > 0.8).sum())
    print("Corr(customer discount share, customer revenue):",
          round(c["share"].corr(c["revenue"]), 2))


def shipping(ot):
    """Print shipping time, late rates, and freight by group.

    Args:
        ot (pandas.DataFrame): Orders from ``prep.order_table``.

    Returns:
        None. Prints to standard output.
    """
    section("9. Shipping: speed, lateness, freight")
    s = ot[ot["ShippedDate"].notna()]
    print("Ship days distribution:", s["ShipDays"].describe().round(1).to_dict())
    for key in ["Shipper", "LastName", "Country"]:
        g = s.groupby(key).agg(orders=("OrderID", "count"),
                               late_rate=("Late", "mean"),
                               median_days=("ShipDays", "median"),
                               avg_freight=("Freight", "mean"))
        print(f"\n--- by {key} ---")
        print(g.sort_values("late_rate", ascending=False).round(2).head(12)
              .to_string())
    print("\nLate rate by required-date window (days):")
    lead = (s["RequiredDate"] - s["OrderDate"]).dt.days
    print(s.groupby(lead)["Late"].agg(["mean", "count"]).round(2).to_string())
    print("\nLate rate by half-year:")
    print(s.groupby(s["OrderDate"].dt.to_period("Q"))["Late"].agg(
        ["mean", "count"]).round(2).to_string())
    print("\nCorr(freight, order revenue):",
          round(ot["Freight"].corr(ot["Revenue"]), 2),
          "| Corr(freight, units):", round(ot["Freight"].corr(ot["Units"]), 2))
    late = s[s["Late"] == True]
    print("Days late beyond required date:",
          (late["ShippedDate"] - late["RequiredDate"]).dt.days.describe()
          .round(1).to_dict())


def inventory(t, d):
    """Compare stock levels with 1998 demand for each product.

    Args:
        t (dict[str, pandas.DataFrame]): Output of ``prep.load_tables``.
        d (pandas.DataFrame): Order lines from ``prep.build_lines``.

    Returns:
        None. Prints to standard output.
    """
    section("10. Inventory vs. demand")
    p = t["Product"].copy()
    recent = d[(d["OrderDate"] >= "1998-01-01") &
               (d["Month"] <= prep.LAST_FULL_MONTH)]
    monthly_units = recent.groupby("ProductID")["Quantity"].sum() / 4
    p["units_per_month_1998"] = p["ProductID"].map(monthly_units).fillna(0)
    p["months_of_stock"] = p["UnitsInStock"] / p["units_per_month_1998"]
    p["below_reorder"] = (p["UnitsInStock"] + p["UnitsOnOrder"]) < p["ReorderLevel"]
    print("Products with 0 in stock:", (p["UnitsInStock"] == 0).sum(),
          p.loc[p["UnitsInStock"] == 0, "ProductName"].tolist())
    print("Stock + on order below reorder level:", p["below_reorder"].sum())
    print("Active products with < 1 month of stock:",
          ((p["months_of_stock"] < 1) & ~p["Discontinued"]).sum())
    print(p[~p["Discontinued"]].sort_values("months_of_stock")[[
        "ProductName", "UnitsInStock", "UnitsOnOrder", "ReorderLevel",
        "units_per_month_1998", "months_of_stock"]].head(10).round(2)
        .to_string(index=False))
    mos = p.loc[~p["Discontinued"], "months_of_stock"]
    print("\nMonths of stock, median (active products):", round(mos.median(), 2),
          "| products with no 1998 sales:", int((mos == float("inf")).sum()))
    disc_rev = d[d["Discontinued"]]
    print("Discontinued products' share of revenue:",
          f"{disc_rev['Revenue'].sum() / d['Revenue'].sum():.1%}",
          "| share in Jan-Apr 1998:",
          f"{recent.loc[recent['Discontinued'], 'Revenue'].sum() / recent['Revenue'].sum():.1%}")


def cross_tabs(d):
    """Print country x category mix and employee coverage.

    Args:
        d (pandas.DataFrame): Order lines from ``prep.build_lines``.

    Returns:
        None. Prints to standard output.
    """
    section("11. Combinations: country x category, employee x customer country")
    top = d.groupby("Country")["Revenue"].sum().nlargest(8).index
    x = d[d["Country"].isin(top)]
    ct = pd.crosstab(x["Country"], x["CategoryName"], values=x["Revenue"],
                     aggfunc="sum", normalize="index")
    print("Category mix (share of each country's revenue):")
    print(ct.round(2).to_string())
    print("\nEmployee office country x customer country (orders):")
    print("Employees in UK office serve customers in:",
          d[d["EmpCountry"] == "UK"]["Country"].nunique(), "countries;",
          "USA office:", d[d["EmpCountry"] == "USA"]["Country"].nunique())
    print("Customers served by how many different employees:")
    print(d.groupby("CustomerID")["EmployeeID"].nunique().describe().round(1)
          .to_dict())


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
    outlier_orders(ot, d)
    price_change(d)
    customers(ot)
    discounts(d, ot)
    shipping(ot)
    inventory(t, d)
    cross_tabs(d)


if __name__ == "__main__":
    main()
