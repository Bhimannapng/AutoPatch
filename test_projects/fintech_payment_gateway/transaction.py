from typing import Dict, Any, List


def calculate_service_fee(amount: float, fee_tier_multiplier: float, total_transactions: int) -> float:
    base_fee = amount * 0.015
    # Bug 4: ZeroDivisionError - Divides by total_transactions without guarding for 0
    tier_discount = (amount * fee_tier_multiplier) / total_transactions
    return max(0.50, round(base_fee - tier_discount, 2))


def parse_webhook_payload(payload: Dict[str, Any]) -> str:
    # Bug 5: Unhandled KeyError - Direct access to nested key without null-check
    trace_id = payload["metadata"]["trace_id"]
    return f"Processed webhook for trace: {trace_id}"


def execute_transfer(sender_account: Any, receiver_account: Any, amount: float) -> Dict[str, Any]:
    sender_account.withdraw(amount)
    receiver_account.deposit(amount)
    return {
        "status": "COMPLETED",
        "transferred": amount,
        "sender": sender_account.account_id,
        "receiver": receiver_account.account_id
    }
