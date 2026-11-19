"""Shared data loading, constants, and chart styling.

Each q*.py script builds its inputs with ``load_all()``.
"""
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "Northwind Database.xlsx"
FIG_DIR = ROOT / "outputs" / "figures"
TABLE_DIR = ROOT / "outputs" / "tables"

DATA_END = pd.Timestamp("1998-05-06")
LAST_FULL_MONTH = pd.Period("1998-04", freq="M")
PRICE_CHANGE_DATE = pd.Timestamp("1997-04-07")

# Validated categorical palette (light mode) and chart chrome.
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
RED, GRAY = "#e34948", "#898781"
INK, INK2, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#e1e0d9", "#c3c2b7", "#fcfcfb"

PRODUCT_COLUMNS = ["ProductID", "ProductName", "SupplierID", "CategoryID",
                   "QuantityPerUnit", "Price", "UnitsInStock", "UnitsOnOrder",
                   "ReorderLevel", "Discontinued"]


def load_tables(path=DATA_PATH):
    """Read every sheet of the Northwind workbook.

    Args:
        path (pathlib.Path): Northwind Excel workbook.

    Returns:
        dict[str, pandas.DataFrame]: One table per sheet name; the
        Product table is cut to its ten real columns (Decision C).
    """
    tables = pd.read_excel(path, sheet_name=None)
    tables["Product"] = tables["Product"][PRODUCT_COLUMNS]  # Decision C
    return tables


def build_orders(tables):
    """Build one row per order with customer and shipping fields.

    Adds ``Month``, ``ShipDays`` (order to shipment), ``Window``
    (order to required date), and ``Late`` (missing if unshipped).

    Args:
        tables (dict[str, pandas.DataFrame]): Output of ``load_tables``.

    Returns:
        pandas.DataFrame: Orders with the added columns.
    """
    o =tables["Orders"].merge(
        tables["Customers"][["CustomerID", "CompanyName", "Country"]],
        on="CustomerID", how="left")  # Decision D: customer's country
    o = o.merge(tables["Employees"][["EmployeeID", "LastName"]],
                on="EmployeeID")
    shippers = tables["Shippers"].rename(
        columns={"ShipperID": "ShipVia", "CompanyName": "Shipper"})
    o = o.merge(shippers[["ShipVia", "Shipper"]], on="ShipVia")
    o["Month"] = o["OrderDate"].dt.to_period("M")
    o["ShipDays"] = (o["ShippedDate"] - o["OrderDate"]).dt.days
    o["Window"] = (o["RequiredDate"] - o["OrderDate"]).dt.days
    late = (o["ShippedDate"] > o["RequiredDate"]).astype("boolean")
    o["Late"] = late.mask(o["ShippedDate"].isna())  # Decision E
    return o


def build_lines(tables, orders):
    """Build one row per order line with product and order data.

    Adds ``Gross`` (price x quantity), ``Revenue`` (after
    discount), and ``ConstRevenue`` (revenue at the current list
    price, which removes the April 1997 price change).

    Args:
        tables (dict[str, pandas.DataFrame]): Output of ``load_tables``.
        orders (pandas.DataFrame): Output of ``build_orders``.

    Returns:
        pandas.DataFrame: Order lines joined to products and orders.
    """
    d =tables["Orders Details"].copy()
    d["Discount"] = d["Discount"].round(2)  # Decision F
    d["Gross"] = d["UnitPrice"] * d["Quantity"]
    d["Revenue"] = d["Gross"] * (1 - d["Discount"])  # Decision B
    products = tables["Product"].merge(
        tables["Categories"][["CategoryID", "CategoryName"]], on="CategoryID")
    products = products.merge(
        tables["Suppliers"][["SupplierID", "CompanyName"]].rename(
            columns={"CompanyName": "Supplier"}), on="SupplierID")
    d = d.merge(products, on="ProductID").merge(orders, on="OrderID")
    # Revenue at today's list price: removes the April 1997 price change.
    d["ConstRevenue"] = d["Price"] * d["Quantity"] * (1 - d["Discount"])
    return d


def build_order_totals(orders, lines):
    """Add line totals to each order.

    Args:
        orders (pandas.DataFrame): Output of ``build_orders``.
        lines (pandas.DataFrame): Output of ``build_lines``.

    Returns:
        pandas.DataFrame: Orders with summed ``Revenue``,
        ``ConstRevenue``, ``Gross``, ``Units``, and line count
        ``Lines``; orders without lines are dropped.
    """
    agg =lines.groupby("OrderID").agg(
        Revenue=("Revenue", "sum"), ConstRevenue=("ConstRevenue", "sum"),
        Gross=("Gross", "sum"), Lines=("ProductID", "count"),
        Units=("Quantity", "sum"))
    return orders.merge(agg, on="OrderID")


def load_all():
    """Load the workbook and build all analysis tables.

    Args:
        None.

    Returns:
        tuple: ``(tables, lines, order_totals)`` -- the raw sheets
        (dict[str, pandas.DataFrame]), order lines from
        ``build_lines``, and orders from ``build_order_totals``.
    """
    tables =load_tables()
    orders = build_orders(tables)
    lines = build_lines(tables, orders)
    order_totals = build_order_totals(orders, lines)
    return tables, lines, order_totals


def save_table(df, name, index=True):
    """Save a table as CSV in outputs/tables/.

    Args:
        df (pandas.DataFrame): Table to save.
        name (str): File name without the .csv extension.
        index (bool): Whether to write the row index.

    Returns:
        None. Overwrites ``outputs/tables/<name>.csv``.
    """
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLE_DIR / f"{name}.csv", index=index)


def style_axes(ax, title, xlabel, ylabel, subtitle=None):
    """Apply the shared chart style and write a wrapped title block.

    Stores the header height on the figure so ``save_figure`` can
    leave room for it.

    Args:
        ax (matplotlib.axes.Axes): Axes to style.
        title (str): Headline placed at the top left of the figure.
        xlabel (str): X-axis label.
        ylabel (str): Y-axis label.
        subtitle (str | None): Smaller text under the title; None
            for no subtitle.

    Returns:
        None. Modifies ``ax`` and its figure in place.
    """
    ax.set_facecolor(SURFACE)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(0.8)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.set_xlabel(xlabel, color=INK2, fontsize=10)
    ax.set_ylabel(ylabel, color=INK2, fontsize=10)
    fig = ax.figure
    width_chars = int(fig.get_figwidth() * 13)
    title_text = textwrap.fill(title, int(fig.get_figwidth() * 9.3))
    sub_text = textwrap.fill(subtitle, width_chars) if subtitle else ""
    fig.text(0.015, 0.985, title_text, color=INK, fontsize=12.5,
             fontweight="bold", va="top", ha="left")
    n_lines = title_text.count("\n") + 1
    if sub_text:
        fig.text(0.015, 0.985 - 0.062 * n_lines * 4.6 / fig.get_figheight(),
                 sub_text, color=INK2, fontsize=9.5, va="top", ha="left")
        n_lines += sub_text.count("\n") + 1
    fig._header_fraction = 0.02 + 0.05 * n_lines * 4.6 / fig.get_figheight()


def new_figure(width=8, height=4.6):
    """Create a figure with one axes and the shared background.

    Args:
        width (float): Figure width in inches.
        height (float): Figure height in inches.

    Returns:
        tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]: The
        figure and its axes.
    """
    fig, ax = plt.subplots(figsize=(width, height), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    return fig, ax


def save_figure(fig, name):
    """Save a figure as PNG in outputs/figures/ and close it.

    Args:
        fig (matplotlib.figure.Figure): Figure to save.
        name (str): File name without the .png extension.

    Returns:
        None. Overwrites ``outputs/figures/<name>.png``.
    """
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    top = 1 - getattr(fig, "_header_fraction", 0.02)
    fig.tight_layout(rect=(0, 0, 1, top))
    fig.savefig(FIG_DIR / f"{name}.png", facecolor=fig.get_facecolor())
    plt.close(fig)


def header(title):
    """Print a section title between two rule lines.

    Args:
        title (str): Section title.

    Returns:
        None. Prints to standard output.
    """
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)
