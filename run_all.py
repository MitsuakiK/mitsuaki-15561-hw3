"""Reproduce every figure, table, and log in outputs/.

Usage: ``python run_all.py`` from the project folder.
"""
import contextlib
import importlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

MODULES = ["q1_price_increase", "q2_growth_drivers", "q3_rush_orders",
           "q4_discounts", "q5_country_markets", "q6_at_risk_customers",
           "q7_concentration"]


def main():
    """Run each analysis script and save its printed output as a log.

    Args:
        None.

    Returns:
        None. Writes outputs/logs/<module>.txt; the scripts write
        figures and tables.
    """
    log_dir = ROOT / "outputs" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    for name in MODULES:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            importlib.import_module(name).main()
        (log_dir / f"{name}.txt").write_text(buffer.getvalue(), encoding="utf-8")
        print(f"done: {name} -> outputs/logs/{name}.txt")
    print("Figures: outputs/figures/  Tables: outputs/tables/")


if __name__ == "__main__":
    main()
