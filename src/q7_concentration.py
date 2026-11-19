"""Q7: How dependent is revenue on a few customers and products?"""
import numpy as np
import pandas as pd

import common as c

PERIODS = [("H2 1996", "1996-07-01", "1997-01-01"), ("H1 1997", "1997-01-01", "1997-07-01"),
           ("H2 1997", "1997-07-01", "1998-01-01"), ("Jan-Apr 1998", "1998-01-01", "1998-05-01")]


def shares(lines, key, value="Revenue"):
    """Compute each group's share of total revenue, largest first.

    Args:
        lines (pandas.DataFrame): Order lines.
        key (str): Column to group by, e.g. "CustomerID".
        value (str): Revenue column, "Revenue" or "ConstRevenue".

    Returns:
        pandas.Series: Shares (0-1) indexed by group, summing to 1.
    """
    s =lines.groupby(key)[value].sum().sort_values(ascending=False)
    return s / s.sum()


def hhi(share):
    """Compute the Herfindahl-Hirschman index.

    Args:
        share (pandas.Series): Shares as fractions (0-1).

    Returns:
        float: HHI on the 0-10,000 scale.
    """
    return float((share ** 2).sum() * 10000)


def overall(lines):
    """Measure concentration by customer, product, supplier, country.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.

    Returns:
        None. Prints results and saves q7_concentration_overall.csv.
    """
    c.header("Q7.1 Concentration over the whole period")
    rows = []
    for key, name in [("CustomerID", "customers"), ("ProductName", "products"),
                      ("Supplier", "suppliers"), ("Country", "countries")]:
        for value in ["Revenue", "ConstRevenue"]:
            sh = shares(lines, key, value)
            cum = sh.cumsum()
            rows.append({"dimension": name, "basis": value, "n": len(sh),
                         "top1": sh.iloc[0], "top1_name": sh.index[0],
                         "top3": sh.head(3).sum(), "top10": sh.head(10).sum(),
                         "n_for_80pct": int((cum < 0.8).sum() + 1),
                         "hhi": hhi(sh), "equal_share_hhi": 10000 / len(sh)})
    t = pd.DataFrame(rows)
    print(t.round(3).to_string(index=False))
    print("HHI guide: below 1,500 = unconcentrated (US merger guideline scale).")
    c.save_table(t, "q7_concentration_overall", index=False)


def over_time(lines):
    """Track customer and product concentration by half-year.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.

    Returns:
        None. Prints results and saves q7_concentration_over_time.csv.
    """
    c.header("Q7.2 Is concentration rising or falling? (by half-year)")
    rows = []
    for label, s, e in PERIODS:
        p = lines[(lines["OrderDate"] >= s) & (lines["OrderDate"] < e)]
        cs, ps = shares(p, "CustomerID"), shares(p, "ProductName")
        rows.append({"period": label, "active_customers": len(cs),
                     "top3_customers": cs.head(3).sum(), "top3_names": ", ".join(cs.index[:3]),
                     "customer_hhi": hhi(cs), "top_product": ps.index[0],
                     "top_product_share": ps.iloc[0],
                     "cote_de_blaye_share": ps.get("Côte de Blaye", 0.0)})
    t = pd.DataFrame(rows)
    print(t.round(3).to_string(index=False))
    c.save_table(t, "q7_concentration_over_time", index=False)


def top_product(lines):
    """Describe who buys the top product, Côte de Blaye, and when.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.

    Returns:
        None. Prints to standard output.
    """
    c.header("Q7.3 The top product: who buys Côte de Blaye?")
    p = lines[lines["ProductName"] == "Côte de Blaye"]
    print(f"Supplier: {p['Supplier'].iloc[0]}; list price ${p['Price'].iloc[0]}; "
          f"{len(p)} order lines, {p['CustomerID'].nunique()} customers, "
          f"revenue ${p['Revenue'].sum():,.0f}")
    by_c = p.groupby("CompanyName")["Revenue"].sum().sort_values(ascending=False)
    print((by_c / by_c.sum()).round(3).head(6).to_string())
    print("Order lines by half-year:",
          {lab: int(((p["OrderDate"] >= s) & (p["OrderDate"] < e)).sum())
           for lab, s, e in PERIODS})
    sup = shares(lines, "Supplier")
    print(f"Its supplier's share of all revenue: {sup[p['Supplier'].iloc[0]]:.1%}; "
          f"products from this supplier: "
          f"{lines.loc[lines['Supplier'] == p['Supplier'].iloc[0], 'ProductName'].unique().tolist()}")


def stress_test(lines):
    """Estimate revenue lost if the biggest accounts disappeared.

    Uses the last 12 months of data at actual prices.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.

    Returns:
        None. Prints to standard output.
    """
    c.header("Q7.4 Stress test: losing the biggest accounts (last 12 months, actual prices)")
    last12 = lines[lines["OrderDate"] > c.DATA_END - pd.Timedelta(days=365)]
    total = last12["Revenue"].sum()
    by_c = last12.groupby("CompanyName")["Revenue"].sum().sort_values(ascending=False)
    for k in [1, 3, 5, 10]:
        print(f"Lose top {k:2d} customers: -${by_c.head(k).sum():>9,.0f} "
              f"({by_c.head(k).sum() / total:.1%} of last-12-month revenue)")
    print("Top 5 customers (last 12 months):",
          (by_c.head(5) / total).round(3).to_dict())
    by_p = last12.groupby("ProductName")["Revenue"].sum().sort_values(ascending=False)
    print(f"Lose Côte de Blaye: -${by_p['Côte de Blaye']:,.0f} "
          f"({by_p['Côte de Blaye'] / total:.1%})")
    ctry = lines.groupby(["Country", "CompanyName"])["Revenue"].sum()
    top_in_country = (ctry.groupby("Country").max() / ctry.groupby("Country").sum())
    print("Countries where one customer is >= 70% of the country's revenue:",
          top_in_country[top_in_country >= 0.7].round(2).to_dict())


def chart(lines):
    """Draw cumulative revenue curves for customers and products.

    Args:
        lines (pandas.DataFrame): Order lines from ``common.load_all``.

    Returns:
        None. Saves q7_concentration_curve.png.
    """
    fig, ax = c.new_figure(8, 5)
    top3 = shares(lines, "CustomerID").head(3).sum()
    top_prod = shares(lines, "ProductName")
    for key, label, color in [("CustomerID", "Customers (89)", c.BLUE),
                              ("ProductName", "Products (77)", c.ORANGE)]:
        sh = shares(lines, key)
        x = np.concatenate([[0], np.arange(1, len(sh) + 1) / len(sh) * 100])
        y = np.concatenate([[0], sh.cumsum().values * 100])
        ax.plot(x, y, color=color, linewidth=2, label=label)
        k = int(round(len(sh) * 0.1))
        ax.plot(x[k], y[k], "o", color=color, markersize=7,
                markeredgecolor=c.SURFACE, markeredgewidth=2)
        is_cust = key == "CustomerID"
        ax.annotate(f"Top 10% of {label.split()[0].lower()} = {y[k]:.0f}% of revenue",
                    (x[k], y[k]), xytext=(3, 88) if is_cust else (36, 16),
                    textcoords="data", fontsize=9, color=c.INK2,
                    arrowprops=dict(arrowstyle="-", color=c.GRAY, linewidth=0.8))
    ax.plot([0, 100], [0, 100], color=c.AXIS, linewidth=1)
    ax.text(62, 55, "Perfectly even", color=c.GRAY, fontsize=8.5, rotation=0)
    c.style_axes(ax, f"Three customers bring {top3:.0%} of sales, and one wine "
                     f"({top_prod.index[0]}) brings {top_prod.iloc[0]:.0%}",
                 "Share of customers / products, largest first (%)",
                 "Cumulative share of revenue (%)",
                 subtitle="Cumulative revenue curve, Jul 1996 – May 1998, actual prices.")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 102)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    c.save_figure(fig, "q7_concentration_curve")


def main():
    """Run the full Q7 analysis.

    Args:
        None.

    Returns:
        None. Prints results and writes Q7 tables and the figure.
    """
    tables, lines, orders = c.load_all()
    overall(lines)
    over_time(lines)
    top_product(lines)
    stress_test(lines)
    chart(lines)


if __name__ == "__main__":
    main()
