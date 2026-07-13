"""Demo authentication with role-based access control.

Tokens are HMAC-signed "username:role" pairs — good enough for a demo and
trivially replaceable by SSO / Microsoft Entra ID (OIDC) in production; the
rest of the app only depends on `CurrentUser`.
"""
import hashlib
import hmac

from fastapi import Depends, Header, HTTPException

from .config import settings

ROLE_RANK = {"employee": 0, "manager": 1, "hr": 2, "admin": 3}

DEMO_USERS = {
    "admin": {"full_name": "System Administrator", "role": "admin"},
    "hr": {"full_name": "HR / Organization Architecture", "role": "hr"},
    "manager": {"full_name": "Line Manager", "role": "manager"},
    "employee": {"full_name": "Employee", "role": "employee"},
}
DEMO_PASSWORD = "demo"


class CurrentUser:
    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role


def _sign(payload: str) -> str:
    return hmac.new(settings.auth_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]


def make_token(username: str, role: str) -> str:
    payload = f"{username}:{role}"
    return f"{payload}:{_sign(payload)}"


def parse_token(token: str) -> CurrentUser | None:
    parts = token.split(":")
    if len(parts) != 3:
        return None
    payload = f"{parts[0]}:{parts[1]}"
    if hmac.compare_digest(_sign(payload), parts[2]):
        return CurrentUser(parts[0], parts[1])
    return None


def get_current_user(authorization: str = Header(default="")) -> CurrentUser:
    if authorization.startswith("Bearer "):
        user = parse_token(authorization[7:])
        if user:
            return user
    # Anonymous read access maps to the employee role.
    return CurrentUser("anonymous", "employee")


def require_role(minimum: str):
    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if ROLE_RANK.get(user.role, -1) < ROLE_RANK[minimum]:
            raise HTTPException(status_code=403, detail=f"Requires role '{minimum}' or higher")
        return user

    return checker
