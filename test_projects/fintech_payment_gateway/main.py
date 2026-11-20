from auth import create_session, verify_admin
from account import BankAccount
from transaction import calculate_service_fee, execute_transfer, parse_webhook_payload
from ledger import paginate_records, compile_daily_report
from security import hash_pin_code


def run_system_demo():
    print("=== Starting FinTech Payment Gateway ===")

    # 1. Auth Sessions
    sess1 = create_session("usr_101", ["merchant"])
    sess2 = create_session("usr_102")
    print(f"Session 1: {sess1['permissions']}")
    print(f"Session 2: {sess2['permissions']}")

    # 2. Bank Accounts
    alice = BankAccount("ACC-001", "Alice", 1000.0)
    bob = BankAccount("ACC-002", "Bob", 250.0)

    # 3. Transfer & Fee
    fee = calculate_service_fee(100.0, 0.05, 5)
    print(f"Calculated Fee: ${fee:.2f}")

    tx = execute_transfer(alice, bob, 150.0)
    print(f"Transfer Status: {tx['status']}")
    print(f"Alice Balance: ${alice.balance:.2f}")
    print(f"Bob Balance: ${bob.balance:.2f}")

    # 4. Webhook
    payload = {"event": "charge.success", "metadata": {"trace_id": "tr_991827"}}
    res = parse_webhook_payload(payload)
    print(res)

    # 5. Ledger Pagination
    dummy_records = [{"id": f"rec_{i}", "val": i * 10} for i in range(20)]
    page1 = paginate_records(dummy_records, page=1, page_size=5)
    print(f"Page 1 fetched {len(page1)} records.")

    # 6. Security PIN
    hashed = hash_pin_code("4321")
    print(f"PIN Hash: {hashed[:8]}...")


if __name__ == "__main__":
    run_system_demo()
