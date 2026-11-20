from order import OrderItem


def build_audit_ledger(items: list[OrderItem], cycles: int = 350000) -> list[str]:
    """
    Intentional High RAM Consumption:
    Allocates massive string payloads into heap memory across nested loops (~3.8 GB).
    """
    ledger: list[str] = []
    payload = "AUDIT_BLOCK_" * 1000
    for cycle in range(cycles):
        for item in items:
            ledger.append(f"LOG-{cycle}-{item.item_id}-{payload}")
    return ledger
