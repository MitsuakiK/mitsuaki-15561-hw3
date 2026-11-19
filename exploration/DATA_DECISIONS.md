# Data Quality Decisions

Evidence for each issue comes from `exploration/01_data_quality_check.py`
(run: `python exploration/01_data_quality_check.py`).

| ID | Issue | Evidence | Decision |
|----|-------|----------|----------|
| A | Partial years | Orders run 1996-07-04 to 1998-05-06; 1996 has 6 months, 1998 has 4 full months plus 6 days of May (14 orders). | Compare by month, not by calendar year. Exclude May 1998 from trend analysis. For year-over-year comparisons, compare the same months (e.g., Jan–Apr 1997 vs. Jan–Apr 1998). |
| B | List price differs from transaction price | `Product.Price` is the current list price. 404 of 405 order lines in 1996 were sold at ~80% of it; all 1998 lines match it. | Compute revenue from `Orders Details`: `UnitPrice * Quantity * (1 - Discount)`. Do not use `Product.Price` for historical revenue. |
| C | Non-original columns in Product sheet | `Cheap`, `Cheap.1`, `IsCheap`, `NewPrice` (= Price x 1.07), `NewPrice.1` (= Price x 1.1, only for Price <= 15), empty `Unnamed: 14`. `Cheap` and `IsCheap` disagree on 4 rows. | Do not use these columns. The source Excel file is left unchanged. |
| D | Ship-to differs from ordering customer | Orders 10248, 10249, 10260, 10808 ship to another customer's address in a different country. (12 more orders differ only in spelling of ShipName.) | Use the customer's country (`Customers.Country`) for geography. Mention the 4 orders as a caveat. |
| E | 21 unshipped orders | `ShippedDate` blank; all ordered 1998-04-08 to 1998-05-06, none past `RequiredDate` at the data end. | Keep in revenue. Exclude only from shipping-time / on-time analysis. |
| F | Discount precision and rare rates | Stored as floats like 0.0500000007. Rates of 1–4% and 6% appear on 8 lines, all in 1998. | Round discounts to 2 decimals. Keep the 8 lines. |
| G | Customers with no orders | FISSA and PARIS have no orders. | Keep; note when counting customers (89 active of 91). |

Not treated as problems: blank Region / Fax / HomePage (normal for some
countries), 8 discontinued products still sold until the end of the data,
employee birth dates (ages at hire 23–40 are plausible).

Limitation: Northwind is a fictional teaching dataset, so some patterns may
reflect how the data was generated rather than real business behavior.
