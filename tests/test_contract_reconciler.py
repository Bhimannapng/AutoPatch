import os
import tempfile
from contract_reconciler import reconcile_project_contracts, discover_project_signatures


def test_generator_len_reconciliation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        analytics_path = os.path.join(tmp_dir, "analytics.py")
        main_path = os.path.join(tmp_dir, "main.py")

        with open(analytics_path, "w") as f:
            f.write("""
def build_audit_ledger(items, cycles=100):
    for i in range(cycles):
        yield f"audit-{i}"
""")

        with open(main_path, "w") as f:
            f.write("""
from analytics import build_audit_ledger

def run():
    ledger = build_audit_ledger([])
    print(f"Total: {len(ledger)}")
""")

        logs = reconcile_project_contracts(tmp_dir)
        assert len(logs) > 0

        with open(main_path, "r") as f:
            healed = f.read()

        assert "len(list(ledger))" in healed


def test_extra_arguments_signature_expansion():
    with tempfile.TemporaryDirectory() as tmp_dir:
        trans_path = os.path.join(tmp_dir, "transaction.py")
        main_path = os.path.join(tmp_dir, "main.py")

        with open(trans_path, "w") as f:
            f.write("""
def execute_transfer(sender, receiver, amount):
    return {"status": "SUCCESS"}
""")

        with open(main_path, "w") as f:
            f.write("""
from transaction import execute_transfer

def run():
    tx = execute_transfer("alice", "bob", 100.0, 5.0)
""")

        logs = reconcile_project_contracts(tmp_dir)
        assert len(logs) > 0

        with open(trans_path, "r") as f:
            healed = f.read()

        assert "*args" in healed
