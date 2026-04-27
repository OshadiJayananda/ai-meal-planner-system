"""Session service facade used by the desktop app."""

from typing import Any

from db_service import get_session_detail, list_sessions


def list_recent_sessions(limit: int = 8) -> list[dict[str, Any]]:
    return list_sessions(limit=limit)


def load_session_detail(session_id: int) -> dict[str, Any] | None:
    return get_session_detail(session_id)
