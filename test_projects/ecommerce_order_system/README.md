# E-Commerce Order System (AutoPatch Benchmark Fixture)

This project contains 4 intentional bugs to benchmark AutoPatch:
1. `order.py` (Line 12): Missing colon `:` in `def format_summary(self) -> str` (SyntaxError).
2. `inventory.py` (Line 7): `range(len(items) + 1)` out-of-bounds loop boundary (IndexError).
3. `billing.py` (Line 8): Divides by `tax_rate` instead of multiplying, creating a ZeroDivisionError risk and price calculation error.
4. `analytics.py` (Line 11): Unbounded nested loop appending ~3.8 GB of string buffers into memory (Memory/OOM Hazard).
