"""Q2: Did growth come from more customers, orders, or bigger orders?"""
import numpy as np
import pandas as pd

import common as c

# Each comparison: label, (earlier start, earlier end), (later start, later end).
# End dates are exclusive. All windows are complete months.
COMPARISONS = [
    ("Jan-Apr 1998 vs Jan-Apr 1997", ("1997-01-01", "1997-05-01"), ("1998-01-01", "1998-05-01")),
    ("Nov 1997-Apr 1998 vs Nov 1996-Apr 1997", ("1996-11-01", "1997-05-01"), ("1997-11-01", "1998-05-01")),
    ("Jul-Dec 1997 vs Jul-Dec 1996", ("1996-07-01", "1997-01-01"), ("1997-07-01", "1998-01-01")),
]
MAIN = COMPARISONS[0][0]


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


def decompose(p1, p2, value_col):
    """Split the revenue change between two periods into three factors.

    Revenue = customers x orders per customer x revenue per order.
    Each factor's share of growth is its log ratio divided by the log
    ratio of revenue, so the three shares sum to 1.

    Args:
        p1 (pandas.DataFrame): Orders in the earlier period.
        p2 (pandas.DataFrame): Orders in the later period.
        value_col (str): Revenue column, "Revenue" or "ConstRevenue".

    Returns:
        tuple: ``(a, b, ratio, share)`` -- dicts of the factor levels
        in the earlier and later period, later/earlier ratios, and
        each factor's share of growth.
    """
    def parts(p):
        """Return the three revenue factors and revenue for one period.

        Args:
            p (pandas.DataFrame): Orders in one period.

        Returns:
            dict[str, float]: The four values keyed by name.
        """
        n = p["CustomerID"].nunique()
        return {"customers": n, "orders_per_customer": len(p) / n,
                "revenue_per_order": p[value_col].sum() / len(p),
                "revenue": p[value_col].sum()}
    a, b = parts(p1), parts(p2)
    ratio = {k: b[k] / a[k] for k in a}
    total_log = np.log(ratio["revenue"])
    share = {k: np.log(ratio[k]) / total_log
             for k in ["customers", "orders_per_customer", "revenue_per_order"]}
    return a, b, ratio, share


def decomposition_table(orders):
    """Decompose revenue growth for every comparison and price basis.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.

    Returns:
        pandas.DataFrame: One row per comparison and basis (constant
        or actual prices) with levels, ratios, and growth shares. Also
        prints it and saves q2_decomposition.csv.
    """
    c.header("Q2.1 Revenue = customers x orders per customer x revenue per order")
    rows = []
    for label, (s1, e1), (s2, e2) in COMPARISONS:
        p1, p2 = period(orders, s1, e1), period(orders, s2, e2)
        for value_col, basis in [("ConstRevenue", "constant prices"),
                                 ("Revenue", "actual prices")]:
            a, b, ratio, share = decompose(p1, p2, value_col)
            rows.append({"comparison": label, "basis": basis,
                         **{f"before_{k}": v for k, v in a.items()},
                         **{f"after_{k}": v for k, v in b.items()},
                         **{f"x_{k}": v for k, v in ratio.items()},
                         **{f"share_of_growth_{k}": v for k, v in share.items()}})
    t = pd.DataFrame(rows)
    show = ["comparison", "basis", "x_revenue", "x_customers",
            "x_orders_per_customer", "x_revenue_per_order",
            "share_of_growth_customers", "share_of_growth_orders_per_customer",
            "share_of_growth_revenue_per_order"]
    print(t[show].round(2).to_string(index=False))
    print("\nLevels (constant prices):")
    lv = t[t["basis"] == "constant prices"][[
        "comparison", "before_customers", "after_customers",
        "before_orders_per_customer", "after_orders_per_customer",
        "before_revenue_per_order", "after_revenue_per_order"]]
    print(lv.round(2).to_string(index=False))
    c.save_table(t, "q2_decomposition", index=False)
    return t


def customer_bridge(orders):
    """Attribute the main comparison's revenue change to customers.

    Groups customers into ordered in both periods, only 1997, or only
    1998, and checks how much the top contributors drive the change.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.

    Returns:
        None. Prints results and saves q2_customer_bridge.csv.
    """
    c.header(f"Q2.2 Which customers drove the change? ({MAIN}, constant prices)")
    (_, (s1, e1), (s2, e2)) = COMPARISONS[0]
    p1, p2 = period(orders, s1, e1), period(orders, s2, e2)
    agg = lambda p: p.groupby("CustomerID").agg(rev=("ConstRevenue", "sum"),
                                               n=("OrderID", "count"))
    b = agg(p1).merge(agg(p2), left_index=True, right_index=True, how="outer",
                      suffixes=("_before", "_after")).fillna(0)
    b["change"] = b["rev_after"] - b["rev_before"]
    b["group"] = np.select(
        [(b["n_before"] > 0) & (b["n_after"] > 0), b["n_after"] > 0],
        ["ordered in both periods", "ordered only in 1998"], "ordered only in 1997")
    g = b.groupby("group").agg(customers=("change", "size"),
                               change=("change", "sum"))
    g["share_of_net_change"] = g["change"] / b["change"].sum()
    print(g.round(2).to_string())
    first_order = orders.groupby("CustomerID")["OrderDate"].min()
    only98 = b.index[b["group"] == "ordered only in 1998"]
    brand_new = (first_order[only98] >= s2).sum()
    print(f"Of the {len(only98)} 'only in 1998' customers, {brand_new} placed their "
          f"first-ever order in Jan-Apr 1998; the rest are returning customers.")
    both =b[b["group"] == "ordered in both periods"]
    print(f"\nIn-both customers: {(both['change'] > 0).sum()} grew, "
          f"{(both['change'] < 0).sum()} shrank; orders per customer "
          f"{both['n_before'].mean():.2f} -> {both['n_after'].mean():.2f}")
    top = b.sort_values("change", ascending=False)
    top_share = top["change"].head(10).sum() / b["change"].sum()
    print(f"Top 10 contributors = {top_share:.0%} of net change; "
          f"customers with positive change: {(b['change'] > 0).sum()} of {len(b)}")
    ex3 = b.drop(top.index[:3])
    print("Growth excluding the 3 biggest contributors: "
          f"{ex3['rev_after'].sum() / ex3['rev_before'].sum() - 1:+.0%} "
          f"(all customers: {b['rev_after'].sum() / b['rev_before'].sum() - 1:+.0%})")
    names = orders.drop_duplicates("CustomerID").set_index("CustomerID")[
        ["CompanyName", "Country"]]
    print("\nTop 10 contributors:")
    print(top.head(10).join(names).round(0).to_string())
    c.save_table(b.join(names).sort_values("change", ascending=False),
                 "q2_customer_bridge")


def robustness(orders):
    """Repeat the main decomposition without the largest 1% of orders.

    Args:
        orders (pandas.DataFrame): Orders from ``common.load_all``.

    Returns:
        None. Prints the factor ratios.
    """
    c.header("Q2.3 Robustness: drop very large orders (top 1%)")
    cutoff = orders["ConstRevenue"].quantile(0.99)
    trimmed = orders[orders["ConstRevenue"] <= cutoff]
    (_, (s1, e1), (s2, e2)) = COMPARISONS[0]
    _, _, ratio, share = decompose(period(trimmed, s1, e1),
                                   period(trimmed, s2, e2), "ConstRevenue")
    print(f"Cutoff ${cutoff:,.0f}. Revenue x{ratio['revenue']:.2f}; "
          f"customers x{ratio['customers']:.2f}, frequency x"
          f"{ratio['orders_per_customer']:.2f}, order size x"
          f"{ratio['revenue_per_order']:.2f}")


def chart(t):
    """Draw the three growth factors for each comparison as bars.

    Args:
        t (pandas.DataFrame): Table from ``decomposition_table``;
            only constant-price rows are plotted.

    Returns:
        None. Saves q2_growth_decomposition.png.
    """
    d = t[t["basis"] == "constant prices"].reset_index(drop=True)
    factors = [("x_customers", "Active customers", c.BLUE),
               ("x_orders_per_customer", "Orders per customer", c.ORANGE),
               ("x_revenue_per_order", "Revenue per order", c.AQUA)]
    fig, ax = c.new_figure(8, 4.8)
    width = 0.26
    x = np.arange(len(d))
    for i, (col, label, color) in enumerate(factors):
        vals = d[col] - 1
        bars = ax.bar(x + (i - 1) * width, vals * 100, width - 0.03,
                      color=color, label=label)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + (2 if v >= 0 else -2),
                    f"{v:+.0%}", ha="center", va="bottom" if v >= 0 else "top",
                    fontsize=8.5, color=c.INK2)
    ax.axhline(0, color=c.AXIS, linewidth=0.8)
    ax.set_ylim(-28, 80)
    ax.set_xticks(x, [f"{lab}\n(revenue {r - 1:+.0%})" for lab, r in
                      zip(d["comparison"], d["x_revenue"])], fontsize=8.5)
    c.style_axes(ax, "Growth came mainly from customers ordering more often, "
                     "even as each order got smaller",
                 "", "Change vs. same months a year earlier (%)",
                 subtitle="Revenue split into three multiplying parts, at constant "
                          "(current list) prices to remove the April 1997 price increase.")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    c.save_figure(fig, "q2_growth_decomposition")


def main():
    """Run the full Q2 analysis.

    Args:
        None.

    Returns:
        None. Prints results and writes Q2 tables and the figure.
    """
    tables, lines, orders = c.load_all()
    t = decomposition_table(orders)
    customer_bridge(orders)
    robustness(orders)
    chart(t)


if __name__ == "__main__":
    main()
