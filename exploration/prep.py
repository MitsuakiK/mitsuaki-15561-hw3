"""Shared data loading and cleaning for the exploration scripts.

Applies the rules in DATA_DECISIONS.md; src/common.py is the
final version used for the results.
"""
from pathlib import Path

import pandas as pd

# Relative to the repository root, so it works from any working directory.
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "Northwind Database.xlsx"
LAST_FULL_MONTH = pd.Period("1998-04", freq="M")


def load_tables(path=DATA_PATH):
    """Read every sheet of the Northwind workbook.

    Args:
        path (pathlib.Path): Northwind Excel workbook.

    Returns:
        dict[str, pandas.DataFrame]: One table per sheet name; the
        Product table is cut to its ten real columns (Decision C).
    """
    t = pd.read_excel(path, sheet_name=None)
    t["Product"] = t["Product"][[
        "ProductID", "ProductName", "SupplierID", "CategoryID",
        "QuantityPerUnit", "Price", "UnitsInStock", "UnitsOnOrder",
        "ReorderLevel", "Discontinued"]]  # Decision C
    return t


def build_lines(t):
    """Build the order table and the order-line table.

    Orders get customer, employee (with ``EmpCountry``), and shipper
    fields plus ``Month``, ``ShipDays``, and ``Late``. Lines get
    ``Gross`` and ``Revenue`` and are joined to product, category,
    supplier (with ``SupCountry``), and order fields.

    Args:
        t (dict[str, pandas.DataFrame]): Output of ``load_tables``.

    Returns:
        tuple[pandas.DataFrame, pandas.DataFrame]: Orders and order
        lines.
    """
    o = t["Orders"].merge(
        t["Customers"][["CustomerID", "CompanyName", "Country"]],
        on="CustomerID", how="left")  # Decision D: customer country
    o = o.merge(t["Employees"][["EmployeeID", "LastName", "Country"]]
                .rename(columns={"Country": "EmpCountry"}), on="EmployeeID")
    o = o.merge(t["Shippers"].rename(columns={
        "ShipperID": "ShipVia", "CompanyName": "Shipper"})[
        ["ShipVia", "Shipper"]], on="ShipVia")
    o["Month"] = o["OrderDate"].dt.to_period("M")
    o["ShipDays"] = (o["ShippedDate"] - o["OrderDate"]).dt.days
    late = (o["ShippedDate"] > o["RequiredDate"]).astype("boolean")
    o["Late"] = late.mask(o["ShippedDate"].isna())  # Decision E: unshipped = NA

    d = t["Orders Details"].copy()
    d["Discount"] = d["Discount"].round(2)  # Decision F
    d["Gross"] = d["UnitPrice"] * d["Quantity"]
    d["Revenue"] = d["Gross"] * (1 - d["Discount"])  # Decision B
    p = t["Product"].merge(t["Categories"][["CategoryID", "CategoryName"]],
                           on="CategoryID").merge(
        t["Suppliers"][["SupplierID", "CompanyName", "Country"]].rename(
            columns={"CompanyName": "Supplier", "Country": "SupCountry"}),
        on="SupplierID")
    d = d.merge(p, on="ProductID").merge(o, on="OrderID")
    return o, d


def order_table(o, d):
    """Add line totals to each order.

    Args:
        o (pandas.DataFrame): Orders from ``build_lines``.
        d (pandas.DataFrame): Order lines from ``build_lines``.

    Returns:
        pandas.DataFrame: Orders with summed ``Revenue``, ``Gross``,
        ``Units``, line count ``Lines``, and ``MaxDiscount``; orders
        without lines are dropped.
    """
    agg = d.groupby("OrderID").agg(
        Revenue=("Revenue", "sum"), Gross=("Gross", "sum"),
        Lines=("ProductID", "count"), Units=("Quantity", "sum"),
        MaxDiscount=("Discount", "max"))
    return o.merge(agg, on="OrderID")
