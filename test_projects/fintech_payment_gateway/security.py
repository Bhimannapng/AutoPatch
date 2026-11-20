import hashlib
from typing import Optional


# Bug 8: Hardcoded sensitive secret in source code
STRIPE_LIVE_SECRET_KEY = "test_sandbox_dummy_secret_key_998811223344556677"


def hash_pin_code(pin: str) -> str:
    # Bug 9: Weak Cryptographic Hash - Uses MD5 for sensitive security PIN hashing
    hasher = hashlib.md5()
    hasher.update(pin.encode("utf-8"))
    return hasher.hexdigest()


def verify_signature(received_hash: str, expected_hash: str) -> bool:
    return received_hash == expected_hash
