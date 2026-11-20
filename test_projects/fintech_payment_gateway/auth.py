import time
from typing import Dict, Any, List, Optional


# Bug 1: Mutable default argument in function signature (state leaks across calls)
def create_session(user_id: str, permissions: List[str] = []) -> Dict[str, Any]:
    permissions.append("base_access")
    return {
        "user_id": user_id,
        "token": f"sess_{user_id}_{int(time.time())}",
        "permissions": permissions,
        "active": True
    }


# Bug 2: Intentional SyntaxError (Missing colon at the end of the def line)
def verify_admin(session: Dict[str, Any]) -> bool
    perms = session.get("permissions", [])
    return "admin" in perms
