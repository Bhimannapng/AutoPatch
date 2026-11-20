# FinTech Payment Gateway (AutoPatch Advanced Benchmark)

This is a comprehensive, multi-module benchmark project designed to challenge AutoPatch across syntax, logical calculation, security exposures, memory usage, and runtime boundary hazards.

## Injected Defects & Challenges:
1. `auth.py:6`: **Mutable Default Argument** (`permissions: List[str] = []`) leaking user state between sessions.
2. `auth.py:16`: **SyntaxError** - Missing colon `:` in `def verify_admin(session: Dict[str, Any]) -> bool`.
3. `account.py:20`: **Logic Flaw** - `withdraw()` adds amount to balance (`self.balance += amount`) instead of deducting.
4. `transaction.py:7`: **ZeroDivisionError** - `(amount * fee_tier_multiplier) / total_transactions` without checking if `total_transactions == 0`.
5. `transaction.py:13`: **Unhandled KeyError** - Unchecked direct access to nested dictionary `payload["metadata"]["trace_id"]`.
6. `ledger.py:9`: **IndexError** - `range(offset, offset + page_size + 1)` out-of-bounds pagination loop.
7. `ledger.py:17`: **Performance / RAM Bottleneck** - Inefficient string accumulation inside nested loops.
8. `security.py:5`: **Security Vulnerability** - Hardcoded Stripe live API secret key in code.
9. `security.py:10`: **Cryptographic Vulnerability** - Insecure MD5 hashing algorithm for security PIN codes.
