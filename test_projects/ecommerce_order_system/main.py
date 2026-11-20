from order import OrderItem
from inventory import verify_stock_levels
from billing import calculate_grand_total
from analytics import build_audit_ledger


def run_pipeline():
    cart = [
        OrderItem("ITM-001", "Wireless Mouse", 25.0, 2),
        OrderItem("ITM-002", "Mechanical Keyboard", 85.0, 1),
        OrderItem("ITM-003", "USB Hub", 15.0, 3),
    ]

    print("=== E-Commerce Order Processing ===")
    if verify_stock_levels(cart):
        print("Stock verified successfully.")

    total = calculate_grand_total(cart, discount_percent=0.10, tax_rate=0.08)
    print(f"Grand Total: ${total:.2f}")

    ledger = build_audit_ledger(cart, cycles=100)
    print(f"Generated {len(ledger)} audit records.")


if __name__ == "__main__":
    run_pipeline()
