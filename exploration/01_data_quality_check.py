"""Step 1: check the raw workbook for data quality problems.

Run from the project folder; the data path is relative.
"""
import pandas as pd

DATA_PATH = "data/Northwind Database.xlsx"


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


def load_tables(path):
    """Read every sheet of the workbook, with no cleaning.

    Args:
        path (str): Path to the Northwind Excel workbook.

    Returns:
        dict[str, pandas.DataFrame]: One table per sheet name.
    """
    return pd.read_excel(path, sheet_name=None)


def overview(t):
    """Print table sizes and the date range of each date column.

    Args:
        t (dict[str, pandas.DataFrame]): Raw tables.

    Returns:
        None. Prints to standard output.
    """
    section("1. Tables: rows x columns")
    for name, df in t.items():
        print(f"{name:16s} {df.shape[0]:5d} rows x {df.shape[1]:3d} cols")

    o = t["Orders"]
    section("2. Date ranges")
    for col in ["OrderDate", "RequiredDate", "ShippedDate"]:
        print(f"{col:13s} {o[col].min().date()} -> {o[col].max().date()}")
    e = t["Employees"]
    for col in ["BirthDate", "HireDate"]:
        print(f"Employees.{col:9s} {e[col].min().date()} -> {e[col].max().date()}")


def missing_values(t):
    """Print blank counts for every column that has blanks.

    Args:
        t (dict[str, pandas.DataFrame]): Raw tables.

    Returns:
        None. Prints to standard output.
    """
    section("3. Missing values (columns with at least one blank)")
    for name, df in t.items():
        miss = df.isna().sum()
        miss = miss[miss > 0]
        if len(miss):
            print(f"\n[{name}] ({len(df)} rows)")
            for col, n in miss.items():
                print(f"  {col:16s} {n:4d} blank ({n / len(df):.0%})")


def duplicates(t):
    """Print duplicate rows, duplicate keys, and repeated names.

    Args:
        t (dict[str, pandas.DataFrame]): Raw tables.

    Returns:
        None. Prints to standard output.
    """
    section("4. Duplicates")
    keys = {
        "Categories": ["CategoryID"], "Customers": ["CustomerID"],
        "Employees": ["EmployeeID"], "Orders": ["OrderID"],
        "Shippers": ["ShipperID"], "Product": ["ProductID"],
        "Suppliers": ["SupplierID"],
        "Orders Details": ["OrderID", "ProductID"],
    }
    for name, key in keys.items():
        df = t[name]
        print(f"{name:16s} duplicate full rows: {df.duplicated().sum():3d}  "
              f"duplicate key {key}: {df.duplicated(subset=key).sum():3d}")
    c = t["Customers"]
    print("Customers with duplicate CompanyName:",
          c["CompanyName"].duplicated().sum())
    p = t["Product"]
    print("Products with duplicate ProductName:",
          p["ProductName"].duplicated().sum())


def foreign_keys(t):
    """Check links between tables and list unused records.

    Args:
        t (dict[str, pandas.DataFrame]): Raw tables.

    Returns:
        None. Prints broken links, orders without lines, customers
        without orders, and products never sold.
    """
    section("5. Links between tables (references to missing records)")
    o, d, p = t["Orders"], t["Orders Details"], t["Product"]
    checks = [
        ("Orders.CustomerID -> Customers", o["CustomerID"], t["Customers"]["CustomerID"]),
        ("Orders.EmployeeID -> Employees", o["EmployeeID"], t["Employees"]["EmployeeID"]),
        ("Orders.ShipVia -> Shippers", o["ShipVia"], t["Shippers"]["ShipperID"]),
        ("Details.OrderID -> Orders", d["OrderID"], o["OrderID"]),
        ("Details.ProductID -> Product", d["ProductID"], p["ProductID"]),
        ("Product.SupplierID -> Suppliers", p["SupplierID"], t["Suppliers"]["SupplierID"]),
        ("Product.CategoryID -> Categories", p["CategoryID"], t["Categories"]["CategoryID"]),
        ("Employees.ReportsTo -> Employees", t["Employees"]["ReportsTo"].dropna(),
         t["Employees"]["EmployeeID"]),
    ]
    for label, child, parent in checks:
        bad = child[~child.isin(parent)]
        print(f"{label:36s} broken links: {len(bad):3d} {sorted(bad.unique())[:10]}")

    print("\nOrders with no line items:",
          (~o["OrderID"].isin(d["OrderID"])).sum())
    no_orders = t["Customers"][~t["Customers"]["CustomerID"].isin(o["CustomerID"])]
    print("Customers with no orders:", len(no_orders),
          no_orders["CustomerID"].tolist())
    unsold = p[~p["ProductID"].isin(d["ProductID"])]
    print("Products never sold:", len(unsold), unsold["ProductName"].tolist())


def time_coverage(t):
    """Print orders per month and per year to find partial periods.

    Args:
        t (dict[str, pandas.DataFrame]): Raw tables.

    Returns:
        None. Prints to standard output.
    """
    section("6. Time coverage: orders per month (partial months?)")
    o = t["Orders"]
    m = o.groupby(o["OrderDate"].dt.to_period("M")).agg(
        orders=("OrderID", "count"),
        first_day=("OrderDate", "min"), last_day=("OrderDate", "max"))
    m["days_with_orders"] = o.groupby(o["OrderDate"].dt.to_period("M"))[
        "OrderDate"].nunique()
    print(m.to_string())
    print("\nOrders per year:")
    print(o.groupby(o["OrderDate"].dt.year)["OrderID"].count().to_string())
    print("Months per year:")
    print(o.groupby(o["OrderDate"].dt.year)["OrderDate"].apply(
        lambda s: s.dt.month.nunique()).to_string())


def invalid_values(t):
    """Print counts of impossible or suspicious values.

    Covers prices, quantities, discounts, freight, dates, unshipped
    and late orders, stock levels, and employee ages at hire.

    Args:
        t (dict[str, pandas.DataFrame]): Raw tables.

    Returns:
        None. Prints to standard output.
    """
    section("7. Impossible or suspicious values")
    o, d, p, e = t["Orders"], t["Orders Details"], t["Product"], t["Employees"]
    print("Details UnitPrice <= 0:", (d["UnitPrice"] <= 0).sum())
    print("Details Quantity <= 0:", (d["Quantity"] <= 0).sum())
    print("Details Discount outside 0-1:",
          ((d["Discount"] < 0) | (d["Discount"] > 1)).sum())
    disc = d.merge(o[["OrderID", "OrderDate"]], on="OrderID")
    print("Discount rates (rounded to 2 decimals) x order year, line counts:")
    print(pd.crosstab(disc["Discount"].round(2), disc["OrderDate"].dt.year)
          .to_string())
    print("Quantity range:", d["Quantity"].min(), "-", d["Quantity"].max())
    print("UnitPrice range:", d["UnitPrice"].min(), "-", d["UnitPrice"].max())
    print("Freight < 0:", (o["Freight"] < 0).sum(),
          "| Freight == 0:", (o["Freight"] == 0).sum(),
          "| range:", o["Freight"].min(), "-", o["Freight"].max())
    print("ShippedDate before OrderDate:",
          (o["ShippedDate"] < o["OrderDate"]).sum())
    print("RequiredDate before OrderDate:",
          (o["RequiredDate"] < o["OrderDate"]).sum())
    unshipped = o[o["ShippedDate"].isna()]
    print("Not shipped (ShippedDate blank):", len(unshipped),
          "| their order dates:", unshipped["OrderDate"].min().date(), "->",
          unshipped["OrderDate"].max().date())
    late = (o["ShippedDate"] > o["RequiredDate"]).sum()
    print("Shipped after RequiredDate (late):", late)
    lead = (o["RequiredDate"] - o["OrderDate"]).dt.days
    print("Days between order and required date:",
          lead.value_counts().sort_index().to_dict())

    print("\nProduct Price <= 0:", (p["Price"] <= 0).sum(),
          "| UnitsInStock < 0:", (p["UnitsInStock"] < 0).sum(),
          "| UnitsOnOrder < 0:", (p["UnitsOnOrder"] < 0).sum())
    print("Discontinued products:", p["Discontinued"].sum())

    age_hire = (e["HireDate"] - e["BirthDate"]).dt.days / 365.25
    print("\nEmployees age at hire:",
          dict(zip(e["EmployeeID"], age_hire.round(1))))


def price_consistency(t):
    """Compare order-line prices with the current list price.

    Args:
        t (dict[str, pandas.DataFrame]): Raw tables.

    Returns:
        None. Prints the price ratios and mismatches by year.
    """
    section("8. Price in order lines vs. current product list price")
    d = t["Orders Details"].merge(
        t["Orders"][["OrderID", "OrderDate"]], on="OrderID").merge(
        t["Product"][["ProductID", "ProductName", "Price"]], on="ProductID")
    d["ratio"] = (d["UnitPrice"] / d["Price"]).round(3)
    print("Ratio order-line price / list price (count of lines):")
    print(d["ratio"].value_counts().to_string())
    print("\nLines priced differently from list price, by year:")
    diff = d["UnitPrice"] != d["Price"]
    print(diff.groupby(d["OrderDate"].dt.year).agg(["sum", "count"]).to_string())


def product_extra_columns(t):
    """Describe the extra, non-original columns in Product.

    Args:
        t (dict[str, pandas.DataFrame]): Raw tables.

    Returns:
        None. Prints to standard output.
    """
    section("9. Extra / unusual columns in Product sheet")
    p = t["Product"]
    for col in ["Cheap", "NewPrice", "Cheap.1", "IsCheap", "Unnamed: 14",
                "NewPrice.1"]:
        s = p[col]
        print(f"{col:12s} non-blank={s.notna().sum():3d} "
              f"sample={s.dropna().unique()[:6].tolist()}")
    print("\nNewPrice / Price:", (p["NewPrice"] / p["Price"]).round(3).unique())
    x = p[p["NewPrice.1"].notna()]
    print("NewPrice.1 / Price:", (x["NewPrice.1"] / x["Price"]).round(3).unique(),
          "| filled only for Price <=", x["Price"].max())
    print("Cheap vs IsCheap:")
    print(pd.crosstab(p["Cheap"], p["IsCheap"]).to_string())
    print("Is Product sheet sorted by ProductID?",
          p["ProductID"].is_monotonic_increasing)
    print("Categories.Picture non-blank:", t["Categories"]["Picture"].notna().sum())


def text_consistency(t):
    """Check country names, ship-to vs. customer, and stray spaces.

    Args:
        t (dict[str, pandas.DataFrame]): Raw tables.

    Returns:
        None. Prints to standard output.
    """
    section("10. Text consistency (country names, shipping vs. customer country)")
    print("Customer countries:", sorted(t["Customers"]["Country"].dropna().unique()))
    print("Ship countries:   ", sorted(t["Orders"]["ShipCountry"].dropna().unique()))
    print("Supplier countries:", sorted(t["Suppliers"]["Country"].dropna().unique()))
    m = t["Orders"].merge(t["Customers"][["CustomerID", "Country"]],
                          on="CustomerID", how="left")
    mism = m[m["ShipCountry"] != m["Country"]]
    print("Orders shipped to a country different from the customer's country:",
          len(mism))
    if len(mism):
        print(mism[["OrderID", "CustomerID", "Country", "ShipCountry"]]
              .head(10).to_string())
    n = m.merge(t["Customers"][["CustomerID", "CompanyName"]], on="CustomerID")
    diff_name = n[n["ShipName"] != n["CompanyName"]]
    print("\nOrders whose ShipName differs from the customer's CompanyName:",
          len(diff_name))
    print(diff_name[["OrderID", "CustomerID", "CompanyName", "ShipName",
                     "ShipCity"]].to_string())
    for name, df in t.items():
        for col in df.select_dtypes(include=["object", "str"]).columns:
            s = df[col].dropna().astype(str)
            n = (s != s.str.strip()).sum()
            if n:
                print(f"Leading/trailing spaces: {name}.{col}: {n}")


def main():
    """Run every check in this script in order.

    Args:
        None.

    Returns:
        None. Prints results to standard output.
    """
    t = load_tables(DATA_PATH)
    overview(t)
    missing_values(t)
    duplicates(t)
    foreign_keys(t)
    time_coverage(t)
    invalid_values(t)
    price_consistency(t)
    product_extra_columns(t)
    text_consistency(t)


if __name__ == "__main__":
    main()
