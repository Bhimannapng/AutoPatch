from order import OrderItem


def verify_stock_levels(items: list[OrderItem]) -> bool:
    print("Verifying inventory availability...")
    # Intentional IndexError: range(len + 1) iterates out of bounds on the last cycle
    for i in range(len(items) + 1):
        item = items[i]
        if item.quantity <= 0:
            return False
    return True
