"""
Safety Guard Module for S.H.I.V.A.
Enforces strict 2-step confirmation for any deletion or destructive action.
"""

from typing import Dict, Optional, Tuple

# In-memory deletion pending states:
# { "path": str, "stage": int (1 or 2), "timestamp": float }
_pending_deletions: Dict[str, int] = {}


def request_deletion(target_path: str) -> str:
    """
    Registers a deletion request and enforces 2-step confirmation.
    Returns status message instructing user on confirmation step.
    """
    current_stage = _pending_deletions.get(target_path, 0)

    if current_stage == 0:
        _pending_deletions[target_path] = 1
        return (
            f"⚠️ [SAFETY ALERT - CONFIRMATION 1/2]:\n"
            f"Boss, you requested to delete: '{target_path}'.\n"
            f"Are you sure? To proceed, please reply: 'confirm delete {target_path}'"
        )
    elif current_stage == 1:
        _pending_deletions[target_path] = 2
        return (
            f"⚠️ [FINAL WARNING - CONFIRMATION 2/2]:\n"
            f"Boss, this will permanently remove: '{target_path}'. This action CANNOT be undone!\n"
            f"To permanently execute deletion, reply: 'final confirm delete {target_path}'"
        )
    else:
        return f"Boss, confirmation 2/2 is already pending for '{target_path}'. Reply 'final confirm delete {target_path}' to execute."


def verify_and_clear_deletion(target_path: str, confirmation_type: str) -> Tuple[bool, str]:
    """
    Verifies if the confirmation matches the required stage.
    """
    stage = _pending_deletions.get(target_path, 0)

    if confirmation_type == "stage1":
        if stage == 1:
            _pending_deletions[target_path] = 2
            return (
                False,
                f"⚠️ [CONFIRMATION 1/2 ACCEPTED].\nFinal security gate: Reply 'final confirm delete {target_path}' to execute permanent deletion."
            )
        return (False, f"Boss, no stage 1 deletion pending for '{target_path}'.")

    elif confirmation_type == "stage2":
        if stage == 2:
            del _pending_deletions[target_path]
            return (True, "CONFIRMED")
        return (False, f"Boss, 2nd confirmation rejected. You must pass confirmation 1 first.")

    return (False, "Invalid confirmation request.")


def cancel_deletion(target_path: Optional[str] = None) -> str:
    """Cancels any pending deletion."""
    global _pending_deletions
    if target_path and target_path in _pending_deletions:
        del _pending_deletions[target_path]
        return f"Deletion request for '{target_path}' has been cancelled, Boss."
    _pending_deletions.clear()
    return "All pending deletion requests have been safely cancelled, Boss."

