"""Approval workflow state machine.

States and transitions follow the Irancell signoff chain (Line Manager /
Functional Manager / OA / HoD / CHRO / CEO-COO) generalized into review
stages. Minimum role names refer to app roles (employee<manager<hr<admin).
"""
from __future__ import annotations

STATES = [
    "Draft",
    "Under Review",
    "HR Review",
    "Business Review",
    "Organization Design Review",
    "Compensation Review",
    "Executive Approval",
    "Published",
    "Archived",
]

# action -> (allowed_from, to_state, minimum_role)
ACTIONS: dict[str, tuple[list[str], str, str]] = {
    "submit": (["Draft"], "Under Review", "employee"),
    "send_to_hr": (["Under Review"], "HR Review", "manager"),
    "send_to_business": (["HR Review"], "Business Review", "hr"),
    "send_to_od": (["Business Review"], "Organization Design Review", "manager"),
    "send_to_comp": (["Organization Design Review"], "Compensation Review", "hr"),
    "send_to_executive": (["Compensation Review"], "Executive Approval", "hr"),
    "approve": (
        ["Under Review", "HR Review", "Business Review", "Organization Design Review", "Compensation Review"],
        "",  # resolved dynamically: advance to next stage
        "manager",
    ),
    "publish": (["Executive Approval", "Compensation Review", "HR Review"], "Published", "hr"),
    "reject": (STATES[1:7], "Draft", "manager"),
    "request_change": (STATES[1:8], "Draft", "employee"),
    "archive": (["Published", "Draft"], "Archived", "hr"),
    "restore": (["Archived"], "Draft", "hr"),
}

REVIEW_CHAIN = STATES[1:8]  # Under Review ... Published


def next_state(action: str, current: str) -> str | None:
    """Resolve the target state for an action, or None if not allowed."""
    if action not in ACTIONS:
        return None
    allowed_from, target, _role = ACTIONS[action]
    if current not in allowed_from:
        return None
    if action == "approve":
        idx = REVIEW_CHAIN.index(current)
        return REVIEW_CHAIN[idx + 1] if idx + 1 < len(REVIEW_CHAIN) else "Published"
    return target


def minimum_role(action: str) -> str:
    return ACTIONS[action][2] if action in ACTIONS else "admin"
